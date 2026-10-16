# Gesture / Racing — Windows controller

[![Python 3.12](https://img.shields.io/badge/python-3.12-3776AB.svg)](https://www.python.org/downloads/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.x-green.svg)](https://opencv.org/)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10.11-orange.svg)](https://developers.google.com/mediapipe)
[![PyAutoGUI](https://img.shields.io/badge/PyAutoGUI-Active-purple.svg)](https://pyautogui.readthedocs.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Windows desktop app that tracks hand poses from a webcam and maps gestures to keyboard or mouse input for the focused game. Camera frames are processed locally.

Designed for web & desktop racing games, endless runners, and arcade titles (e.g., *Hill Climb Racing*, *Moto X3M*, *Temple Run 2*, *Subway Surfers*, *Drift Boss*, *Road Fury*).

---

## Features

* **Dual-hand steering:** Use both hands to calculate a steering angle from wrist positions.
* **Adaptive smoothing and hysteresis:** Smooths movement and filters small angle changes to reduce unintended steering.
* **Built-in 2D Offline Racetrack:** Embedded interactive 2D physics racing simulator directly inside the dashboard to test steering and throttle with lap timing without needing an internet connection.
* **Picture-in-Picture (PiP) Floating Mini-HUD:** 1-click toggle collapses the dashboard into a sleek, floating, always-on-top compact widget that sits cleanly alongside any full-screen game.
* **Live Camera Device Hot-Swapping:** Scan and switch between connected webcams (built-in, USB HD cams, OBS Virtual Cam) dynamically without restarting the application.
* **Air-Mouse & Cursor Emulation:** Move your OS mouse cursor with index finger tracking and click/drag using pinch gestures.
* **Dedicated Audio Queue Worker:** Non-blocking background sound dispatcher with on/off toggle.
* **Win32 Window Focus:** Activates the selected game window through the Windows API.
* **Persistent Settings (`settings.json`):** Remembers custom calibration angles, sensitivity deadzones, camera indices, audio preferences, and custom games.
* **Dynamic Custom Game Creator:** Add and customize game profiles, URLs, and keybindings via the UI.

---

## 🏗️ System Architecture & Data Flow

```
+--------------------+      +-----------------------+      +---------------------------+
| Multi-Cam Capture  | ---> | Image Preprocessing   | ---> | MediaPipe Multi-Hand Graph|
| (cv2.VideoCapture) |      | (cv2.flip, BGR2RGB)   |      | (21-Landmark Dual-Hand)   |
+--------------------+      +-----------------------+      +---------------------------+
                                                                         |
                                                                         v
+--------------------+      +-----------------------+      +---------------------------+
| Target Game / App  | <--- | Input Dispatcher | <--- | Multi-Feature Engine      |
| (Browser, Offline  |      | (Win32 SendInput +    |      | (Dual-Hand Slope, atan2,  |
|  2D Track, Steam)  |      |  PyAutoGUI & AirMouse)|      |  Adaptive Smoothing, PWM)|
+--------------------+      +-----------------------+      +---------------------------+
```

---

## 📐 Mathematical Formulation

### 1. Single-Hand Orientation Angle ($\theta$)
Measured between the **Wrist** ($P_0 = (x_1, y_1)$) and target fingertip $P_t = (x_2, y_2)$:

$$\Delta x = x_2 - x_1$$
$$\Delta y_{\text{inverted}} = y_1 - y_2 \quad (\text{compensates for top-left image origin})$$
$$\theta_{\text{raw}} = \left(\text{atan2}(\Delta y_{\text{inverted}}, \Delta x) \times \frac{180}{\pi} + 360\right) \pmod{360}$$

### 2. Dual-Hand Steering Wheel Slope
Computed between **Left Wrist** $(x_L, y_L)$ and **Right Wrist** $(x_R, y_R)$:

$$\Delta x_{\text{wheel}} = x_R - x_L, \quad \Delta y_{\text{wheel}} = y_L - y_R$$
$$\theta_{\text{wheel}} = \left(90^\circ + 1.8 \times \text{atan2}(\Delta y_{\text{wheel}}, \Delta x_{\text{wheel}}) \times \frac{180}{\pi}\right) \pmod{360}$$

### 3. Adaptive Dynamic Velocity Smoothing
$$\alpha = \alpha_{\text{min}} + \min\left(\frac{|\Delta\theta|}{45^\circ}, 1.0\right) \times (\alpha_{\text{max}} - \alpha_{\text{min}})$$
$$\theta_{t} = (\theta_{t-1} + \alpha \cdot \Delta\theta) \pmod{360}$$

---

## 📁 Repository Structure

| File | Description |
| :--- | :--- |
| [`main.py`](main.py) | Application entry point with persistent settings initialization. |
| [`gesture_engine.py`](gesture_engine.py) | OpenCV multi-cam handler, dual-hand tracking, adaptive smoothing, and HUD renderer. |
| [`game_controller.py`](game_controller.py) | Win32 SendInput controller with dedicated audio worker & air mouse. |
| [`ui.py`](ui.py) | Tkinter dashboard with PiP floating mode, embedded 2D offline track, and animated telemetry. |
| [`games.py`](games.py) | Dynamic game catalog, persistent custom games, and control blueprints. |
| [`config.py`](config.py) | Central configuration and `settings.json` manager. |
| [`test_system.py`](test_system.py) | Automated test suite verifying single & dual-hand trigonometry and state transitions. |
| [`build.bat`](build.bat) | One-click PyInstaller build script for standalone Windows executable. |
| [`LICENSE`](LICENSE) | Official MIT License. |
| [`requirements.txt`](requirements.txt) | Python package dependencies. |

---

## 🚀 Quick Start Guide

### Verified Windows baseline (Python 3.12)

The project uses a local environment at `gesture_racing_controller\.venv`. From PowerShell in the inner `gesture_racing_controller` folder:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m unittest -v test_system.py
```

Then double-click the top-level `run.bat`, or run it from PowerShell:

```powershell
..\run.bat
```

`run.bat` uses `.venv\Scripts\python.exe` directly, starts `main.py`, and leaves a useful error visible if startup fails.

If no webcam is available, the source selector clearly shows **Simulation** and the offline track opens automatically. Use Left/Right/Up/Down or A/D/W/S for left, right, accelerate, and brake. Releasing the key returns to straight/neutral. Escape or the red Stop button is the emergency stop; closing the window releases all held keyboard/mouse inputs and the camera.

For a real webcam, choose `Camera N` in the source selector. Camera gesture behavior requires physical confirmation on the target machine.

### 1. Installation
```bash
git clone https://github.com/your-username/gesture-racing-controller.git
cd gesture-racing-controller
pip install -r requirements.txt
```

### 2. Run the Application
```bash
python main.py
```

### 3. Build Standalone Executable (.exe)
Double-click `build.bat` or run:
```bash
build.bat
```

---

## 📜 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
