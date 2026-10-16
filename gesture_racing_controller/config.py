"""
config.py — Gesture Racing settings and visual theme
══════════════════════════════════════════════════════════════════════════════════════════════
Centralized parameters for computer vision, multi-hand tracking, adaptive smoothing,
audio dispatching, settings persistence (settings.json), visual design tokens, and runtime constants.
"""

import os
import json
from typing import Dict, Any

# ── Base Directory & Paths ───────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")

# ── Default Application Settings ──────────────────────────────────────────────
DEFAULT_SETTINGS: Dict[str, Any] = {
    "camera_index": 0,
    "target_fps": 60,
    "ui_refresh_ms": 12,
    "enable_audio_feedback": True,
    "neutral_angle": 90.0,
    "steer_deadzone_deg": 25.0,
    "hysteresis_deg": 3.0,
    "adaptive_smoothing": True,
    "smoothing_alpha_min": 0.22,
    "smoothing_alpha_max": 0.85,
    "control_mode": "racing",       # "racing" | "two_hand" | "runner" | "air_mouse" | "arcade"
    "handedness_auto": True,
    "two_hand_enabled": True,
    "air_mouse_sensitivity": 1.6,
    "pwm_steering_enabled": True,
    "active_theme": "gesture_racing",
    "last_selected_game": "🏔  Hill Climb Racing",
    "custom_games": [],
    "custom_keybindings": {},
}

def load_settings() -> Dict[str, Any]:
    """Loads persistent user settings from settings.json or initializes defaults."""
    if not os.path.exists(SETTINGS_FILE):
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            merged = DEFAULT_SETTINGS.copy()
            merged.update(data)
            return merged
    except Exception as e:
        print(f"[CONFIG] Warning: Could not parse settings.json ({e}). Using defaults.")
        return DEFAULT_SETTINGS.copy()

def save_settings(settings: Dict[str, Any]) -> bool:
    """Saves updated user settings dictionary to settings.json."""
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
        return True
    except Exception as e:
        print(f"[CONFIG] Error saving settings.json: {e}")
        return False

# Initialize runtime settings
RUNTIME_SETTINGS = load_settings()

def get_setting(key: str, default: Any = None) -> Any:
    return RUNTIME_SETTINGS.get(key, default if default is not None else DEFAULT_SETTINGS.get(key))

def set_setting(key: str, value: Any, auto_save: bool = True) -> None:
    RUNTIME_SETTINGS[key] = value
    if auto_save:
        save_settings(RUNTIME_SETTINGS)

# ── Camera & Stream Settings ──────────────────────────────────────────────────
CAMERA_INDEX       = RUNTIME_SETTINGS.get("camera_index", 0)
FRAME_WIDTH        = 640
FRAME_HEIGHT       = 480
TARGET_FPS         = RUNTIME_SETTINGS.get("target_fps", 60)
UI_REFRESH_MS      = RUNTIME_SETTINGS.get("ui_refresh_ms", 12)

# ── MediaPipe Model Confidence ────────────────────────────────────────────────
DETECTION_CONFIDENCE = 0.70
TRACKING_CONFIDENCE  = 0.70
MAX_NUM_HANDS        = 2   # Enabled dual-hand tracking for true steering wheel mode

# ── Steering & Orientation Thresholds (in degrees, 0-360 range) ───────────────
NEUTRAL_ANGLE_DEFAULT = float(RUNTIME_SETTINGS.get("neutral_angle", 90.0))
STEER_DEADZONE_DEG    = float(RUNTIME_SETTINGS.get("steer_deadzone_deg", 25.0))
HYSTERESIS_DEG        = float(RUNTIME_SETTINGS.get("hysteresis_deg", 3.0))

# Baseline directional thresholds
STEER_LEFT_MIN  = 115
STEER_LEFT_MAX  = 260
STEER_RIGHT_MIN = 65
STEER_RIGHT_MAX = 280

# ── Temporal & Adaptive Smoothing ─────────────────────────────────────────────
ADAPTIVE_SMOOTHING   = bool(RUNTIME_SETTINGS.get("adaptive_smoothing", True))
SMOOTHING_ALPHA_MIN  = float(RUNTIME_SETTINGS.get("smoothing_alpha_min", 0.22))
SMOOTHING_ALPHA_MAX  = float(RUNTIME_SETTINGS.get("smoothing_alpha_max", 0.85))
ANGLE_SMOOTHING_ALPHA = 0.35
POSITION_SMOOTHING_ALPHA = 0.40

# ── Dynamic Gesture (Swipe & Mouse) Parameters ────────────────────────────────
SWIPE_DELTA_THRESHOLD = 0.045
SWIPE_COOLDOWN_SEC    = 0.26
AIR_MOUSE_SENSITIVITY = float(RUNTIME_SETTINGS.get("air_mouse_sensitivity", 1.6))
AIR_MOUSE_CLICK_DIST  = 0.050

# ── 5-Finger Extension Distance Ratios ────────────────────────────────────────
FINGER_EXTENDED_RATIO = 1.15
THUMB_EXTENDED_RATIO  = 1.10
PINCH_THRESHOLD_DIST  = 0.065

# ── Audio Feedback ────────────────────────────────────────────────────────────
ENABLE_AUDIO_FEEDBACK = bool(RUNTIME_SETTINGS.get("enable_audio_feedback", True))

# ── Gesture Racing theme tokens ──────────────────────────────────────────────
BG_DEEP       = "#080B12"
BG_PANEL      = "#0D1119"
BG_CARD       = "#141A24"
BG_CARD_HOVER = "#1A222D"
BORDER_GLOW   = "#35433C"

NEON_CYAN     = "#66E6DE"
NEON_PURPLE   = "#B49AFF"
NEON_PINK     = "#FD76A8"
NEON_BLUE     = "#7DA6FF"
NEON_GREEN    = "#D3FC51"
NEON_GOLD     = "#FF985E"
NEON_RED      = "#FF647C"

TEXT_TITLE    = "#F0F0E9"
TEXT_BODY     = "#DEE2DA"
TEXT_MUTED    = "#858D88"
TEXT_DIM      = "#505954"

# ── Application Metadata ──────────────────────────────────────────────────────
APP_NAME    = "GESTURE / RACING"
APP_VERSION = "1.0"
APP_SUBTITLE = "WEBCAM GESTURE CONTROLLER"
