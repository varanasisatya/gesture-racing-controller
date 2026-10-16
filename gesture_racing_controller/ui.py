"""
ui.py — Cinematic Cyberpunk Dashboard, Offline 2D Track & Telemetry Hub (v3.0 Ultra)
══════════════════════════════════════════════════════════════════════════════════
Features:
  • Real-time OpenCV video stream with glowing neural landmark HUD & dual-hand tracking
  • Animated Sci-Fi Digital Steering Wheel & Orientation Radar (60 FPS Sub-pixel)
  • Interactive Game Hub with dynamic profiles & visual hand blueprints
  • Built-in Offline 2D Canvas Racetrack with physics for instant testing
  • Compact Floating Picture-in-Picture (PiP) Mini-HUD Mode
  • Live Camera Device Selector & Instant Audio Mute Toggle
  • 1-Click 3-Second Dynamic Calibration Wizard with Holographic Reticle
  • In-App Custom Game Creator & Key Remapping
  • Batched single-event UI dispatch loop for zero lag & maximum smoothness
  • Fast Win32 Direct Window Activation & Spacebar Master Shortcut
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import math
import time
import webbrowser
import cv2
import numpy as np
from PIL import Image, ImageTk
from typing import Optional, Dict, Tuple, List, Any

from config import (
    APP_NAME, APP_VERSION, APP_SUBTITLE,
    BG_DEEP, BG_PANEL, BG_CARD, BG_CARD_HOVER, BORDER_GLOW,
    NEON_CYAN, NEON_PURPLE, NEON_PINK, NEON_BLUE, NEON_GREEN, NEON_GOLD, NEON_RED,
    TEXT_TITLE, TEXT_BODY, TEXT_MUTED, TEXT_DIM,
    STEER_DEADZONE_DEG, UI_REFRESH_MS, ENABLE_AUDIO_FEEDBACK,
    get_setting, set_setting, save_settings, RUNTIME_SETTINGS
)
from games import get_all_games, add_custom_game, BROWSER_TITLES
from game_controller import GameController, DEFAULT_KEY_PAIRS

WHEEL_SIZE = 140
VIDEO_W = 460
VIDEO_H = 330


class OfflineRaceTrack:
    """Embedded interactive 2D physics racetrack for instant offline gesture testing."""
    def __init__(self, canvas: tk.Canvas, width: int = 540, height: int = 210):
        self.canvas = canvas
        self.w = width
        self.h = height

        # Vehicle physics state
        self.car_x: float = 120.0
        self.car_y: float = 175.0
        self.car_angle: float = 0.0  # degrees
        self.speed: float = 0.0
        self.max_speed: float = 7.5
        self.accel: float = 0.32
        self.friction: float = 0.94
        self.steer_speed: float = 4.2

        # Lap metrics
        self.lap_count: int = 0
        self.lap_start_time: float = time.time()
        self.best_lap: Optional[float] = None
        self.checkpoint_passed: bool = False

        # Track definition (Outer and Inner track loops scaled to canvas)
        self.outer_poly = [
            (30, 30), (510, 30), (525, 60), (525, 160), (500, 195),
            (280, 195), (240, 150), (180, 150), (140, 195), (40, 195), (15, 160), (15, 60)
        ]
        self.inner_poly = [
            (80, 75), (460, 75), (475, 95), (475, 130), (450, 155),
            (310, 155), (270, 110), (150, 110), (120, 155), (80, 155), (65, 130), (65, 95)
        ]

    def update_physics(self, steering: str, accelerating: bool, braking: bool, raw_steer_angle: Optional[float] = None) -> None:
        if accelerating:
            self.speed = min(self.speed + self.accel, self.max_speed)
        elif braking:
            self.speed = max(self.speed - self.accel * 1.5, -self.max_speed * 0.4)
        else:
            self.speed *= self.friction

        if abs(self.speed) < 0.05:
            self.speed = 0.0

        if self.speed != 0:
            direction_factor = 1 if self.speed > 0 else -1
            if raw_steer_angle is not None and abs(raw_steer_angle - 90.0) > 15.0:
                turn_rate = ((raw_steer_angle - 90.0) / 45.0) * self.steer_speed
                self.car_angle += turn_rate * direction_factor
            elif steering == "left":
                self.car_angle -= self.steer_speed * direction_factor
            elif steering == "right":
                self.car_angle += self.steer_speed * direction_factor

        rad = math.radians(self.car_angle)
        self.car_x += self.speed * math.cos(rad)
        self.car_y += self.speed * math.sin(rad)

        self.car_x = max(20, min(self.w - 20, self.car_x))
        self.car_y = max(20, min(self.h - 20, self.car_y))

        if self.car_x > 380 and not self.checkpoint_passed:
            self.checkpoint_passed = True
        if self.car_x < 140 and 140 < self.car_y < 200 and self.checkpoint_passed:
            self.lap_count += 1
            lap_time = time.time() - self.lap_start_time
            if self.best_lap is None or lap_time < self.best_lap:
                self.best_lap = lap_time
            self.lap_start_time = time.time()
            self.checkpoint_passed = False

    def render(self) -> None:
        c = self.canvas
        c.delete("all")

        c.create_rectangle(0, 0, self.w, self.h, fill="#080D18", outline="")
        c.create_polygon(self.outer_poly, fill="#121B2F", outline=NEON_CYAN, width=2)
        c.create_polygon(self.inner_poly, fill="#080D18", outline=NEON_PURPLE, width=2)
        c.create_line(120, 150, 120, 195, fill=NEON_GOLD, width=3, dash=(4, 4))

        cx, cy = self.car_x, self.car_y
        rad = math.radians(self.car_angle)
        car_len = 18
        car_wid = 10

        dx_f = (car_len / 2) * math.cos(rad)
        dy_f = (car_len / 2) * math.sin(rad)
        dx_s = (car_wid / 2) * math.cos(rad + math.pi / 2)
        dy_s = (car_wid / 2) * math.sin(rad + math.pi / 2)

        p1 = (cx + dx_f + dx_s, cy + dy_f + dy_s)
        p2 = (cx + dx_f - dx_s, cy + dy_f - dy_s)
        p3 = (cx - dx_f - dx_s, cy - dy_f - dy_s)
        p4 = (cx - dx_f + dx_s, cy - dy_f + dy_s)

        c.create_polygon([p1, p2, p3, p4], fill=NEON_CYAN, outline="#FFFFFF", width=1)

        h_left = (p1[0] + 14 * math.cos(rad - 0.2), p1[1] + 14 * math.sin(rad - 0.2))
        h_right = (p2[0] + 14 * math.cos(rad + 0.2), p2[1] + 14 * math.sin(rad + 0.2))
        c.create_line(p1[0], p1[1], h_left[0], h_left[1], fill=NEON_GREEN, width=2)
        c.create_line(p2[0], p2[1], h_right[0], h_right[1], fill=NEON_GREEN, width=2)

        mph = int(abs(self.speed) * 14)
        c.create_text(40, 14, text=f"SPEED: {mph} MPH", fill=NEON_CYAN, font=("Consolas", 8, "bold"), anchor="w")
        c.create_text(200, 14, text=f"LAP: {self.lap_count}", fill=NEON_GOLD, font=("Consolas", 8, "bold"), anchor="w")
        best_str = f"{self.best_lap:.2f}s" if self.best_lap else "--"
        c.create_text(350, 14, text=f"BEST: {best_str}", fill=NEON_GREEN, font=("Consolas", 8, "bold"), anchor="w")


class AppUI:
    """Cyberpunk Neural HUD, Mini-HUD (PiP), and Game Hub Interface."""

    def __init__(self, root: tk.Tk, engine, controller: GameController) -> None:
        self.root = root
        self.engine = engine
        self.controller = controller

        self.running: bool = False
        self.is_pip_mode: bool = False
        self.show_offline_track: bool = bool(self.engine.simulation_mode)
        self._thread: Optional[threading.Thread] = None
        self._latest_ui: Optional[Tuple[np.ndarray, Any, str]] = None
        self._ui_poll_id: Optional[str] = None
        self._launch_briefing_open: bool = False
        self._last_camera_preview: Optional[np.ndarray] = None
        self._last_camera_result: Optional[Any] = None

        self._all_games = get_all_games()
        last_game_name = get_setting("last_selected_game", self._all_games[0]["name"])
        self._active_game: dict = next((g for g in self._all_games if g["name"] == last_game_name), self._all_games[0])
        self._game_var = tk.StringVar(value=self._active_game["name"])
        self._mode_var = tk.StringVar(value=get_setting("control_mode", "racing"))

        self.audio_enabled: bool = get_setting("enable_audio_feedback", True)
        self.controller.set_audio_feedback(self.audio_enabled)

        self._sensitivity = tk.IntVar(value=int(get_setting("steer_deadzone_deg", 25.0)))

        self._session_start: Optional[float] = None
        self._counts: Dict[str, int] = {
            "left": 0, "right": 0, "gas": 0, "brake": 0, "jump": 0, "action": 0
        }
        self._last_gesture: str = "none"

        self._wheel_angle: float = 0.0
        self._wheel_target: float = 0.0
        self._wheel_anim_id: Optional[str] = None

        self._build_window()
        self._build_layout()
        self._animate_wheel()
        self._ui_poll_id = self.root.after(UI_REFRESH_MS, self._poll_latest_ui)

        self.root.bind("<space>", lambda e: self._toggle())
        self.root.bind("<Escape>", lambda e: self.stop())
        self.root.bind("<KeyPress>", self._on_sim_key_press)
        self.root.bind("<KeyRelease>", self._on_sim_key_release)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self.root.after(120, self.start)

    def _build_window(self) -> None:
        self.root.title(f"⚡ {APP_NAME} — v{APP_VERSION}")
        self.root.configure(bg=BG_DEEP)
        self.root.resizable(False, False)
        w, h = 1140, 850
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.root.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after(1000, lambda: self.root.attributes('-topmost', False))
        self.root.focus_force()

    def _build_layout(self) -> None:
        for widget in self.root.winfo_children():
            widget.destroy()

        top = tk.Frame(self.root, bg=BG_PANEL, height=58, highlightbackground=BORDER_GLOW, highlightthickness=1)
        top.pack(fill="x")
        top.pack_propagate(False)

        title_frame = tk.Frame(top, bg=BG_PANEL)
        title_frame.pack(side="left", padx=16, pady=6)

        tk.Label(title_frame, text=f"⚡ {APP_NAME}", bg=BG_PANEL, fg=NEON_CYAN,
                 font=("Consolas", 14, "bold")).pack(anchor="w")
        tk.Label(title_frame, text=f"{APP_SUBTITLE}  •  v{APP_VERSION}", bg=BG_PANEL, fg=TEXT_MUTED,
                 font=("Consolas", 8)).pack(anchor="w")

        self._lat_badge = tk.Label(top, text="LATENCY: -- ms", bg=BG_CARD, fg=NEON_CYAN,
                                   font=("Consolas", 8, "bold"), padx=8, pady=4)
        self._lat_badge.pack(side="right", padx=(4, 16), pady=12)

        self._fps_badge = tk.Label(top, text="FPS: --", bg=BG_CARD, fg=NEON_GREEN,
                                   font=("Consolas", 8, "bold"), padx=8, pady=4)
        self._fps_badge.pack(side="right", padx=4, pady=12)

        self._pip_btn = tk.Button(
            top, text="🗖 PiP HUD", bg=BG_CARD, fg=NEON_GOLD, activebackground=BG_CARD_HOVER,
            font=("Consolas", 8, "bold"), relief="flat", padx=8, pady=3, cursor="hand2",
            command=self._toggle_pip_mode
        )
        self._pip_btn.pack(side="right", padx=4, pady=12)

        self._audio_btn = tk.Button(
            top, text="🔊 AUDIO ON" if self.audio_enabled else "🔇 MUTED",
            bg=BG_CARD, fg=NEON_CYAN if self.audio_enabled else TEXT_DIM,
            activebackground=BG_CARD_HOVER, font=("Consolas", 8, "bold"),
            relief="flat", padx=8, pady=3, cursor="hand2", command=self._toggle_audio
        )
        self._audio_btn.pack(side="right", padx=4, pady=12)

        cam_frame = tk.Frame(top, bg=BG_PANEL)
        cam_frame.pack(side="right", padx=8, pady=12)

        tk.Label(cam_frame, text="CAM:", bg=BG_PANEL, fg=TEXT_MUTED, font=("Consolas", 8, "bold")).pack(side="left", padx=(0, 4))
        cams = self.engine.get_available_cameras()
        self._cam_var = tk.StringVar(value="Simulation" if self.engine.simulation_mode else f"Camera {self.engine.camera_index}")
        cam_names = [f"Camera {i}" for i in cams] + ["Simulation"]
        self._cam_dd = ttk.Combobox(cam_frame, textvariable=self._cam_var, values=cam_names,
                                    state="readonly", width=9, font=("Consolas", 8))
        self._cam_dd.pack(side="left")
        self._cam_dd.bind("<<ComboboxSelected>>", self._on_camera_selected)

        self._body = tk.Frame(self.root, bg=BG_DEEP)
        self._body.pack(fill="both", expand=True, padx=12, pady=8)

        left = tk.Frame(self._body, bg=BG_DEEP, width=VIDEO_W + 10)
        left.pack(side="left", fill="y", padx=(0, 10))

        cam_card = tk.Frame(left, bg=BG_CARD, highlightbackground=NEON_CYAN, highlightthickness=1)
        cam_card.pack(fill="x")

        self._video_label = tk.Label(cam_card, bg="#000000", width=VIDEO_W, height=VIDEO_H)
        self._video_label.pack()
        self._cam_placeholder()

        self._build_game_hub(left)

        self._right = tk.Frame(self._body, bg=BG_DEEP)
        self._right.pack(side="right", fill="both", expand=True)

        self._build_status_panel(self._right)
        self._build_radar_panel(self._right)
        self._build_controls_panel(self._right)
        self._build_stats_or_track_panel(self._right)

    def _build_game_hub(self, parent: tk.Frame) -> None:
        card = self._card(parent, "🎮  NEURAL GAME LAUNCHER & PROFILES")

        sel_row = tk.Frame(card, bg=BG_CARD)
        sel_row.pack(fill="x", pady=(2, 4))

        game_names = [g["name"] for g in self._all_games]
        self._game_dd = ttk.Combobox(
            sel_row, textvariable=self._game_var, values=game_names,
            state="readonly", font=("Consolas", 9), width=27
        )
        self._game_dd.pack(side="left", padx=(0, 6))
        self._game_dd.bind("<<ComboboxSelected>>", self._on_game_selected)

        self._genre_badge = tk.Label(sel_row, text=self._active_game.get("genre", "RACING"),
                                     bg=NEON_PURPLE, fg=TEXT_TITLE, font=("Consolas", 8, "bold"), padx=6, pady=2)
        self._genre_badge.pack(side="left")

        btn_row = tk.Frame(card, bg=BG_CARD)
        btn_row.pack(fill="x", pady=(2, 4))

        self._launch_btn = tk.Button(
            btn_row, text="🚀 Launch Game", bg=NEON_PURPLE, fg=TEXT_TITLE,
            activebackground="#5E17EB", font=("Consolas", 8, "bold"),
            relief="flat", padx=8, pady=4, cursor="hand2", command=self._launch_game
        )
        self._launch_btn.pack(side="left", padx=(0, 4))

        self._focus_btn = tk.Button(
            btn_row, text="🎯 Focus", bg=BG_DEEP, fg=NEON_CYAN,
            activebackground=BG_PANEL, font=("Consolas", 8, "bold"),
            relief="flat", padx=8, pady=4, cursor="hand2", command=self._focus_game_window
        )
        self._focus_btn.pack(side="left", padx=(0, 4))

        self._add_game_btn = tk.Button(
            btn_row, text="➕ Add Game", bg=BG_DEEP, fg=NEON_GOLD,
            activebackground=BG_PANEL, font=("Consolas", 8, "bold"),
            relief="flat", padx=8, pady=4, cursor="hand2", command=self._open_add_game_modal
        )
        self._add_game_btn.pack(side="left")

        self._blueprint_frame = tk.Frame(card, bg=BG_DEEP, highlightbackground=BORDER_GLOW, highlightthickness=1, padx=6, pady=4)
        self._blueprint_frame.pack(fill="x", pady=(3, 0))
        self._render_blueprint_tiles()

    def _render_blueprint_tiles(self) -> None:
        for widget in self._blueprint_frame.winfo_children():
            widget.destroy()

        game = self._active_game
        gestures = game.get("gestures", [])

        tk.Label(self._blueprint_frame, text=f"CONTROL PROFILE — {game['name']}",
                 bg=BG_DEEP, fg=NEON_CYAN, font=("Consolas", 8, "bold")).pack(anchor="w", pady=(0, 2))

        grid = tk.Frame(self._blueprint_frame, bg=BG_DEEP)
        grid.pack(fill="x")

        for idx, (gesture_name, action_name, key_name) in enumerate(gestures[:4]):
            tile = tk.Frame(grid, bg=BG_CARD, highlightbackground=BORDER_GLOW, highlightthickness=1, padx=5, pady=3)
            tile.grid(row=idx // 2, column=idx % 2, padx=2, pady=2, sticky="ew")
            grid.columnconfigure(idx % 2, weight=1)

            tk.Label(tile, text=gesture_name, bg=BG_CARD, fg=NEON_GOLD, font=("Consolas", 8, "bold")).pack(anchor="w")
            tk.Label(tile, text=f"➔ {action_name}", bg=BG_CARD, fg=TEXT_TITLE, font=("Consolas", 7)).pack(anchor="w")
            tk.Label(tile, text=key_name, bg=BG_CARD, fg=TEXT_MUTED, font=("Consolas", 7, "italic")).pack(anchor="w")

    def _on_game_selected(self, _event=None) -> None:
        name = self._game_var.get()
        for g in self._all_games:
            if g["name"] == name:
                self._active_game = g
                self._genre_badge.config(text=g.get("genre", "RACING"))
                self.controller.mode = g.get("mode", "racing")
                set_setting("last_selected_game", name)
                self._render_blueprint_tiles()
                break

    def _build_status_panel(self, parent: tk.Frame) -> None:
        card = self._card(parent, "⚡ NEURAL GESTURE TELEMETRY")

        self._gesture_label = tk.Label(
            card, text="⬛  IDLE / READY", bg=BG_CARD, fg=TEXT_MUTED,
            font=("Consolas", 16, "bold"), pady=2
        )
        self._gesture_label.pack(fill="x")

        row = tk.Frame(card, bg=BG_CARD)
        row.pack(fill="x", pady=(3, 2))

        self._steer_badge    = self._badge(row, "STRAIGHT", NEON_CYAN)
        self._throttle_badge = self._badge(row, "IDLE",     TEXT_DIM)
        self._nitro_badge    = self._badge(row, "ACTION",   TEXT_DIM)
        self._hand_badge     = self._badge(row, "NO HAND",  NEON_RED)

        for b in (self._steer_badge, self._throttle_badge, self._nitro_badge, self._hand_badge):
            b.pack(side="left", padx=(0, 4))

        meta_row = tk.Frame(card, bg=BG_CARD)
        meta_row.pack(fill="x", pady=(3, 0))

        self._angle_label = tk.Label(meta_row, text="ANGLE: --° (Neutral: 90°)", bg=BG_CARD, fg=TEXT_MUTED, font=("Consolas", 8))
        self._angle_label.pack(side="left")

        self._finger_bits = tk.Label(meta_row, text="FINGERS: [ - - - - - ]", bg=BG_CARD, fg=NEON_CYAN, font=("Consolas", 8, "bold"))
        self._finger_bits.pack(side="right")

    def _build_radar_panel(self, parent: tk.Frame) -> None:
        card = self._card(parent, "🧭 ORIENTATION RADAR & STEERING TELEMETRY")

        hud_row = tk.Frame(card, bg=BG_CARD)
        hud_row.pack(fill="x")

        self._wheel_canvas = tk.Canvas(
            hud_row, width=WHEEL_SIZE, height=WHEEL_SIZE, bg=BG_CARD, highlightthickness=0
        )
        self._wheel_canvas.pack(side="left", padx=8)
        self._draw_wheel(0.0)

        info_col = tk.Frame(hud_row, bg=BG_CARD)
        info_col.pack(side="left", fill="both", expand=True, padx=6)

        tk.Label(info_col, text="CYBER STEERING ANGLE", bg=BG_CARD, fg=TEXT_MUTED, font=("Consolas", 8, "bold")).pack(anchor="w")
        self._steer_angle_val = tk.Label(info_col, text="0.0°", bg=BG_CARD, fg=NEON_CYAN, font=("Consolas", 18, "bold"))
        self._steer_angle_val.pack(anchor="w")

        btn_bar = tk.Frame(info_col, bg=BG_CARD)
        btn_bar.pack(anchor="w", pady=(3, 0))

        self._calib_btn = tk.Button(
            btn_bar, text="⚡ 1-Click Calibrate (3s)", bg=BG_DEEP, fg=NEON_GOLD,
            activebackground=BG_PANEL, font=("Consolas", 8, "bold"),
            relief="flat", padx=6, pady=3, cursor="hand2", command=self._start_calibration
        )
        self._calib_btn.pack(side="left", padx=(0, 4))

        self._track_toggle_btn = tk.Button(
            btn_bar, text="🏎️ Offline Track", bg=BG_DEEP, fg=NEON_GREEN,
            activebackground=BG_PANEL, font=("Consolas", 8, "bold"),
            relief="flat", padx=6, pady=3, cursor="hand2", command=self._toggle_offline_track
        )
        self._track_toggle_btn.pack(side="left")

        self._calib_status = tk.Label(info_col, text=f"Neutral calibrated: {self.engine.neutral_angle:.1f}°",
                                      bg=BG_CARD, fg=TEXT_DIM, font=("Consolas", 8))
        self._calib_status.pack(anchor="w", pady=(2, 0))

    def _build_controls_panel(self, parent: tk.Frame) -> None:
        card = self._card(parent, "🕹️ MASTER CONTROLLER  [SPACEBAR = Start/Stop]")

        btn_row = tk.Frame(card, bg=BG_CARD)
        btn_row.pack(fill="x", pady=(0, 4))

        self._start_btn = tk.Button(
            btn_row, text="▶  START CONTROLLER", bg=NEON_GREEN, fg=BG_DEEP,
            activebackground="#00B85C", font=("Consolas", 10, "bold"),
            relief="flat", padx=14, pady=6, cursor="hand2", command=self.start
        )
        self._start_btn.pack(side="left", padx=(0, 6))

        self._stop_btn = tk.Button(
            btn_row, text="■  STOP", bg=NEON_RED, fg=TEXT_TITLE,
            activebackground="#CC0033", font=("Consolas", 10, "bold"),
            relief="flat", padx=14, pady=6, cursor="hand2", state="disabled", command=self.stop
        )
        self._stop_btn.pack(side="left")

        sens_row = tk.Frame(card, bg=BG_CARD)
        sens_row.pack(fill="x", pady=(3, 0))

        tk.Label(sens_row, text="Steering Deadzone (± deg):", bg=BG_CARD, fg=TEXT_MUTED, font=("Consolas", 8)).pack(side="left")
        self._sens_val_lbl = tk.Label(sens_row, text=f"{self._sensitivity.get()}°", bg=BG_CARD, fg=NEON_CYAN, font=("Consolas", 8, "bold"))
        self._sens_val_lbl.pack(side="right")

        ttk.Scale(card, from_=10, to=50, orient="horizontal", variable=self._sensitivity,
                  command=self._on_sensitivity_change).pack(fill="x", pady=(2, 0))

    def _build_stats_or_track_panel(self, parent: tk.Frame) -> None:
        self._stats_container = tk.Frame(parent, bg=BG_DEEP)
        self._stats_container.pack(fill="both", expand=True)

        if self.show_offline_track:
            self._render_track_view()
        else:
            self._render_stats_view()

    def _render_stats_view(self) -> None:
        for w in self._stats_container.winfo_children():
            w.destroy()

        card = self._card(self._stats_container, "📊 SESSION TELEMETRY & ACTIONS")
        grid = tk.Frame(card, bg=BG_CARD)
        grid.pack(fill="x")

        self._stat_labels = {}
        items = [
            ("LEFT", NEON_BLUE, "left"),
            ("RIGHT", NEON_PINK, "right"),
            ("GAS", NEON_GREEN, "gas"),
            ("BRAKE", NEON_RED, "brake"),
            ("ACTION", NEON_PURPLE, "action"),
        ]
        for col, (name, colour, key) in enumerate(items):
            cell = tk.Frame(grid, bg=BG_CARD)
            cell.grid(row=0, column=col, padx=4, sticky="ew")
            grid.columnconfigure(col, weight=1)

            tk.Label(cell, text=name, bg=BG_CARD, fg=colour, font=("Consolas", 8, "bold")).pack()
            lbl = tk.Label(cell, text="0", bg=BG_CARD, fg=TEXT_TITLE, font=("Consolas", 14, "bold"))
            lbl.pack()
            self._stat_labels[key] = lbl

        self._session_time_lbl = tk.Label(card, text="Session Time: 00:00", bg=BG_CARD, fg=TEXT_MUTED, font=("Consolas", 8))
        self._session_time_lbl.pack(anchor="center", pady=(3, 0))
        self._tick_session_clock()

    def _render_track_view(self) -> None:
        for w in self._stats_container.winfo_children():
            w.destroy()

        card = self._card(self._stats_container, "🏎️ BUILT-IN OFFLINE 2D RACING SIMULATOR")
        self._track_canvas = tk.Canvas(card, width=540, height=210, bg="#080D18", highlightthickness=0)
        self._track_canvas.pack(fill="both", expand=True)
        self.offline_sim = OfflineRaceTrack(self._track_canvas, width=540, height=210)
        self.offline_sim.render()

    def _toggle_offline_track(self) -> None:
        self.show_offline_track = not self.show_offline_track
        self._track_toggle_btn.config(
            text="📊 Session Stats" if self.show_offline_track else "🏎️ Offline Track",
            fg=NEON_GOLD if self.show_offline_track else NEON_GREEN
        )
        self._build_stats_or_track_panel(self._right)

    def _toggle_pip_mode(self) -> None:
        self.is_pip_mode = not self.is_pip_mode
        if self.is_pip_mode:
            self.root.geometry("380x300")
            self.root.attributes('-topmost', True)
            for widget in self.root.winfo_children():
                widget.pack_forget()

            self._pip_frame = tk.Frame(self.root, bg=BG_PANEL, highlightbackground=NEON_CYAN, highlightthickness=1)
            self._pip_frame.pack(fill="both", expand=True)

            header = tk.Frame(self._pip_frame, bg=BG_PANEL)
            header.pack(fill="x", padx=4, pady=2)
            tk.Label(header, text="⚡ GESTURE HUD", bg=BG_PANEL, fg=NEON_CYAN, font=("Consolas", 8, "bold")).pack(side="left")

            tk.Button(header, text="🗗 RESTORE", bg=BG_CARD, fg=NEON_GOLD, font=("Consolas", 7, "bold"),
                      relief="flat", cursor="hand2", command=self._toggle_pip_mode).pack(side="right")

            self._pip_video = tk.Label(self._pip_frame, bg="#000000")
            self._pip_video.pack(fill="both", expand=True, padx=4, pady=2)

            self._pip_status = tk.Label(self._pip_frame, text="STEERING: STRAIGHT", bg=BG_PANEL, fg=NEON_GREEN,
                                        font=("Consolas", 9, "bold"))
            self._pip_status.pack(pady=(0, 2))
        else:
            self.root.attributes('-topmost', False)
            w, h = 1140, 850
            sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
            self.root.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")
            self._build_layout()

    def _toggle_audio(self) -> None:
        self.audio_enabled = not self.audio_enabled
        self.controller.set_audio_feedback(self.audio_enabled)
        set_setting("enable_audio_feedback", self.audio_enabled)
        self._audio_btn.config(
            text="🔊 AUDIO ON" if self.audio_enabled else "🔇 MUTED",
            fg=NEON_CYAN if self.audio_enabled else TEXT_DIM
        )

    def _on_camera_selected(self, _event=None) -> None:
        cam_str = self._cam_var.get()
        if cam_str == "Simulation":
            self.engine.simulation_mode = True
            self.engine.set_simulation_action("straight")
            return
        try:
            cam_idx = int(cam_str.split(" ")[-1])
            success = self.engine.set_camera(cam_idx)
            if success:
                set_setting("camera_index", cam_idx)
            else:
                messagebox.showerror("Camera Error", f"Could not connect to {cam_str}.")
        except Exception:
            pass

    def _open_add_game_modal(self) -> None:
        top = tk.Toplevel(self.root)
        top.title("➕ Add Custom Web Game Profile")
        top.configure(bg=BG_CARD)
        top.geometry("440x320")
        top.resizable(False, False)
        top.grab_set()

        tk.Label(top, text="🎮 ADD CUSTOM GAME PROFILE", bg=BG_CARD, fg=NEON_CYAN,
                 font=("Consolas", 11, "bold")).pack(pady=8)

        form = tk.Frame(top, bg=BG_CARD, padx=16)
        form.pack(fill="both", expand=True)

        tk.Label(form, text="Game Name:", bg=BG_CARD, fg=TEXT_MUTED, font=("Consolas", 8)).grid(row=0, column=0, sticky="w", pady=4)
        name_entry = tk.Entry(form, width=32, font=("Consolas", 9))
        name_entry.grid(row=0, column=1, pady=4)

        tk.Label(form, text="Game URL:", bg=BG_CARD, fg=TEXT_MUTED, font=("Consolas", 8)).grid(row=1, column=0, sticky="w", pady=4)
        url_entry = tk.Entry(form, width=32, font=("Consolas", 9))
        url_entry.grid(row=1, column=1, pady=4)

        tk.Label(form, text="Genre:", bg=BG_CARD, fg=TEXT_MUTED, font=("Consolas", 8)).grid(row=2, column=0, sticky="w", pady=4)
        genre_entry = tk.Entry(form, width=32, font=("Consolas", 9))
        genre_entry.insert(0, "CUSTOM RACER")
        genre_entry.grid(row=2, column=1, pady=4)

        tk.Label(form, text="Mode:", bg=BG_CARD, fg=TEXT_MUTED, font=("Consolas", 8)).grid(row=3, column=0, sticky="w", pady=4)
        mode_cb = ttk.Combobox(form, values=["racing", "runner", "arcade", "drift", "air_mouse"], width=30, state="readonly")
        mode_cb.set("racing")
        mode_cb.grid(row=3, column=1, pady=4)

        def _save_game():
            g_name = name_entry.get().strip()
            g_url = url_entry.get().strip()
            if not g_name or not g_url:
                messagebox.showwarning("Incomplete", "Please provide both a Name and URL.")
                return
            new_g = {
                "id": f"custom_{int(time.time())}",
                "name": f"⭐ {g_name}",
                "genre": genre_entry.get().strip().upper(),
                "mode": mode_cb.get(),
                "url": g_url,
                "gestures": [
                    ("👈 Hand Left", "Steer Left", "←"),
                    ("👉 Hand Right", "Steer Right", "→"),
                    ("👍 Thumb Up", "Gas Throttle", "↑"),
                    ("✊ Closed Fist", "Brake", "↓"),
                ]
            }
            add_custom_game(new_g)
            self._all_games = get_all_games()
            self._game_dd["values"] = [g["name"] for g in self._all_games]
            self._game_var.set(new_g["name"])
            self._on_game_selected()
            top.destroy()

        tk.Button(top, text="💾 Save Custom Game", bg=NEON_GREEN, fg=BG_DEEP, font=("Consolas", 9, "bold"),
                  relief="flat", padx=12, pady=6, cursor="hand2", command=_save_game).pack(pady=12)

    def _launch_game(self) -> None:
        if getattr(self, "_launch_briefing_open", False):
            return
        self._launch_briefing_open = True
        self.controller.stop()

        top = tk.Toplevel(self.root)
        top.title(f"PRE-RACE CHECK — {self._active_game['name']}")
        top.configure(bg=BG_DEEP)
        top.geometry("760x510")
        top.resizable(False, False)
        top.transient(self.root)
        top.grab_set()

        head = tk.Frame(top, bg=BG_PANEL, padx=20, pady=13, highlightbackground=BORDER_GLOW, highlightthickness=1)
        head.pack(fill="x", padx=14, pady=(14, 10))
        tk.Label(head, text=f"🏁  PRE-RACE CHECK  /  {self._active_game.get('genre', 'RACING')}",
                 bg=BG_PANEL, fg=NEON_CYAN, font=("Consolas", 10, "bold")).pack(anchor="w")
        tk.Label(head, text=f"{self._active_game['name']} · check your hand positions and camera framing before launch",
                 bg=BG_PANEL, fg=TEXT_MUTED, font=("Consolas", 8)).pack(anchor="w", pady=(5, 0))

        body = tk.Frame(top, bg=BG_DEEP, padx=14)
        body.pack(fill="both", expand=True)
        guide = tk.Frame(body, bg=BG_CARD, padx=12, pady=10, highlightbackground=BORDER_GLOW, highlightthickness=1)
        guide.pack(side="left", fill="both", expand=True, padx=(0, 9))
        tk.Label(guide, text="HAND POSITION  →  ACTION  →  GAME INPUT", bg=BG_CARD,
                 fg=NEON_GOLD, font=("Consolas", 8, "bold")).pack(anchor="w", pady=(0, 8))
        for gesture_name, action_name, key_name in self._active_game.get("gestures", [])[:5]:
            row = tk.Frame(guide, bg=BG_DEEP, padx=9, pady=8, highlightbackground=BORDER_GLOW, highlightthickness=1)
            row.pack(fill="x", pady=3)
            tk.Label(row, text=gesture_name, bg=BG_DEEP, fg=NEON_CYAN,
                     font=("Consolas", 8, "bold"), anchor="w").pack(fill="x")
            tk.Label(row, text=f"{action_name}   ·   {key_name}", bg=BG_DEEP, fg=TEXT_BODY,
                     font=("Consolas", 8), anchor="w").pack(fill="x", pady=(3, 0))
        tk.Label(guide, text="Keep the full hand visible, fingers apart, and face a light source.",
                 bg=BG_CARD, fg=TEXT_MUTED, font=("Consolas", 8), wraplength=360, justify="left").pack(anchor="w", pady=(8, 0))

        preview = tk.Frame(body, bg=BG_CARD, padx=9, pady=9, highlightbackground=NEON_CYAN, highlightthickness=1)
        preview.pack(side="right", fill="y")
        tk.Label(preview, text="LIVE CAMERA / HAND TRACK", bg=BG_CARD, fg=NEON_CYAN,
                 font=("Consolas", 8, "bold")).pack(anchor="w", pady=(0, 7))
        preview_label = tk.Label(preview, bg="#05080e", width=300, height=225)
        preview_label.pack()
        preview_status = tk.Label(preview, text="Waiting for camera…", bg=BG_CARD, fg=TEXT_MUTED,
                                  font=("Consolas", 8), wraplength=285, justify="left")
        preview_status.pack(fill="x", pady=(7, 0))

        footer = tk.Frame(top, bg=BG_DEEP, padx=14, pady=12)
        footer.pack(fill="x")

        def close_briefing() -> None:
            self._launch_briefing_open = False
            try:
                top.grab_release()
                top.destroy()
            except tk.TclError:
                pass

        def enter_game() -> None:
            close_briefing()
            webbrowser.open(self._active_game["url"])
            self.start()
            self._gesture_label.config(text="🎮 GAME OPENED! CLICK SCREEN ONCE", fg=NEON_GOLD)
            self.root.after(900, self._focus_game_window)

        tk.Button(footer, text="CLOSE", bg=BG_CARD, fg=TEXT_MUTED, activebackground=BG_CARD_HOVER,
                  font=("Consolas", 8, "bold"), relief="flat", padx=14, pady=8,
                  command=close_briefing).pack(side="left")
        tk.Button(footer, text="ENTER GAME  →", bg=NEON_PURPLE, fg=TEXT_TITLE, activebackground="#5E17EB",
                  font=("Consolas", 9, "bold"), relief="flat", padx=20, pady=8,
                  command=enter_game).pack(side="right")

        def refresh_preview() -> None:
            if not top.winfo_exists():
                return
            frame = self._last_camera_preview
            if frame is not None:
                try:
                    resized = cv2.resize(frame, (300, 225))
                    rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
                    imgtk = ImageTk.PhotoImage(image=Image.fromarray(rgb))
                    preview_label.configure(image=imgtk)
                    preview_label.imgtk = imgtk
                    result = self._last_camera_result
                    if result and result.hand_detected:
                        detected = "BOTH HANDS" if result.is_two_handed else f"{result.handedness.upper()} HAND"
                        preview_status.config(text=f"{detected} · {result.gesture.replace('_', ' ').upper()} · {result.fps:.0f} FPS", fg=NEON_GREEN)
                    else:
                        preview_status.config(text="No hand detected · move into the frame", fg=NEON_GOLD)
                except Exception:
                    pass
            top.after(50, refresh_preview)

        top.protocol("WM_DELETE_WINDOW", close_briefing)
        refresh_preview()

    def _focus_game_window(self) -> None:
        GameController.focus_window_win32(BROWSER_TITLES)

    def _start_calibration(self) -> None:
        self.engine.start_calibration(duration_sec=3.0)
        self._calib_status.config(text="⚡ Hold neutral hand steady for 3s...", fg=NEON_GOLD)

    # ══════════════════════════════════════════════════════════════════════════
    # High-Performance Vision & UI Sync Loop
    # ══════════════════════════════════════════════════════════════════════════

    def start(self) -> None:
        if self.running:
            return
        self.running = True
        self._session_start = time.time()
        self._counts = {k: 0 for k in self._counts}
        self._start_btn.config(state="disabled")
        self._stop_btn.config(state="normal")
        self.root.after(300, self._focus_game_window)

        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self.running = False
        self.controller.stop()
        self._start_btn.config(state="normal")
        self._stop_btn.config(state="disabled")
        self._cam_placeholder()

    def _on_sim_key_press(self, event) -> None:
        if not self.engine.simulation_mode:
            return
        action = {"Left": "left", "a": "left", "A": "left", "Right": "right", "d": "right", "D": "right", "Up": "accelerate", "w": "accelerate", "W": "accelerate", "Down": "brake", "s": "brake", "S": "brake"}.get(event.keysym)
        if action:
            self.engine.set_simulation_action(action)

    def _on_sim_key_release(self, event) -> None:
        if self.engine.simulation_mode and event.keysym in {"Left", "Right", "Up", "Down", "a", "A", "d", "D", "w", "W", "s", "S"}:
            self.engine.set_simulation_action("straight")

    def _toggle(self) -> None:
        (self.stop if self.running else self.start)()

    def _loop(self) -> None:
        while self.running:
            try:
                frame, result = self.engine.get_frame()
            except Exception as exc:
                print(f"[VISION] Recoverable frame-processing error: {exc}")
                self.controller.stop()
                time.sleep(0.1)
                continue
            if frame is None:
                continue

            g = result.gesture
            angle = result.angle
            mode = self._active_game.get("mode", "racing")

            if self._launch_briefing_open:
                self.controller.stop()
                self._latest_ui = (frame, result, "straight" if result.hand_detected else "nohand")
                continue

            # ── Multi-Mode Gesture Mapping ────────────────────────────────────
            if not result.hand_detected:
                self.controller.stop()
                g_display = "nohand"

            elif mode == "air_mouse":
                if result.air_mouse_dx != 0 or result.air_mouse_dy != 0:
                    self.controller.move_mouse_rel(result.air_mouse_dx, result.air_mouse_dy)
                if result.is_pinch:
                    self.controller.mouse_set_down(True)
                    g_display = "action"
                else:
                    self.controller.mouse_set_down(False)
                    g_display = "straight"

            elif mode == "runner":
                if result.dynamic_swipe == "swipe_left" or g == "thumb_left":
                    self.controller.steer_left()
                    g_display = "left"
                elif result.dynamic_swipe == "swipe_right" or g == "thumb_right":
                    self.controller.steer_right()
                    g_display = "right"
                elif result.dynamic_swipe == "swipe_up" or g == "open_palm":
                    self.controller.trigger_jump()
                    g_display = "jump"
                elif result.dynamic_swipe == "swipe_down" or g == "fist":
                    self.controller.trigger_slide()
                    g_display = "slide"
                else:
                    self.controller.steer_straight()
                    g_display = "straight"

            elif mode == "arcade":
                if g == "thumb_left":
                    self.controller.steer_left()
                    g_display = "left"
                elif g == "thumb_right":
                    self.controller.steer_right()
                    g_display = "right"
                elif g == "open_palm":
                    self.controller.trigger_jump()
                    g_display = "jump"
                elif g == "point":
                    self.controller.trigger_action(True)
                    g_display = "action"
                elif g == "fist":
                    self.controller.brake()
                    g_display = "brake"
                else:
                    self.controller.steer_straight()
                    self.controller.trigger_action(False)
                    g_display = "straight"

            else:
                # Pro Racing & Dual-Hand Mode
                if g == "thumb_left":
                    self.controller.steer_left()
                    g_display = "left"
                elif g == "thumb_right":
                    self.controller.steer_right()
                    g_display = "right"
                elif g in ("open_palm", "thumb_up"):
                    self.controller.steer_straight()
                    self.controller.accelerate()
                    g_display = "gas"
                elif g in ("fist", "thumb_down"):
                    self.controller.steer_straight()
                    self.controller.brake()
                    g_display = "brake"
                elif g in ("point", "pinch"):
                    self.controller.trigger_nitro(True)
                    g_display = "nitro"
                else:
                    self.controller.steer_straight()
                    self.controller.release_throttle()
                    self.controller.trigger_nitro(False)
                    g_display = "straight"

            if self.show_offline_track and hasattr(self, "offline_sim"):
                self.offline_sim.update_physics(
                    self.controller.current_steering,
                    self.controller.accelerating,
                    self.controller.braking,
                    angle
                )

            if g_display != self._last_gesture and g_display in self._counts:
                self._counts[g_display] += 1
                self._last_gesture = g_display

            # Keep only the newest result. Tkinter must only be touched by its main thread.
            self._latest_ui = (frame, result, g_display)

    def _poll_latest_ui(self) -> None:
        """Render the newest vision result on Tk's main thread without frame backlog."""
        latest = self._latest_ui
        self._latest_ui = None
        if latest is not None and self.running:
            frame, result, gesture = latest
            self._sync_ui(frame, result, gesture)
            if not self.engine.is_calibrating and self._calib_status["text"].startswith("⚡"):
                self._calib_status.config(
                    text=f"Neutral calibrated: {self.engine.neutral_angle:.1f}°", fg=NEON_GREEN
                )
                set_setting("neutral_angle", self.engine.neutral_angle)
        self._ui_poll_id = self.root.after(UI_REFRESH_MS, self._poll_latest_ui)

    # ══════════════════════════════════════════════════════════════════════════
    # Batched Atomic UI Synchronizer
    # ══════════════════════════════════════════════════════════════════════════

    def _sync_ui(self, frame: np.ndarray, result, gesture: str) -> None:
        self._last_camera_preview = frame.copy()
        self._last_camera_result = result
        cfg = {
            "left":     ("👈  STEER LEFT",     NEON_BLUE,  "LEFT ←",     -42),
            "right":    ("👉  STEER RIGHT",    NEON_PINK,  "RIGHT →",     42),
            "gas":      ("👍  GAS ACCELERATE", NEON_GREEN, "GAS ↑",        0),
            "brake":    ("✊  BRAKE / REVERSE",NEON_RED,   "BRAKE ↓",      0),
            "jump":     ("🖐  SUPER JUMP",     NEON_GOLD,  "JUMP ↑",       0),
            "slide":    ("✊  POWER SLIDE",    NEON_PURPLE,"SLIDE ↓",      0),
            "nitro":    ("☝️  NITRO BOOST",    NEON_CYAN,  "NITRO ⚡",     0),
            "action":   ("☝️  ACTION FIRE",    NEON_PURPLE,"ACTION 💥",    0),
            "straight": ("👌  STRAIGHT / NEUTRAL", NEON_CYAN, "STRAIGHT",  0),
            "nohand":   ("🖐  NO HAND IN FRAME", NEON_RED,  "—",           0),
            "idle":     ("⬛  CONTROLLER IDLE", TEXT_MUTED, "IDLE",        0),
        }
        text, colour, steer_txt, wheel_t = cfg.get(gesture, cfg["idle"])

        # 1. Update Video Frame
        try:
            if self.is_pip_mode and hasattr(self, "_pip_video"):
                resized = cv2.resize(frame, (360, 220))
                rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
                imgtk = ImageTk.PhotoImage(image=Image.fromarray(rgb))
                self._pip_video.configure(image=imgtk)
                self._pip_video.imgtk = imgtk
                if hasattr(self, "_pip_status"):
                    self._pip_status.config(text=text, fg=colour)
                return
            elif hasattr(self, "_video_label"):
                resized = cv2.resize(frame, (VIDEO_W, VIDEO_H))
                rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
                imgtk = ImageTk.PhotoImage(image=Image.fromarray(rgb))
                self._video_label.configure(image=imgtk)
                self._video_label.imgtk = imgtk
        except Exception:
            pass

        # 2. Update Header Badges
        fcol = NEON_GREEN if result.fps >= 30 else NEON_GOLD if result.fps >= 15 else NEON_RED
        self._fps_badge.config(text=f"FPS: {result.fps:.0f}", fg=fcol)
        lcol = NEON_CYAN if result.latency_ms <= 20 else NEON_GOLD if result.latency_ms <= 40 else NEON_RED
        self._lat_badge.config(text=f"LATENCY: {result.latency_ms:.1f}ms", fg=lcol)

        # 3. Update Gesture State Badges
        self._gesture_label.config(text=text, fg=colour)
        self._steer_badge.config(text=steer_txt, bg=colour if gesture not in ("nohand", "idle") else BG_DEEP,
                                 fg=BG_DEEP if gesture not in ("nohand", "idle") else TEXT_MUTED)

        st = self.controller.state
        if st["accelerating"]:
            self._throttle_badge.config(text="ACCEL ↑", bg=NEON_GREEN, fg=BG_DEEP)
        elif st["braking"]:
            self._throttle_badge.config(text="BRAKE ↓", bg=NEON_RED, fg=TEXT_TITLE)
        else:
            self._throttle_badge.config(text="THROTTLE", bg=BG_DEEP, fg=TEXT_DIM)

        if st["nitro"] or st["action"]:
            self._nitro_badge.config(text="ACTION 💥", bg=NEON_CYAN, fg=BG_DEEP)
        else:
            self._nitro_badge.config(text="ACTION", bg=BG_DEEP, fg=TEXT_DIM)

        hand_txt = "DUAL HANDS" if result.is_two_handed else f"HAND: {result.handedness.upper()}" if gesture not in ("nohand", "idle") else "NO HAND"
        self._hand_badge.config(
            text=hand_txt,
            bg=NEON_CYAN if gesture not in ("nohand", "idle") else NEON_RED,
            fg=BG_DEEP
        )

        if result.angle is not None:
            self._angle_label.config(text=f"ANGLE: {result.angle:.1f}° (Neutral: {self.engine.neutral_angle:.1f}°)")
            self._steer_angle_val.config(text=f"{result.angle:.1f}°")
            self._wheel_target = -(result.angle - self.engine.neutral_angle)
        else:
            self._angle_label.config(text="ANGLE: --° (Neutral: 90°)")
            self._wheel_target = 0.0

        f_str = "".join(["✓ " if b else "· " for b in result.extended_fingers])
        self._finger_bits.config(text=f"FINGERS: [ {f_str}] ({result.finger_count}/5)")

        # 4. Update Stats or Track
        if self.show_offline_track and hasattr(self, "offline_sim"):
            self.offline_sim.render()
        elif hasattr(self, "_stat_labels"):
            for key, lbl in self._stat_labels.items():
                lbl.config(text=str(self._counts.get(key, 0)))

    # ══════════════════════════════════════════════════════════════════════════
    # Animated Digital Steering Wheel
    # ══════════════════════════════════════════════════════════════════════════

    def _draw_wheel(self, angle_deg: float) -> None:
        if not hasattr(self, "_wheel_canvas"):
            return
        c = self._wheel_canvas
        c.delete("all")
        cx = cy = WHEEL_SIZE // 2
        ro, ri, rh = WHEEL_SIZE // 2 - 8, WHEEL_SIZE // 2 - 20, 10

        c.create_oval(cx - ro, cy - ro, cx + ro, cy + ro, outline=BORDER_GLOW, width=3, fill=BG_DEEP)
        c.create_oval(cx - ri, cy - ri, cx + ri, cy + ri, outline=NEON_PURPLE, width=2, fill=BG_DEEP)

        for base in (0, 120, 240):
            rad = math.radians(angle_deg + base)
            x1, y1 = cx + rh * math.cos(rad), cy + rh * math.sin(rad)
            x2, y2 = cx + ri * math.cos(rad), cy + ri * math.sin(rad)
            c.create_line(x1, y1, x2, y2, fill=NEON_CYAN if base == 0 else TEXT_MUTED,
                          width=3 if base == 0 else 2)

        c.create_oval(cx - rh, cy - rh, cx + rh, cy + rh, fill=NEON_PURPLE, outline=NEON_CYAN, width=1)
        rd = math.radians(angle_deg)
        dx, dy = cx + (ro - 6) * math.cos(rd), cy + (ro - 6) * math.sin(rd)
        c.create_oval(dx - 4, dy - 4, dx + 4, dy + 4, fill=NEON_CYAN, outline=TEXT_TITLE)

    def _animate_wheel(self) -> None:
        diff = self._wheel_target - self._wheel_angle
        if diff > 180:   diff -= 360
        elif diff < -180: diff += 360
        self._wheel_angle += diff * 0.22
        self._draw_wheel(self._wheel_angle)
        self._wheel_anim_id = self.root.after(16, self._animate_wheel)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _on_sensitivity_change(self, val: str) -> None:
        dz = float(val)
        self.engine.deadzone_deg = dz
        set_setting("steer_deadzone_deg", dz)
        if hasattr(self, "_sens_val_lbl"):
            self._sens_val_lbl.config(text=f"{int(dz)}°")

    def _tick_session_clock(self) -> None:
        if self._session_start and self.running and hasattr(self, "_session_time_lbl"):
            e = int(time.time() - self._session_start)
            m, s = divmod(e, 60)
            self._session_time_lbl.config(text=f"Session Time: {m:02d}:{s:02d}")
        self.root.after(1000, self._tick_session_clock)

    def _card(self, parent: tk.Frame, title: str) -> tk.Frame:
        outer = tk.Frame(parent, bg=BORDER_GLOW, padx=1, pady=1)
        outer.pack(fill="x", pady=(0, 6))
        inner = tk.Frame(outer, bg=BG_CARD, padx=10, pady=6)
        inner.pack(fill="x")
        tk.Label(inner, text=title, bg=BG_CARD, fg=NEON_CYAN, font=("Consolas", 8, "bold")).pack(anchor="w")
        return inner

    def _badge(self, parent: tk.Frame, text: str, colour: str) -> tk.Label:
        return tk.Label(parent, text=text, bg=BG_DEEP, fg=colour,
                        font=("Consolas", 8, "bold"), padx=6, pady=2,
                        highlightbackground=BORDER_GLOW, highlightthickness=1)

    def _cam_placeholder(self) -> None:
        ph = np.zeros((VIDEO_H, VIDEO_W, 3), dtype=np.uint8)
        ph[:] = (10, 15, 25)
        cv2.putText(ph, "NEURAL VISION STREAM", (VIDEO_W // 2 - 130, VIDEO_H // 2 - 15),
                    cv2.FONT_HERSHEY_DUPLEX, 0.7, (0, 255, 209), 1, cv2.LINE_AA)
        cv2.putText(ph, "Select Game & Press START (Spacebar)", (VIDEO_W // 2 - 160, VIDEO_H // 2 + 18),
                    cv2.FONT_HERSHEY_DUPLEX, 0.45, (130, 145, 175), 1, cv2.LINE_AA)
        rgb = cv2.cvtColor(ph, cv2.COLOR_BGR2RGB)
        imgtk = ImageTk.PhotoImage(image=Image.fromarray(rgb))
        self._video_label.configure(image=imgtk)
        self._video_label.imgtk = imgtk

    def _on_close(self) -> None:
        self.running = False
        self.controller.stop()
        self.engine.release()
        save_settings(RUNTIME_SETTINGS)
        if self._wheel_anim_id:
            self.root.after_cancel(self._wheel_anim_id)
        if self._ui_poll_id:
            self.root.after_cancel(self._ui_poll_id)
        self.root.destroy()
