"""
game_controller.py — Multi-Mode Hardware Input Automation Engine
═════════════════════════════════════════════════════════════════════════════
Translates classified gesture decisions into OS keyboard, mouse,
and game input events via Windows SendInput API + PyAutoGUI with state-latching,
dedicated audio queue worker, and fast Win32 window focus.
"""

import sys
import ctypes
from ctypes import wintypes
import pyautogui
import threading
import queue
import time
from typing import Dict, Set, Optional, List, Tuple

# Zero delay — timing is strictly managed by our vision loop
pyautogui.PAUSE = 0
pyautogui.FAILSAFE = False

# Try importing winsound for subtle audio feedback on Windows
try:
    import winsound
    HAS_SOUND = True
except ImportError:
    HAS_SOUND = False

# Windows SendInput Structures
INPUT_KEYBOARD = 1
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_ulonglong if ctypes.sizeof(ctypes.c_void_p) == 8 else wintypes.DWORD),
    ]

class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD)
    ]

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_ulonglong if ctypes.sizeof(ctypes.c_void_p) == 8 else wintypes.DWORD)
    ]

class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = [
            ("ki", KEYBDINPUT),
            ("mi", MOUSEINPUT),
            ("hi", HARDWAREINPUT)
        ]
    _anonymous_ = ("_input",)
    _fields_ = [("type", wintypes.DWORD), ("_input", _INPUT)]


# Win32 Virtual Key codes for low-level DirectInput/browser canvas injection
WIN32_VK = {
    "left": 0x25,
    "up": 0x26,
    "right": 0x27,
    "down": 0x28,
    "space": 0x20,
    "shift": 0x10,
    "ctrl": 0x11,
    "alt": 0x12,
    "enter": 0x0D,
    "esc": 0x1B,
    "a": 0x41,
    "d": 0x44,
    "w": 0x57,
    "s": 0x53,
    "e": 0x45,
    "r": 0x52,
    "z": 0x5A,
    "x": 0x58,
    "c": 0x43,
}

# Standardized logical key pairs (Fixed: Gas does NOT trigger Right Arrow!)
DEFAULT_KEY_PAIRS = {
    "left": ["left", "a"],
    "right": ["right", "d"],
    "up": ["up", "w"],
    "down": ["down", "s"],
    "space": ["space"],
    "shift": ["shift"],
    "e": ["e"],
    "r": ["r"],
    "gas": ["up", "w"],            # Throttle only (no directional tilt conflicts)
    "brake": ["down", "s"],        # Brake / Reverse
}


class AudioWorker:
    """Dedicated background audio queue thread to eliminate thread creation overhead."""
    def __init__(self, enabled: bool = True):
        self.enabled = enabled and HAS_SOUND
        self._queue = queue.Queue(maxsize=10)
        self._running = True
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def play(self, freq: int, dur_ms: int):
        if not self.enabled:
            return
        try:
            # Non-blocking enqueue, discard if queue is backed up
            self._queue.put_nowait((freq, dur_ms))
        except queue.Full:
            pass

    def _worker(self):
        while self._running:
            try:
                freq, dur_ms = self._queue.get(timeout=0.2)
                if HAS_SOUND and self.enabled:
                    winsound.Beep(freq, dur_ms)
                self._queue.task_done()
            except queue.Empty:
                continue
            except Exception:
                pass


class GameController:
    """Multi-profile state-managed virtual keyboard and mouse controller."""

    ALL_MANAGED_KEYS = {
        "left", "right", "up", "down",
        "space", "shift", "e", "w", "a", "s", "d", "r", "z", "x", "c"
    }

    def __init__(self, audio_feedback: bool = True) -> None:
        self.audio_worker = AudioWorker(enabled=audio_feedback)
        self.mode: str = "racing"  # "racing" | "two_hand" | "runner" | "arcade" | "air_mouse"
        self.key_mappings: Dict[str, List[str]] = DEFAULT_KEY_PAIRS.copy()

        # State tracking flags
        self.current_steering: str = "straight"   # 'left' | 'right' | 'straight'
        self.accelerating: bool = False
        self.braking: bool = False
        self.nitro: bool = False
        self.action_active: bool = False
        self.mouse_clicked: bool = False

        # Set of currently held virtual keys
        self._held_keys: Set[str] = set()

        # PWM / Tap-Steering simulation thread
        self.pwm_enabled: bool = True
        self._pwm_duty: float = 1.0  # 0.0 to 1.0
        self._pwm_direction: Optional[str] = None
        self._pwm_stop_event = threading.Event()
        self._pwm_thread: Optional[threading.Thread] = None

    def set_audio_feedback(self, enabled: bool) -> None:
        self.audio_worker.enabled = enabled and HAS_SOUND

    # ── Win32 Window Focus Optimization ───────────────────────────────────────

    @staticmethod
    def focus_window_win32(title_keywords: List[str]) -> bool:
        """Brings the target browser or game window to the front with the Win32 API."""
        if sys.platform != "win32":
            return False
        try:
            user32 = ctypes.windll.user32
            found_hwnd = None

            def enum_proc(hwnd, extra):
                nonlocal found_hwnd
                if user32.IsWindowVisible(hwnd):
                    length = user32.GetWindowTextLengthW(hwnd)
                    if length > 0:
                        buff = ctypes.create_unicode_buffer(length + 1)
                        user32.GetWindowTextW(hwnd, buff, length + 1)
                        title = buff.value.lower()
                        for kw in title_keywords:
                            if kw.lower() in title:
                                found_hwnd = hwnd
                                return False
                return True

            WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
            user32.EnumWindows(WNDENUMPROC(enum_proc), 0)

            if found_hwnd:
                user32.ShowWindow(found_hwnd, 9)  # SW_RESTORE
                user32.SetForegroundWindow(found_hwnd)
                return True
        except Exception:
            pass
        return False

    # ── Key Dispatch Helpers ──────────────────────────────────────────────────

    def _send_hardware_input(self, vk: int, is_down: bool) -> None:
        """Dispatches hardware-level Win32 keyboard event via SendInput."""
        if sys.platform != "win32":
            return
        try:
            user32 = ctypes.windll.user32
            scan = user32.MapVirtualKeyW(vk, 0)
            flags = KEYEVENTF_SCANCODE
            if not is_down:
                flags |= KEYEVENTF_KEYUP
            if vk in [0x25, 0x26, 0x27, 0x28]:  # Left, Up, Right, Down Arrows
                flags |= KEYEVENTF_EXTENDEDKEY
            # When KEYEVENTF_SCANCODE is set, wVk is ignored, but it's safe to pass 0
            inp = INPUT(type=INPUT_KEYBOARD, ki=KEYBDINPUT(wVk=0, wScan=scan, dwFlags=flags, time=0, dwExtraInfo=0))
            user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
        except Exception:
            pass

    def _press_key(self, logical_key: str) -> None:
        subkeys = self.key_mappings.get(logical_key, [logical_key])
        for k in subkeys:
            if k not in self._held_keys:
                self._held_keys.add(k)
                try:
                    pyautogui.keyDown(k)
                except Exception:
                    pass
                vk = WIN32_VK.get(k)
                if vk is not None:
                    self._send_hardware_input(vk, True)

    def _release_key(self, logical_key: str) -> None:
        subkeys = self.key_mappings.get(logical_key, [logical_key])
        for k in subkeys:
            if k in self._held_keys:
                self._held_keys.discard(k)
                try:
                    pyautogui.keyUp(k)
                except Exception:
                    pass
                vk = WIN32_VK.get(k)
                if vk is not None:
                    self._send_hardware_input(vk, False)

    # ── Steering Controls ─────────────────────────────────────────────────────

    def steer_left(self, intensity: float = 1.0) -> None:
        if self.current_steering != "left":
            self._press_key("left")
            self._release_key("right")
            self.current_steering = "left"
            self.audio_worker.play(800, 25)

    def steer_right(self, intensity: float = 1.0) -> None:
        if self.current_steering != "right":
            self._press_key("right")
            self._release_key("left")
            self.current_steering = "right"
            self.audio_worker.play(1400, 25)

    def steer_straight(self) -> None:
        if self.current_steering != "straight":
            self._release_key("left")
            self._release_key("right")
            self.current_steering = "straight"

    # ── Throttle & Brake Controls ─────────────────────────────────────────────

    def accelerate(self) -> None:
        """Full throttle acceleration (Up Arrow + W)."""
        if self.braking:
            self._release_key("brake")
            self.braking = False
        if not self.accelerating:
            self._press_key("gas")
            self.accelerating = True
            self.audio_worker.play(1600, 30)

    def brake(self) -> None:
        """Full braking / reverse (Down Arrow + S)."""
        if self.accelerating:
            self._release_key("gas")
            self.accelerating = False
        if not self.braking:
            self._press_key("brake")
            self.braking = True
            self.audio_worker.play(600, 40)

    def release_throttle(self) -> None:
        if self.accelerating:
            self._release_key("gas")
            self.accelerating = False
        if self.braking:
            self._release_key("brake")
            self.braking = False

    # ── Actions, Nitro & Runner Jumps ─────────────────────────────────────────

    def trigger_jump(self) -> None:
        """Trigger instant single jump impulse for runner games."""
        self._press_key("up")
        self._press_key("space")
        self.audio_worker.play(1800, 40)
        def _release():
            time.sleep(0.08)
            self._release_key("space")
            if self.mode == "runner":
                self._release_key("up")
        threading.Thread(target=_release, daemon=True).start()

    def trigger_slide(self) -> None:
        """Trigger slide impulse for runner games."""
        self._press_key("down")
        self.audio_worker.play(500, 50)
        def _release():
            time.sleep(0.12)
            self._release_key("down")
        threading.Thread(target=_release, daemon=True).start()

    def trigger_nitro(self, activate: bool = True) -> None:
        """Hold or release nitro boost."""
        if activate:
            if not self.nitro:
                self._press_key("space")
                self.nitro = True
                self.audio_worker.play(2200, 50)
        else:
            if self.nitro:
                self._release_key("space")
                self.nitro = False

    def trigger_action(self, activate: bool = True) -> None:
        """Hold or release primary action / fire."""
        if activate:
            if not self.action_active:
                self._press_key("shift")
                self._press_key("e")
                self.action_active = True
                self.audio_worker.play(2000, 30)
        else:
            if self.action_active:
                self._release_key("shift")
                self._release_key("e")
                self.action_active = False

    # ── Air-Mouse Cursor Emulation ────────────────────────────────────────────

    def move_mouse_rel(self, dx: int, dy: int) -> None:
        """Smooth relative mouse displacement."""
        if dx != 0 or dy != 0:
            try:
                pyautogui.moveRel(dx, dy, _pause=False)
            except Exception:
                pass

    def mouse_click(self) -> None:
        """Single mouse click on pinch gesture."""
        try:
            pyautogui.click()
            self.audio_worker.play(1900, 20)
        except Exception:
            pass

    def mouse_set_down(self, is_down: bool) -> None:
        """Hold or release left mouse button for drag/steering."""
        if is_down and not self.mouse_clicked:
            pyautogui.mouseDown()
            self.mouse_clicked = True
            self.audio_worker.play(1900, 20)
        elif not is_down and self.mouse_clicked:
            pyautogui.mouseUp()
            self.mouse_clicked = False

    # ── Emergency Stop & Fail-Safe ────────────────────────────────────

    def stop(self) -> None:
        """Instantly releases all active virtual keys and mouse buttons."""
        for key in list(self._held_keys):
            try:
                pyautogui.keyUp(key)
            except Exception:
                pass
            vk = WIN32_VK.get(key)
            if vk is not None:
                self._send_hardware_input(vk, False)
        self._held_keys.clear()

        if self.mouse_clicked:
            try:
                pyautogui.mouseUp()
            except Exception:
                pass
            self.mouse_clicked = False

        # Reset states
        self.current_steering = "straight"
        self.accelerating     = False
        self.braking          = False
        self.nitro            = False
        self.action_active    = False

    # ── State Snapshot for UI Telemetry ───────────────────────────────────────

    @property
    def state(self) -> dict:
        return {
            "steering":     self.current_steering,
            "accelerating": self.accelerating,
            "braking":      self.braking,
            "nitro":        self.nitro,
            "action":       self.action_active,
            "held_count":   len(self._held_keys),
        }
