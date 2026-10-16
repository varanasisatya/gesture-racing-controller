"""Local-only, allowlisted keyboard bridge for the browser cockpit."""

from __future__ import annotations

import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from game_controller import GameController


PORT = int(os.environ.get("MOTION_COCKPIT_PORT", "8765"))
ALLOWED_ORIGINS = {
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://website-jet-tau-52.vercel.app",
}
EXTRA_ORIGINS = os.environ.get("MOTION_COCKPIT_ALLOWED_ORIGINS", "")
ALLOWED_ORIGINS.update(origin.strip() for origin in EXTRA_ORIGINS.split(",") if origin.strip())
VALID_ACTIONS = {"IDLE", "LEFT", "RIGHT", "GAS", "BRAKE", "REVERSE", "ACTION"}
VALID_GAMES = {"circuit", "moto-x3m", "drift-hunters", "crazy-grand-prix", "rally", "night-city", "runner", "real-car-driving"}
LEASE_SECONDS = 0.9

controller = GameController(audio_feedback=False)
state_lock = threading.Lock()
last_action = "IDLE"
last_game = "circuit"
last_controls = {"steering": "STRAIGHT", "pedal": "IDLE", "nitro": False}
last_seen = time.monotonic()
active = False


def _legacy_controls(action: str) -> dict[str, str | bool]:
    controls: dict[str, str | bool] = {"steering": "STRAIGHT", "pedal": "IDLE", "nitro": False}
    if action in {"LEFT", "RIGHT"}:
        controls["steering"] = action
    elif action in {"GAS", "BRAKE", "REVERSE"}:
        controls["pedal"] = action
    elif action == "ACTION":
        controls["nitro"] = True
    return controls


def apply_controls(controls: dict[str, str | bool], game: str) -> None:
    global last_action, last_game, last_controls
    with state_lock:
        previous = last_controls
        if game != last_game:
            controller.stop()
            previous = {"steering": "STRAIGHT", "pedal": "IDLE", "nitro": False}
        if controls == last_controls and game == last_game:
            return
        controller.key_mappings["brake"] = ["down", "s"]
        # Night City Racing binds NOS to Shift. Sending Space there applies the
        # handbrake, which makes a correctly detected thumb-up look like a stop.
        controller.key_mappings["space"] = ["shift"] if game == "night-city" else ["space"]
        steering = controls["steering"]
        if steering != previous["steering"]:
            if steering == "LEFT":
                controller.steer_left()
            elif steering == "RIGHT":
                controller.steer_right()
            else:
                controller.steer_straight()

        pedal = controls["pedal"]
        if pedal != previous["pedal"]:
            if pedal == "GAS":
                controller.accelerate()
            elif pedal in {"BRAKE", "REVERSE"}:
                controller.brake()
            elif previous["pedal"] in {"GAS", "BRAKE", "REVERSE"}:
                controller.release_throttle()

        if controls["nitro"] != previous["nitro"]:
            controller.trigger_nitro(bool(controls["nitro"]))

        active_actions = []
        if steering in {"LEFT", "RIGHT"}:
            active_actions.append(steering)
        if pedal != "IDLE":
            active_actions.append(str(pedal))
        if controls["nitro"]:
            active_actions.append("ACTION")
        last_action = "+".join(active_actions) if active_actions else "IDLE"
        last_game = game
        last_controls = dict(controls)


def apply_action(action: str, game: str) -> None:
    """Compatibility wrapper for older callers using a single action."""
    apply_controls(_legacy_controls(action), game)


def watchdog() -> None:
    global active, last_action, last_controls
    while True:
        time.sleep(0.15)
        with state_lock:
            expired = active and time.monotonic() - last_seen > LEASE_SECONDS
            if expired:
                controller.stop()
                last_action = "IDLE"
                last_controls = {"steering": "STRAIGHT", "pedal": "IDLE", "nitro": False}
                active = False


class Handler(BaseHTTPRequestHandler):
    server_version = "MotionCockpitBridge/1.0"

    def _cors(self) -> bool:
        origin = self.headers.get("Origin", "")
        if origin not in ALLOWED_ORIGINS:
            return False
        self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        if self.headers.get("Access-Control-Request-Private-Network") == "true":
            self.send_header("Access-Control-Allow-Private-Network", "true")
        return True

    def _json(self, status: int, data: dict) -> None:
        allowed = self.headers.get("Origin", "") in ALLOWED_ORIGINS
        if not allowed:
            status = 403
        payload = json.dumps(data).encode("utf-8") if allowed else b""
        self.send_response(status)
        if allowed:
            self._cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        if allowed:
            self.wfile.write(payload)

    def do_OPTIONS(self) -> None:
        if self.headers.get("Origin", "") not in ALLOWED_ORIGINS:
            self.send_error(403)
            return
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self) -> None:
        if self.path != "/health":
            self._json(404, {"ok": False})
            return
        if self.headers.get("Origin", "") not in ALLOWED_ORIGINS:
            self._json(403, {"ok": False, "error": "Origin not allowed"})
            return
        self._json(200, {"ok": True, "active": active, "action": last_action})

    def do_POST(self) -> None:
        global active, last_seen
        if self.path != "/control":
            self._json(404, {"ok": False})
            return
        if self.headers.get("Origin", "") not in ALLOWED_ORIGINS:
            self._json(403, {"ok": False, "error": "Origin not allowed"})
            return
        if self.headers.get_content_type() != "application/json":
            self._json(415, {"ok": False, "error": "JSON required"})
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if size < 1 or size > 256:
                raise ValueError("Invalid request size")
            body = json.loads(self.rfile.read(size))
            action = body.get("action")
            game = body.get("game", "circuit")
            enabled = body.get("enabled") is True
            if action not in VALID_ACTIONS or not isinstance(game, str):
                raise ValueError("Invalid action")
            if game not in VALID_GAMES:
                game = "circuit"
            controls = body.get("controls", _legacy_controls(action))
            if not isinstance(controls, dict) or set(controls) != {"steering", "pedal", "nitro"}:
                raise ValueError("Invalid controls")
            if controls["steering"] not in {"STRAIGHT", "LEFT", "RIGHT"}:
                raise ValueError("Invalid steering")
            if controls["pedal"] not in {"IDLE", "GAS", "BRAKE", "REVERSE"}:
                raise ValueError("Invalid pedal")
            if not isinstance(controls["nitro"], bool):
                raise ValueError("Invalid nitro state")
            if not enabled:
                controls = {"steering": "STRAIGHT", "pedal": "IDLE", "nitro": False}
        except (ValueError, TypeError, json.JSONDecodeError):
            self._json(400, {"ok": False, "error": "Invalid control message"})
            return

        with state_lock:
            last_seen = time.monotonic()
            active = enabled
        apply_controls(controls, game)
        self._json(200, {"ok": True, "active": active, "action": last_action, "game": last_game})

    def log_message(self, _format: str, *_args: object) -> None:
        pass


if __name__ == "__main__":
    if os.name != "nt":
        raise SystemExit("The game input bridge requires Windows.")
    threading.Thread(target=watchdog, daemon=True).start()
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    server.daemon_threads = True
    print(f"Gesture Racing local input bridge listening at http://127.0.0.1:{PORT}")
    print("Only the configured project website can send allowlisted game controls.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        controller.stop()
        server.server_close()
