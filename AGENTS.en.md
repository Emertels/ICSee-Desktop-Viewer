# 🤖 Technical Architecture & Agent Reference (AGENTS.en.md)

<p align="center">
  <a href="AGENTS.md">🇧🇷 Português</a> | <b>🇺🇸 English</b>
</p>

This document provides a technical specification of the **ICSee Desktop Viewer** codebase. It is designed for software engineers and autonomous AI agents maintaining, debugging, or extending the application.

---

## 1. System Overview

The application is an asynchronous, event-driven Windows desktop client built with **Python 3.12**, **PyQt6**, **OpenCV (cv2)**, **onvif-zeep**, **pygame-ce**, and **PyAudio**. It interfaces directly with Xiongmai / Sofia-based IP security cameras (specifically the dual-lens `XM535_X6E-WEQ_8M` hardware series), as well as generic ONVIF-compliant IP cameras.

```
+------------------------------------------------------------------------------------+
|                               PyQt6 Main GUI Thread                                |
|                                  (main_window.py)                                  |
|   +--------------------+  +----------------------+  +--------------------------+   |
|   | Automodulating Top |  | Settings & Tips Draw |  |   VideoWidget Canvas     |   |
|   | - Dynamic Buttons  |  | - IP / Port / User   |  | - Dual-Lens Slicer       |   |
|   | - SD / HD Switch   |  | - Password Toggle    |  | - Digital Zoom (Ctrl+Wh)|   |
|   | - ⯀ / ⚏ Layout     |  | - Limpar Cache / Dad |  | - Fail-Safe Toast (3s/5s)|   |
|   | - 📸 Snapshots     |  | - 10-Language i18n   |  | - Shutter Flash (90ms)   |   |
|   +--------------------+  +----------------------+  +--------------------------+   |
|                              |                      |  QScrollArea Right Panel |   |
|                              |                      |  - D-Pad + Red Pause btn |   |
|                              |                      |  - 🤖 Auto-Tracking      |   |
|                              |                      |  - 💡 Luz / LED Controls |   |
|                              |                      |  - 🔊 Ouvir / 🎙️ Falar   |   |
|                              |                      |  - 🎥 MP4 Video Recorder |   |
+------------------------------------------------------------------------------------+
           |                             |                             ^
           | (Fast PTZ & Tracking)       | (URL hot-swap)              | (QImage frames)
           v                             v                             |
+---------------------+        +--------------------+        +---------------------+
|    CameraManager    |        |    VideoWorker     |        |    GamepadWorker    |
| (camera_manager.py) |        |  (video_worker.py) |        |  (gamepad_worker.py)|
| - Sofia TCP :34567  |        | - RTSP Port 554    |        | - pygame-ce @ 25Hz  |
| - ONVIF Port 8899   |        | - cv2.VideoCapture |        | - DualSense / Xbox  |
| - Detect.DetectTrack|        | - Hot-swap URL     |        | - 8-way stick steer |
| - OPPTZControl ~60ms|        | - TCP transport    |        | - ptz_stop & action |
+---------------------+        +--------------------+        +---------------------+
           |
           +---------------------------+---------------------------+
           v                           v                           v
+---------------------+     +---------------------+     +---------------------+
|    VideoRecorder    |     | CameraAudioReceiver |     |  CameraAudioTalker  |
| (cv2.VideoWriter)   |     | (audio_manager.py)  |     | (audio_manager.py)  |
| - mp4v codec        |     | - Sofia Port 34567  |     | - Sofia Port 34567  |
| - Queue offloading  |     | - PyAudio output    |     | - Mic capture + AGC |
| - Background worker |     | - G.711A / PCM16    |     | - TALK_CU_PU_DATA   |
+---------------------+     +---------------------+     +---------------------+
```

---

## 2. Hardware Profile & Xiongmai Protocols

- **SoC:** Xiongmai XM535 (`XM535_X6E-WEQ_8M` or compatible Xiongmai/Sofia series).
- **Lens Architecture:** Dual-Sensor.
  - Sensor 1 (Upper): Motorized PTZ lens.
  - Sensor 2 (Lower): Fixed wide-angle panoramic lens.
- **Video Composition:** The camera encoder multiplexes both optical sensors into a single vertically stacked video raster:
  - **Sub-stream (SD):** `640 x 720` (each lens is `640 x 360`).
  - **Main-stream (HD):** `2304 x 2592` (each lens is `2304 x 1296`).

### 2.1 The Xiongmai RTSP Authentication Protocol
Standard ONVIF clients query the media service using `GetStreamUri`. However, when password authentication is activated in the ICSee mobile app under **Configurações Avançadas > NVR/IPC**:
1. The ONVIF service on port 8899 returns an unauthenticated URI path:
   `rtsp://<ip>:554/channel=0_stream=0&onvif=0.sdp?real_stream`
2. Attempting to connect via standard RTSP with HTTP Digest or Basic authentication headers results in a `401 Unauthorized` or socket reset from Xiongmai's firmware.
3. **The Solution:** Xiongmai firmware expects user credentials embedded inside the RTSP path parameters:
   ```text
   rtsp://<ip>:554/user=<user>_password=<pass>_channel=0_stream=<0|1>.sdp?real_stream
   ```
   - `stream=0`: Main-stream (HD Ultra).
   - `stream=1`: Sub-stream (SD Fluido).

### 2.2 Sofia NetSDK Protocol (Port 34567)
While video is streamed over RTSP (port 554), all control commands (PTZ, Human Tracking, Night Light, Two-way Audio) run over the binary Sofia NetSDK protocol on TCP port 34567:
- **Header:** 20 bytes beginning with `\xff\x00\x00\x00`.
- **Packet Structure:**
  - `0x00`: Magic Byte (`0xFF`)
  - `0x04`: Session ID (assigned during login `LOGIN_REQ 1000`)
  - `0x08`: Sequence Number
  - `0x0c`: Message ID (e.g., `1436` for PTZ, `1040` for Config Set)
  - `0x10`: Payload Length (little-endian uint32)
  - `0x14`: JSON Payload

### 2.3 Two-Way Audio Protocol (Talkback)
1. **Login & Session:** Establishes session on port 34567.
2. **Claim Channel:** `TALK_CLAIM` (`msg_id=1434`) claims the audio intercom channel.
3. **Request Talk:** `TALK_REQ` (`msg_id=1430`) initializes audio streaming.
4. **Data Transmission:** `TALK_CU_PU_DATA` (`msg_id=1432`):
   - 8-byte subheader: `\x00\x00\x01\xfa\x0e\x02@\x01`
   - G.711A (PCMA) encoded audio chunks (8000 Hz, 16-bit mono, 320-byte payload per 40ms frame).
   - Software digital gain (3.5x) with soft limiting ensures audibility even in loud outdoor environments.

---

## 3. Module Responsibilities

### 3.1 `camera_manager.py`
- Implements `SofiaClient` for high-speed TCP socket commands (~60ms latency).
- Implements `CameraManager` handling ONVIF discovery, profile tokens, PTZ controls, human tracking, and white-light floodlight toggling.
- Thread-safe command dispatch with automatic socket reconnect.

### 3.2 `video_worker.py`
- Encapsulates `cv2.VideoCapture` inside a dedicated `QThread`.
- Real-time frame decoding into `QImage` (Format_RGB888).
- URL hot-swapping without killing worker thread or leaking handles.

### 3.3 `audio_manager.py`
- `CameraAudioReceiver`: Captures real-time incoming audio from the camera speaker/mic.
- `CameraAudioTalker`: Records local PC microphone, converts to 8000Hz mono G.711A with 3.5x digital boost, and streams via Sofia NetSDK to the camera's external speaker.

### 3.4 `i18n.py`
- Multilingual engine with 10 native languages: `pt`, `en`, `es`, `fr`, `de`, `it`, `ja`, `zh`, `ru`, `ko`.
- Reactive listener pattern updating all UI components without restarting the application.

### 3.5 `gamepad_worker.py`
- Non-blocking `pygame-ce` event pump polling at 25Hz.
- Native support for Xbox 360/One/Series, PlayStation DualShock 4/DualSense, 8BitDo, and generic DirectInput/XInput controllers.
- Smooth analog PTZ joystick steering with deadzone thresholding (0.15).

### 3.6 `main_window.py`
- Main Qt GUI window orchestration.
- Canvas rendering in `VideoWidget` (paintEvent with QPainter, smooth scaling, crop modes, digital zoom).
- Toast notification system with failsafe auto-dismiss timer.
- Settings management, cache reset ("Limpar Dados / Cache"), and Windows startup integration.

---

## 4. Configuration Schema (`config.json`)

```json
{
  "ip": "192.168.1.10",
  "port": 8899,
  "user": "admin",
  "password": "",
  "quality": "sub",
  "layout_mode": "vertical",
  "speed": 0.5,
  "invert_x": true,
  "invert_y": false,
  "always_on_top": false,
  "start_with_windows": false,
  "start_minimized": false,
  "window_width": 960,
  "window_height": 560,
  "lang": "pt"
}
```

---

## 5. Security & Privacy Guidelines

- **Never commit `config.json`**: This file contains user-specific IP addresses, usernames, and passwords. It must remain in `.gitignore`.
- **Use `config.example.json`**: For onboarding and default schema validation.
- **Cache Clearing**: The GUI includes a dedicated "Limpar Dados / Cache" button which resets `config.json` to factory defaults, wipes passwords, and unregisters startup entries.
