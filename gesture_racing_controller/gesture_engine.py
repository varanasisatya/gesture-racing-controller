"""
gesture_engine.py — Advanced Multi-Gesture Neural Vision Pipeline (v3.0 Ultra)
═════════════════════════════════════════════════════════════════════════════
High-performance real-time hand-tracking engine combining MediaPipe 21-point
landmark extraction, dual-hand steering wheel trigonometry, adaptive velocity-scaled
EMA smoothing, 5-finger bitmask analysis, dynamic swipe velocity estimation,
air-mouse tracking, camera hot-swapping, and cybernetic holographic HUD rendering.
"""

import os
import urllib.request
import cv2
import mediapipe as mp
import math
import time
import numpy as np
from typing import Optional, Tuple, List, Dict
from dataclasses import dataclass, field

from config import (
    CAMERA_INDEX,
    FRAME_WIDTH,
    FRAME_HEIGHT,
    TARGET_FPS,
    DETECTION_CONFIDENCE,
    TRACKING_CONFIDENCE,
    MAX_NUM_HANDS,
    NEUTRAL_ANGLE_DEFAULT,
    STEER_DEADZONE_DEG,
    HYSTERESIS_DEG,
    ADAPTIVE_SMOOTHING,
    SMOOTHING_ALPHA_MIN,
    SMOOTHING_ALPHA_MAX,
    ANGLE_SMOOTHING_ALPHA,
    SWIPE_DELTA_THRESHOLD,
    SWIPE_COOLDOWN_SEC,
    AIR_MOUSE_SENSITIVITY,
    NEON_CYAN,
    NEON_PURPLE,
    NEON_PINK,
    NEON_BLUE,
    NEON_GREEN,
    NEON_GOLD,
    NEON_RED,
)


@dataclass
class GestureResult:
    """Rich telemetry packet emitted per video frame."""
    angle:            Optional[float]      # Smoothed steering angle (0-360°)
    raw_angle:        Optional[float]      # Unfiltered angle
    gesture:          str                  # Primary classified gesture
    extended_fingers: List[bool]           # [Thumb, Index, Middle, Ring, Pinky]
    finger_count:     int                  # Number of extended fingers (0-5)
    is_pinch:         bool                 # True if thumb & index tips are pinched
    dynamic_swipe:    Optional[str]        # "swipe_left"|"swipe_right"|"swipe_up"|"swipe_down"|None
    hand_detected:    bool
    num_hands:        int                  # 0, 1, or 2 hands
    is_two_handed:    bool                 # True if dual-hand steering wheel active
    handedness:       str                  # "Left" | "Right" | "Both" | "None"
    air_mouse_dx:     int                  # Relative X displacement for mouse
    air_mouse_dy:     int                  # Relative Y displacement for mouse
    latency_ms:       float                # Processing latency in milliseconds
    fps:              float
    calibrating:      bool                 # True if calibration is active
    calib_progress:   float                # 0.0 to 1.0


class GestureEngine:
    """Manages OpenCV webcam streaming, MediaPipe multi-hand inference, and next-gen gesture logic."""

    def __init__(self, camera_index: int = CAMERA_INDEX) -> None:
        self.camera_index = camera_index
        self.cap: Optional[cv2.VideoCapture] = None
        self.simulation_mode: bool = not self._init_camera(self.camera_index)
        self.simulation_action: str = "straight"
        self._camera_failures: int = 0
        self._last_camera_frame: Optional[np.ndarray] = None

        # MediaPipe Landmark graph connections
        self.HAND_CONNECTIONS = [
            (0, 1), (1, 2), (2, 3), (3, 4),
            (0, 5), (5, 6), (6, 7), (7, 8),
            (5, 9), (9, 10), (10, 11), (11, 12),
            (9, 13), (13, 14), (14, 15), (15, 16),
            (13, 17), (17, 18), (18, 19), (19, 20),
            (0, 17)
        ]

        # Dual compatibility: MediaPipe Solutions (legacy) or MediaPipe Tasks (modern)
        self._use_tasks_api = not (hasattr(mp, "solutions") and hasattr(mp.solutions, "hands"))
        if self._use_tasks_api:
            model_dir = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.join(model_dir, "hand_landmarker.task")
            if not os.path.exists(model_path):
                print("[VISION] Downloading MediaPipe hand landmarker model...")
                url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"
                urllib.request.urlretrieve(url, model_path)
            from mediapipe.tasks import python as mp_python
            from mediapipe.tasks.python import vision as mp_vision
            base_options = mp_python.BaseOptions(model_asset_path=model_path)
            options = mp_vision.HandLandmarkerOptions(
                base_options=base_options,
                num_hands=MAX_NUM_HANDS,
                min_hand_detection_confidence=DETECTION_CONFIDENCE,
                min_hand_presence_confidence=TRACKING_CONFIDENCE,
                min_tracking_confidence=TRACKING_CONFIDENCE,
            )
            self.detector = mp_vision.HandLandmarker.create_from_options(options)
            self.hands = None
        else:
            self._mp_hands = mp.solutions.hands
            self.hands = self._mp_hands.Hands(
                static_image_mode        = False,
                max_num_hands            = MAX_NUM_HANDS,
                min_detection_confidence = DETECTION_CONFIDENCE,
                min_tracking_confidence  = TRACKING_CONFIDENCE,
            )
            self.detector = None

        # Performance & Timing
        self._prev_tick: float = time.time()
        self.fps: float = 60.0
        self.latency_ms: float = 0.0

        # State & Adaptive Smoothing
        self.smoothed_angle: Optional[float] = None
        self._prev_angle: Optional[float] = None
        self.neutral_angle: float = NEUTRAL_ANGLE_DEFAULT
        self.deadzone_deg: float = STEER_DEADZONE_DEG
        self.hysteresis_deg: float = HYSTERESIS_DEG
        self.last_classified_steering: str = "straight"
        self._gesture_candidate: str = "none"
        self._gesture_candidate_frames: int = 0
        self._stable_gesture: str = "none"

        # Air-Mouse State Tracking
        self._prev_index_pos: Optional[Tuple[float, float]] = None
        self.air_mouse_mode: bool = False

        # Dynamic Swipe Tracking
        self._prev_wrist_pos: Optional[Tuple[float, float]] = None
        self._prev_pos_time: float = time.time()
        self._last_swipe_time: float = 0.0

        # Calibration State
        self.is_calibrating: bool = False
        self._calib_start_time: float = 0.0
        self._calib_duration: float = 3.0
        self._calib_samples: List[float] = []

    # ── Camera Management & High-Speed Ingestion ──────────────────────────────

    def _init_camera(self, index: int) -> bool:
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass
        
        # Try MSMF (Media Foundation) first as it is often more reliable on modern Windows laptops
        self.cap = cv2.VideoCapture(index, cv2.CAP_MSMF)
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(index)
            
        if self.cap.isOpened():
            try:
                self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
            except Exception:
                pass
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,  FRAME_WIDTH)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
            self.cap.set(cv2.CAP_PROP_FPS, TARGET_FPS)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Zero buffer lag
            self.camera_index = index
            return True
        return False

    def set_camera(self, index: int) -> bool:
        success = self._init_camera(index)
        self.simulation_mode = not success
        if success:
            print(f"[VISION] Switched to Camera Index: {index}")
        return success

    @staticmethod
    def get_available_cameras(max_tested: int = 4) -> List[int]:
        available = []
        for i in range(max_tested):
            temp_cap = cv2.VideoCapture(i, cv2.CAP_MSMF)
            if not temp_cap.isOpened():
                temp_cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
            if not temp_cap.isOpened():
                temp_cap = cv2.VideoCapture(i)
            
            if temp_cap.isOpened():
                available.append(i)
                temp_cap.release()
        return available

    def set_simulation_action(self, action: str) -> None:
        allowed = {"left", "right", "accelerate", "brake", "straight"}
        self.simulation_action = action if action in allowed else "straight"

    def _simulation_frame(self) -> Tuple[np.ndarray, GestureResult]:
        mapping = {"left": ("thumb_left", 150.0), "right": ("thumb_right", 30.0), "accelerate": ("open_palm", 90.0), "brake": ("fist", 90.0), "straight": ("none", 90.0)}
        gesture, angle = mapping[self.simulation_action]
        frame = np.zeros((FRAME_HEIGHT, FRAME_WIDTH, 3), dtype=np.uint8)
        frame[:] = (10, 15, 25)
        cv2.putText(frame, "SIMULATION MODE - NO CAMERA", (55, 190), cv2.FONT_HERSHEY_DUPLEX, 0.75, (0, 255, 209), 2, cv2.LINE_AA)
        cv2.putText(frame, f"ACTION: {self.simulation_action.upper()}", (150, 245), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 215, 0), 2, cv2.LINE_AA)
        cv2.putText(frame, "Use Arrow Keys or WASD", (135, 290), cv2.FONT_HERSHEY_DUPLEX, 0.55, (180, 190, 210), 1, cv2.LINE_AA)
        return frame, GestureResult(angle=angle, raw_angle=angle, gesture=gesture, extended_fingers=[False] * 5, finger_count=0, is_pinch=False, dynamic_swipe=None, hand_detected=True, num_hands=0, is_two_handed=False, handedness="Simulated", air_mouse_dx=0, air_mouse_dy=0, latency_ms=0.0, fps=float(TARGET_FPS), calibrating=False, calib_progress=0.0)

    # ── Calibration ───────────────────────────────────────────────────────────

    def start_calibration(self, duration_sec: float = 3.0) -> None:
        self.is_calibrating = True
        self._calib_start_time = time.time()
        self._calib_duration = duration_sec
        self._calib_samples = []

    def _update_calibration(self, raw_angle: float) -> float:
        elapsed = time.time() - self._calib_start_time
        self._calib_samples.append(raw_angle)
        progress = min(elapsed / max(self._calib_duration, 0.1), 1.0)

        if progress >= 1.0:
            if self._calib_samples:
                rads = [math.radians(a) for a in self._calib_samples]
                sin_mean = sum(math.sin(r) for r in rads) / len(rads)
                cos_mean = sum(math.cos(r) for r in rads) / len(rads)
                mean_deg = math.degrees(math.atan2(sin_mean, cos_mean))
                if mean_deg < 0:
                    mean_deg += 360
                self.neutral_angle = mean_deg
            self.is_calibrating = False
            self._calib_samples = []
        return progress

    # ── Geometry & Feature Extraction ─────────────────────────────────────────

    @staticmethod
    def _dist_2d(p1, p2) -> float:
        dx = (p1.x - p2.x) * FRAME_WIDTH
        dy = (p1.y - p2.y) * FRAME_HEIGHT
        return math.hypot(dx, dy)

    @staticmethod
    def _joint_angle_deg(a, b, c) -> float:
        """Angle at b using normalized 3D landmarks, expressed in degrees."""
        va = ((a.x - b.x) * FRAME_WIDTH, (a.y - b.y) * FRAME_HEIGHT, (a.z - b.z) * FRAME_WIDTH)
        vc = ((c.x - b.x) * FRAME_WIDTH, (c.y - b.y) * FRAME_HEIGHT, (c.z - b.z) * FRAME_WIDTH)
        dot = sum(x * y for x, y in zip(va, vc))
        mag_a = math.sqrt(sum(x * x for x in va))
        mag_c = math.sqrt(sum(x * x for x in vc))
        if mag_a < 1e-6 or mag_c < 1e-6:
            return 0.0
        cosine = max(-1.0, min(1.0, dot / (mag_a * mag_c)))
        return math.degrees(math.acos(cosine))

    def _extract_finger_states(self, lm) -> Tuple[List[bool], int, bool]:
        """Estimate extension from joint straightness and palm-relative scale.

        This is less sensitive to how close a fingertip is to the wrist when a
        user rotates or moves their hand toward the camera.
        """
        finger_chain = [(5, 6, 7, 8), (9, 10, 11, 12), (13, 14, 15, 16), (17, 18, 19, 20)]
        extended = []
        wrist = lm[0]
        palm_width = max(self._dist_2d(lm[5], lm[17]), 1e-4)

        thumb_straight = (
            self._joint_angle_deg(lm[1], lm[2], lm[3]) > 138
            and self._joint_angle_deg(lm[2], lm[3], lm[4]) > 142
        )
        thumb_clear_of_palm = self._dist_2d(lm[4], lm[5]) > palm_width * 0.42
        thumb_ext = thumb_straight and thumb_clear_of_palm
        extended.append(thumb_ext)

        for mcp_idx, pip_idx, dip_idx, tip_idx in finger_chain:
            pip_angle = self._joint_angle_deg(lm[mcp_idx], lm[pip_idx], lm[dip_idx])
            dip_angle = self._joint_angle_deg(lm[pip_idx], lm[dip_idx], lm[tip_idx])
            reaches_past_joint = self._dist_2d(lm[tip_idx], wrist) > self._dist_2d(lm[pip_idx], wrist) * 1.04
            extended.append(pip_angle > 150 and dip_angle > 145 and reaches_past_joint)

        ext_count = sum(extended)
        pinch_dist = self._dist_2d(lm[4], lm[8])
        is_pinch = pinch_dist < palm_width * 0.32
        return extended, ext_count, is_pinch

    def _stabilize_gesture(self, candidate: str) -> str:
        """Require two consecutive frames before changing active gesture."""
        if candidate == "none":
            self._gesture_candidate = "none"
            self._gesture_candidate_frames = 0
            self._stable_gesture = "none"
            return "none"
        if candidate == self._gesture_candidate:
            self._gesture_candidate_frames += 1
        else:
            self._gesture_candidate = candidate
            self._gesture_candidate_frames = 1
        if self._gesture_candidate_frames >= 2:
            self._stable_gesture = candidate
        return self._stable_gesture

    def _extract_dynamic_swipe(self, wrist_pos: Tuple[float, float], now: float) -> Optional[str]:
        if self._prev_wrist_pos is None:
            self._prev_wrist_pos = wrist_pos
            self._prev_pos_time = now
            return None

        dt = now - self._prev_pos_time
        if dt < 0.015:
            return None

        dx = (wrist_pos[0] - self._prev_wrist_pos[0])
        dy = (wrist_pos[1] - self._prev_wrist_pos[1])

        self._prev_wrist_pos = wrist_pos
        self._prev_pos_time = now

        if (now - self._last_swipe_time) < SWIPE_COOLDOWN_SEC:
            return None

        swipe = None
        if abs(dx) > abs(dy):
            if dx > SWIPE_DELTA_THRESHOLD:
                swipe = "swipe_right"
            elif dx < -SWIPE_DELTA_THRESHOLD:
                swipe = "swipe_left"
        else:
            if dy < -SWIPE_DELTA_THRESHOLD:
                swipe = "swipe_up"
            elif dy > SWIPE_DELTA_THRESHOLD:
                swipe = "swipe_down"

        if swipe:
            self._last_swipe_time = now

        return swipe

    # ── Adaptive Velocity-Based Smoothing ─────────────────────────────────────

    def _apply_adaptive_smoothing(self, raw_angle: float) -> float:
        if self.smoothed_angle is None:
            self.smoothed_angle = raw_angle
            self._prev_angle = raw_angle
            return raw_angle

        diff = (raw_angle - self.smoothed_angle + 180) % 360 - 180

        if ADAPTIVE_SMOOTHING:
            angular_speed = abs(diff)
            alpha_range = SMOOTHING_ALPHA_MAX - SMOOTHING_ALPHA_MIN
            alpha = SMOOTHING_ALPHA_MIN + min(angular_speed / 40.0, 1.0) * alpha_range
        else:
            alpha = ANGLE_SMOOTHING_ALPHA

        self.smoothed_angle = (self.smoothed_angle + diff * alpha) % 360
        self._prev_angle = self.smoothed_angle
        return self.smoothed_angle

    # ── Main Video Processing Pipeline ────────────────────────────────────────

    def get_frame(self) -> Tuple[Optional[np.ndarray], GestureResult]:
        t_start = time.time()
        if self.simulation_mode:
            time.sleep(1.0 / max(TARGET_FPS, 1))
            return self._simulation_frame()
        if self.cap is None or not self.cap.isOpened():
            if not self._init_camera(self.camera_index):
                self.simulation_mode = True
                return self._simulation_frame()

        success, img = self.cap.read() if self.cap else (False, None)

        t_now = time.time()
        dt = max(t_now - self._prev_tick, 1e-6)
        instant_fps = 1.0 / dt
        self.fps = self.fps * 0.9 + instant_fps * 0.1  # Smooth FPS display
        self._prev_tick = t_now

        if not success or img is None:
            self._camera_failures += 1
            time.sleep(0.05)
            if self._camera_failures % 10 == 0:
                self._init_camera(self.camera_index)
            if self._camera_failures >= 30:
                print("[VISION] Camera signal remained unavailable; switching to Simulation Mode.")
                self.simulation_mode = True
                return self._simulation_frame()
            self.latency_ms = (time.time() - t_start) * 1000.0
            fallback = self._last_camera_frame.copy() if self._last_camera_frame is not None else np.zeros((FRAME_HEIGHT, FRAME_WIDTH, 3), dtype=np.uint8)
            cv2.rectangle(fallback, (0, 0), (FRAME_WIDTH, 46), (15, 15, 35), -1)
            cv2.putText(fallback, "CAMERA SIGNAL LOST - RECONNECTING", (55, 30), cv2.FONT_HERSHEY_DUPLEX, 0.65, (0, 64, 255), 2, cv2.LINE_AA)
            return fallback, GestureResult(
                angle=None, raw_angle=None, gesture="none",
                extended_fingers=[False]*5, finger_count=0,
                is_pinch=False, dynamic_swipe=None,
                hand_detected=False, num_hands=0,
                is_two_handed=False, handedness="None",
                air_mouse_dx=0, air_mouse_dy=0,
                latency_ms=self.latency_ms, fps=self.fps,
                calibrating=self.is_calibrating, calib_progress=0.0
            )

        self._camera_failures = 0
        img = cv2.flip(img, 1)
        self._last_camera_frame = img.copy()
        h, w, _ = img.shape
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        landmarks_list = []
        handedness_list = []

        if self._use_tasks_api:
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            results = self.detector.detect(mp_image)
            if results.hand_landmarks:
                landmarks_list = results.hand_landmarks
                if results.handedness:
                    handedness_list = [h[0].category_name for h in results.handedness]
        else:
            results = self.hands.process(rgb)
            if results.multi_hand_landmarks:
                landmarks_list = [hl.landmark for hl in results.multi_hand_landmarks]
                if results.multi_handedness:
                    handedness_list = [h.classification[0].label for h in results.multi_handedness]

        raw_angle:      Optional[float] = None
        classified:     str             = "none"
        extended_flags: List[bool]      = [False] * 5
        finger_count:   int             = 0
        is_pinch:       bool            = False
        dynamic_swipe:  Optional[str]   = None
        calib_prog:     float           = 0.0
        is_two_handed:  bool            = False
        handedness_str: str             = "None"
        air_dx:         int             = 0
        air_dy:         int             = 0

        num_detected_hands = len(landmarks_list)

        if num_detected_hands >= 2:
            # ══════════════════════════════════════════════════════════════════
            # DUAL-HAND STEERING WHEEL MODE (Authentic Virtual Steering)
            # ══════════════════════════════════════════════════════════════════
            is_two_handed = True
            handedness_str = "Both"

            hand1_lm = landmarks_list[0]
            hand2_lm = landmarks_list[1]

            w1_x, w1_y = hand1_lm[0].x * w, hand1_lm[0].y * h
            w2_x, w2_y = hand2_lm[0].x * w, hand2_lm[0].y * h

            if w1_x < w2_x:
                left_wrist = (w1_x, w1_y)
                right_wrist = (w2_x, w2_y)
            else:
                left_wrist = (w2_x, w2_y)
                right_wrist = (w1_x, w1_y)

            dx_w = right_wrist[0] - left_wrist[0]
            dy_w = left_wrist[1] - right_wrist[1]
            wheel_slope_angle = math.degrees(math.atan2(dy_w, max(dx_w, 1e-5)))

            raw_angle = (90.0 + wheel_slope_angle * 1.8) % 360
            active_angle = self._apply_adaptive_smoothing(raw_angle)

            extended_flags, finger_count, is_pinch = self._extract_finger_states(hand1_lm)

            diff_from_neutral = (active_angle - self.neutral_angle + 180) % 360 - 180
            dz = self.deadzone_deg
            h_buf = self.hysteresis_deg if self.last_classified_steering != "straight" else 0.0

            if diff_from_neutral < -(dz - h_buf):
                classified = "thumb_left"
                self.last_classified_steering = "left"
            elif diff_from_neutral > (dz - h_buf):
                classified = "thumb_right"
                self.last_classified_steering = "right"
            else:
                classified = "thumb_up"
                self.last_classified_steering = "straight"

            classified = self._stabilize_gesture(classified)
            self._render_dual_hand_hud(img, landmarks_list, int(left_wrist[0]), int(left_wrist[1]),
                                       int(right_wrist[0]), int(right_wrist[1]), active_angle, classified)

        elif num_detected_hands == 1:
            # ══════════════════════════════════════════════════════════════════
            # SINGLE-HAND TILT & AIR-MOUSE MODE
            # ══════════════════════════════════════════════════════════════════
            lm = landmarks_list[0]
            handedness_str = handedness_list[0] if handedness_list else "Right"

            extended_flags, finger_count, is_pinch = self._extract_finger_states(lm)

            wrist     = lm[0]
            thumb_tip = lm[4]
            index_tip = lm[8]
            mid_tip   = lm[12]

            wx, wy = int(wrist.x * w), int(wrist.y * h)
            tx, ty = int(thumb_tip.x * w), int(thumb_tip.y * h)
            ix, iy = int(index_tip.x * w), int(index_tip.y * h)
            mx, my = int(mid_tip.x * w), int(mid_tip.y * h)

            dynamic_swipe = self._extract_dynamic_swipe((wrist.x, wrist.y), t_now)

            if self._prev_index_pos is not None:
                adx = (index_tip.x - self._prev_index_pos[0]) * w * AIR_MOUSE_SENSITIVITY
                ady = (index_tip.y - self._prev_index_pos[1]) * h * AIR_MOUSE_SENSITIVITY
                air_dx = int(adx)
                air_dy = int(ady)
            self._prev_index_pos = (index_tip.x, index_tip.y)

            if extended_flags[0] and finger_count <= 2:
                target_x, target_y = tx, ty
            else:
                target_x, target_y = mx, my

            angle = math.degrees(math.atan2(wy - target_y, target_x - wx))
            if angle < 0:
                angle += 360
            raw_angle = angle

            active_angle = self._apply_adaptive_smoothing(raw_angle)

            if self.is_calibrating:
                calib_prog = self._update_calibration(raw_angle)

            if is_pinch:
                classified = "pinch"
            elif finger_count >= 4:
                classified = "open_palm"
            elif finger_count == 0:
                classified = "fist"
            elif extended_flags[1] and finger_count == 1:
                classified = "point"
            elif extended_flags[1] and extended_flags[2] and finger_count == 2:
                classified = "peace"
            elif active_angle < (50 + self.hysteresis_deg) or active_angle >= (310 - self.hysteresis_deg):
                classified = "thumb_right"
            elif (130 - self.hysteresis_deg) <= active_angle < (230 + self.hysteresis_deg):
                classified = "thumb_left"
            elif 230 <= active_angle < 310:
                classified = "thumb_down"
            else:
                classified = "thumb_up"

            classified = self._stabilize_gesture(classified)
            self._render_cyberpunk_hud(
                img, lm, wx, wy, target_x, target_y,
                active_angle, classified, finger_count, is_pinch,
                calib_prog, handedness_str
            )

        else:
            self._prev_wrist_pos = None
            self._prev_index_pos = None
            self.smoothed_angle = None
            self.last_classified_steering = "straight"
            self._stabilize_gesture("none")

        self.latency_ms = (time.time() - t_start) * 1000.0

        return img, GestureResult(
            angle            = self.smoothed_angle,
            raw_angle        = raw_angle,
            gesture          = classified,
            extended_fingers = extended_flags,
            finger_count     = finger_count,
            is_pinch         = is_pinch,
            dynamic_swipe    = dynamic_swipe,
            hand_detected    = num_detected_hands > 0,
            num_hands        = num_detected_hands,
            is_two_handed    = is_two_handed,
            handedness       = handedness_str,
            air_mouse_dx     = air_dx,
            air_mouse_dy     = air_dy,
            latency_ms       = self.latency_ms,
            fps              = self.fps,
            calibrating      = self.is_calibrating,
            calib_progress   = calib_prog,
        )

    # ── Cyberpunk Single-Hand HUD Overlay Generator ───────────────────────────

    def _render_cyberpunk_hud(
        self, img: np.ndarray, lm,
        wx: int, wy: int, tx: int, ty: int,
        angle: float, gesture: str, finger_count: int,
        is_pinch: bool, calib_prog: float, handedness: str
    ) -> None:
        h, w, _ = img.shape
        gesture_colors = {
            "thumb_left":  (246, 130, 59),    # Neon Blue
            "thumb_right": (22, 115, 249),    # Neon Orange
            "thumb_up":    (209, 255, 0),     # Neon Cyan
            "thumb_down":  (68, 23, 255),     # Neon Red
            "open_palm":   (0, 230, 118),     # Emerald Green
            "fist":        (68, 23, 255),     # Crimson Red
            "point":       (226, 43, 138),    # Electric Violet
            "peace":       (255, 105, 180),   # Neon Pink
            "pinch":       (0, 215, 255),     # Gold
            "none":        (140, 140, 140),
        }
        hud_col = gesture_colors.get(gesture, (0, 255, 209))

        for p1_idx, p2_idx in self.HAND_CONNECTIONS:
            x1, y1 = int(lm[p1_idx].x * w), int(lm[p1_idx].y * h)
            x2, y2 = int(lm[p2_idx].x * w), int(lm[p2_idx].y * h)
            cv2.line(img, (x1, y1), (x2, y2), (40, 55, 80), 2, cv2.LINE_AA)

        finger_tip_indices = [4, 8, 12, 16, 20]
        for i, pt in enumerate(lm):
            px, py = int(pt.x * w), int(pt.y * h)
            if i in finger_tip_indices:
                cv2.circle(img, (px, py), 8, hud_col, -1, cv2.LINE_AA)
                cv2.circle(img, (px, py), 10, (255, 255, 255), 2, cv2.LINE_AA)
            else:
                cv2.circle(img, (px, py), 4, (0, 255, 209), -1, cv2.LINE_AA)

        cv2.line(img, (wx, wy), (tx, ty), hud_col, 3, cv2.LINE_AA)
        cv2.circle(img, (wx, wy), 7, (0, 215, 255), -1, cv2.LINE_AA)
        cv2.circle(img, (tx, ty), 14, hud_col, 2, cv2.LINE_AA)
        cv2.putText(img, f"{angle:.0f}*", (tx + 16, ty - 10),
                    cv2.FONT_HERSHEY_DUPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)

        # Telemetry Badge
        badge_text = f"{gesture.upper().replace('_', ' ')}  [{handedness.upper()}]"
        cv2.rectangle(img, (0, h - 38), (len(badge_text) * 13 + 20, h), (10, 15, 25), -1)
        cv2.rectangle(img, (0, h - 38), (4, h), hud_col, -1)
        cv2.putText(img, badge_text, (14, h - 12),
                    cv2.FONT_HERSHEY_DUPLEX, 0.6, hud_col, 1, cv2.LINE_AA)

        # Guided Calibration Hologram Overlay
        if self.is_calibrating:
            bar_w = int(w * 0.7)
            bx1, by1 = int((w - bar_w) / 2), 20
            bx2, by2 = bx1 + bar_w, by1 + 24
            cv2.rectangle(img, (bx1, by1), (bx2, by2), (20, 25, 35), -1)
            cv2.rectangle(img, (bx1, by1), (bx1 + int(bar_w * calib_prog), by2), (0, 215, 255), -1)
            cv2.putText(img, f"CALIBRATING NEUTRAL: {int(calib_prog * 100)}%",
                        (bx1 + 10, by1 + 17), cv2.FONT_HERSHEY_DUPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
            cv2.circle(img, (w // 2, h // 2), 60, (0, 215, 255), 1, cv2.LINE_AA)
            cv2.drawMarker(img, (w // 2, h // 2), (0, 255, 209), cv2.MARKER_CROSS, 20, 1)

    # ── Dual-Hand Holographic Steering Wheel HUD Overlay ──────────────────────

    def _render_dual_hand_hud(
        self, img: np.ndarray, landmarks_list: List,
        lx: int, ly: int, rx: int, ry: int,
        angle: float, gesture: str
    ) -> None:
        h, w, _ = img.shape
        col = (0, 255, 209) if gesture == "thumb_up" else (246, 130, 59) if gesture == "thumb_left" else (22, 115, 249)

        for lm in landmarks_list:
            for p1_idx, p2_idx in self.HAND_CONNECTIONS:
                x1, y1 = int(lm[p1_idx].x * w), int(lm[p1_idx].y * h)
                x2, y2 = int(lm[p2_idx].x * w), int(lm[p2_idx].y * h)
                cv2.line(img, (x1, y1), (x2, y2), (40, 55, 80), 2, cv2.LINE_AA)

        cv2.line(img, (lx, ly), (rx, ry), col, 4, cv2.LINE_AA)
        cv2.circle(img, (lx, ly), 12, (255, 0, 128), -1, cv2.LINE_AA)
        cv2.circle(img, (rx, ry), 12, (0, 230, 118), -1, cv2.LINE_AA)

        mx, my = (lx + rx) // 2, (ly + ry) // 2
        cv2.circle(img, (mx, my), 24, col, 2, cv2.LINE_AA)
        cv2.circle(img, (mx, my), 5, (255, 255, 255), -1, cv2.LINE_AA)
        cv2.putText(img, f"{angle:.0f}*", (mx - 15, my - 30),
                    cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)

        badge_text = f"DUAL-HAND WHEEL: {gesture.upper()}"
        cv2.rectangle(img, (0, h - 38), (len(badge_text) * 13 + 20, h), (10, 15, 25), -1)
        cv2.rectangle(img, (0, h - 38), (4, h), col, -1)
        cv2.putText(img, badge_text, (14, h - 12),
                    cv2.FONT_HERSHEY_DUPLEX, 0.6, col, 1, cv2.LINE_AA)

    def release(self) -> None:
        try:
            if self.cap:
                self.cap.release()
        except Exception:
            pass
        if self.hands is not None:
            try:
                self.hands.close()
            except Exception:
                pass
        if self.detector is not None:
            try:
                self.detector.close()
            except Exception:
                pass
