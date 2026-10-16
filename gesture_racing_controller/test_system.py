"""
test_system.py — Automated Verification & Unit Tests for Gesture Gaming Controller (v3.0 Ultra)
═══════════════════════════════════════════════════════════════════════════════════════════════
Verifies module imports, single & dual-hand trigonometry, state transitions,
adaptive smoothing math, settings persistence, and game profile integrity.
"""

import unittest
import math
import os
import tempfile
import json
import time
from dataclasses import dataclass
from unittest.mock import patch

from config import (
    STEER_LEFT_MIN, STEER_LEFT_MAX, STEER_RIGHT_MIN, STEER_RIGHT_MAX,
    NEUTRAL_ANGLE_DEFAULT, STEER_DEADZONE_DEG, ANGLE_SMOOTHING_ALPHA,
    load_settings, save_settings, get_setting, set_setting, SETTINGS_FILE
)
from games import get_all_games, add_custom_game, remove_custom_game, BROWSER_TITLES
from game_controller import GameController


class TestGestureSystem(unittest.TestCase):

    def test_imports(self):
        """Verify all core dependencies and project modules import cleanly."""
        import cv2
        import mediapipe as mp
        import pyautogui
        import numpy as np
        from PIL import Image, ImageTk
        from gesture_engine import GestureEngine, GestureResult
        from ui import AppUI, OfflineRaceTrack

        self.assertTrue(True, "All imports succeeded")

    def test_game_catalog_integrity(self):
        """Ensure all game catalog entries have valid URLs, genres, and gestures."""
        catalog = get_all_games()
        self.assertGreaterEqual(len(catalog), 8)
        for game in catalog:
            self.assertIn("name", game)
            self.assertIn("url", game)
            self.assertTrue(game["url"].startswith("http"))
            self.assertIn("genre", game)
            self.assertIn("gestures", game)
            self.assertGreater(len(game["gestures"]), 0)
            self.assertIn("crazygames.com/game/", game["url"])

    def test_custom_game_addition(self):
        """Verify dynamic custom game creation and removal."""
        custom = {
            "id": "test_game_123",
            "name": "⭐ Test Racing Game",
            "genre": "ARCADE",
            "mode": "racing",
            "url": "https://poki.com",
            "gestures": [("👈 Left", "Steer", "←")]
        }
        add_custom_game(custom)
        games_after = get_all_games()
        self.assertTrue(any(g["id"] == "test_game_123" for g in games_after))

        remove_custom_game("test_game_123")
        games_cleaned = get_all_games()
        self.assertFalse(any(g["id"] == "test_game_123" for g in games_cleaned))

    def test_angle_math(self):
        """Verify single-hand inverted-Y atan2 trigonometry across all 4 quadrants."""
        # 1. Straight UP: dx=0, dy_raw=-100 -> dy_inv = 100 -> atan2(100, 0) = 90 deg
        wy, ty = 200, 100
        wx, tx = 200, 200
        ang_up = math.degrees(math.atan2(wy - ty, tx - wx))
        self.assertAlmostEqual(ang_up, 90.0)

        # 2. Steer RIGHT: dx=100, dy_raw=0 -> dy_inv = 0 -> atan2(0, 100) = 0 deg
        wy, ty = 200, 200
        wx, tx = 200, 300
        ang_right = math.degrees(math.atan2(wy - ty, tx - wx))
        self.assertAlmostEqual(ang_right, 0.0)

        # 3. Steer LEFT: dx=-100, dy_raw=0 -> dy_inv = 0 -> atan2(0, -100) = 180 deg
        wy, ty = 200, 200
        wx, tx = 200, 100
        ang_left = math.degrees(math.atan2(wy - ty, tx - wx))
        self.assertAlmostEqual(ang_left, 180.0)

        # 4. Straight DOWN: dx=0, dy_raw=100 -> dy_inv = -100 -> atan2(-100, 0) = -90 -> 270 deg
        wy, ty = 200, 300
        wx, tx = 200, 200
        ang_down = (math.degrees(math.atan2(wy - ty, tx - wx)) + 360) % 360
        self.assertAlmostEqual(ang_down, 270.0)

    def test_dual_hand_steering_trigonometry(self):
        """Verify dual-hand steering wheel angle calculation."""
        # Left wrist at (100, 200), Right wrist at (300, 200) -> Level wheel = 90°
        lx, ly = 100, 200
        rx, ry = 300, 200
        dx = rx - lx
        dy = ly - ry  # 0
        slope = math.degrees(math.atan2(dy, dx))
        angle_level = (90.0 + slope * 1.8) % 360
        self.assertAlmostEqual(angle_level, 90.0)

        # Turn Right: Right hand goes down (ry=250), Left hand goes up (ly=150) -> dy = 150 - 250 = -100
        # Slope is negative -> angle decreases from 90°
        slope_r = math.degrees(math.atan2(150 - 250, 200))
        angle_r = (90.0 + slope_r * 1.8) % 360
        self.assertLess(angle_r, 90.0)

    def test_game_controller_state_latching_and_throttle_decoupling(self):
        """Verify GameController handles state transitions without throttle-steering conflicts."""
        gc = GameController(audio_feedback=False)

        # Initial state
        self.assertEqual(gc.current_steering, "straight")
        self.assertFalse(gc.accelerating)
        self.assertFalse(gc.braking)

        # Steer Left
        gc.steer_left()
        self.assertEqual(gc.current_steering, "left")
        self.assertIn("left", gc._held_keys)
        self.assertNotIn("right", gc._held_keys)

        # Accelerate: Verify Gas does NOT press Right Arrow (avoids tilting flip bug)
        gc.accelerate()
        self.assertTrue(gc.accelerating)
        self.assertIn("up", gc._held_keys)
        self.assertNotIn("right", gc._held_keys)

        # Brake transition (should release accelerate)
        gc.brake()
        self.assertTrue(gc.braking)
        self.assertFalse(gc.accelerating)
        self.assertIn("down", gc._held_keys)
        self.assertNotIn("up", gc._held_keys)

        # Emergency Stop
        gc.stop()
        self.assertEqual(gc.current_steering, "straight")
        self.assertFalse(gc.accelerating)
        self.assertFalse(gc.braking)
        self.assertEqual(len(gc._held_keys), 0)

    def test_emergency_stop_releases_every_held_input(self):
        gc = GameController(audio_feedback=False)
        gc._held_keys = set(gc.ALL_MANAGED_KEYS)
        gc.mouse_clicked = True
        with patch("game_controller.pyautogui.keyUp") as key_up, patch("game_controller.pyautogui.mouseUp") as mouse_up, patch.object(gc, "_send_hardware_input"):
            gc.stop()
        self.assertEqual(gc._held_keys, set())
        self.assertFalse(gc.mouse_clicked)
        self.assertEqual(key_up.call_count, len(gc.ALL_MANAGED_KEYS))
        mouse_up.assert_called_once_with()

    def test_settings_persistence(self):
        """Verify settings save and load roundtrip."""
        settings = load_settings()
        self.assertIn("neutral_angle", settings)
        self.assertIn("steer_deadzone_deg", settings)

        orig_deadzone = settings["steer_deadzone_deg"]
        set_setting("steer_deadzone_deg", 33.0)
        reloaded = load_settings()
        self.assertEqual(reloaded["steer_deadzone_deg"], 33.0)

        # Restore
        set_setting("steer_deadzone_deg", orig_deadzone)

    def test_simulation_mode_actions_are_deterministic(self):
        from unittest.mock import patch
        from gesture_engine import GestureEngine
        with patch.object(GestureEngine, "_init_camera", return_value=False):
            engine = GestureEngine()
        expected = {"left": "thumb_left", "right": "thumb_right", "accelerate": "open_palm", "brake": "fist", "straight": "none"}
        for action, gesture in expected.items():
            engine.set_simulation_action(action)
            frame, result = engine._simulation_frame()
            self.assertIsNotNone(frame)
            self.assertEqual(result.gesture, gesture)
        engine.release()

    def test_camera_read_failure_returns_safe_reconnect_frame(self):
        from gesture_engine import GestureEngine
        class FailedCapture:
            def isOpened(self): return True
            def read(self): return False, None
        engine = GestureEngine.__new__(GestureEngine)
        engine.simulation_mode = False
        engine.cap = FailedCapture()
        engine.camera_index = 0
        engine._prev_tick = time.time()
        engine.fps = 30.0
        engine.latency_ms = 0.0
        engine.is_calibrating = False
        engine._camera_failures = 0
        engine._last_camera_frame = None
        frame, result = engine.get_frame()
        self.assertIsNotNone(frame)
        self.assertFalse(result.hand_detected)
        self.assertEqual(engine._camera_failures, 1)

    def test_offline_track_responds_to_all_driving_actions(self):
        from ui import OfflineRaceTrack
        track = OfflineRaceTrack.__new__(OfflineRaceTrack)
        track.w, track.h = 540, 210
        track.car_x, track.car_y, track.car_angle, track.speed = 120.0, 175.0, 0.0, 1.0
        track.max_speed, track.accel, track.friction, track.steer_speed = 7.5, 0.32, 0.94, 4.2
        track.lap_count, track.lap_start_time, track.best_lap, track.checkpoint_passed = 0, 0.0, None, False
        track.update_physics("left", False, False)
        self.assertLess(track.car_angle, 0)
        track.update_physics("right", False, False)
        self.assertAlmostEqual(track.car_angle, 0)
        speed = track.speed
        track.update_physics("straight", True, False)
        self.assertGreater(track.speed, speed)
        speed = track.speed
        track.update_physics("straight", False, True)
        self.assertLess(track.speed, speed)

    def test_desktop_bridge_combines_throttle_steering_and_nitro(self):
        import local_input_bridge as bridge
        calls = []
        bridge.last_controls = {"steering": "STRAIGHT", "pedal": "IDLE", "nitro": False}
        bridge.last_game = "night-city"
        bridge.last_action = "IDLE"
        with patch.object(bridge.controller, "stop", side_effect=lambda: calls.append("stop")), \
             patch.object(bridge.controller, "accelerate", side_effect=lambda: calls.append("gas")), \
             patch.object(bridge.controller, "steer_left", side_effect=lambda: calls.append("left")), \
             patch.object(bridge.controller, "trigger_nitro", side_effect=lambda enabled: calls.append(("nitro", enabled))):
            bridge.apply_controls({"steering": "STRAIGHT", "pedal": "GAS", "nitro": False}, "night-city")
            calls.clear()
            bridge.apply_controls({"steering": "LEFT", "pedal": "GAS", "nitro": True}, "night-city")

        self.assertIn("left", calls)
        self.assertIn(("nitro", True), calls)
        self.assertNotIn("stop", calls)
        self.assertEqual(bridge.controller.key_mappings["space"], ["shift"])


if __name__ == "__main__":
    unittest.main()
