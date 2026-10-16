"""
main.py — Master Entry Point for Gesture Gaming Controller (v3.0 Ultra)
═══════════════════════════════════════════════════════════════════════
Launches the touchless Human-Computer Interaction (HCI) neural game engine,
initializes the multi-hand vision pipeline and game controller, and manages the Tkinter UI.
"""

import sys
import tkinter as tk
from gesture_engine import GestureEngine
from game_controller import GameController
from ui import AppUI
from config import APP_NAME, APP_VERSION, ENABLE_AUDIO_FEEDBACK, CAMERA_INDEX, load_settings


def main() -> None:
    settings = load_settings()

    print(f"===========================================================")
    print(f"  INITIALIZING {APP_NAME} (v{APP_VERSION})")
    print(f"===========================================================")
    print("  • Vision Pipeline: MediaPipe Multi-Hand Graph (Dual-Hand Enabled)")
    print("  • Controller: Direct Win32 SendInput + Audio Worker Queue")
    print("  • Features: PiP Floating HUD, 2D Offline Track, Camera Hot-Swap")
    print(f"  • Active Camera Index: {settings.get('camera_index', CAMERA_INDEX)}")
    print("-----------------------------------------------------------")

    engine     = GestureEngine(camera_index=settings.get("camera_index", 0))
    controller = GameController(audio_feedback=settings.get("enable_audio_feedback", ENABLE_AUDIO_FEEDBACK))

    root = tk.Tk()
    app  = AppUI(root, engine, controller)

    try:
        root.mainloop()
    finally:
        print("\n[SHUTDOWN] Releasing controller keys, audio queue, and camera resources...")
        controller.stop()
        engine.release()
        print("[SHUTDOWN] Complete. Safe exit.")


if __name__ == "__main__":
    main()