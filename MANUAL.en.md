# 📖 User Manual - ICSee Desktop Viewer

<p align="center">
  <a href="MANUAL.md">🇧🇷 Português</a> | <b>🇺🇸 English</b>
</p>

Comprehensive user guide and reference manual for the **ICSee Desktop Viewer** for Xiongmai / ICSee dual-lens security cameras.

---

## 📑 Table of Contents
1. [System Overview](#1-system-overview)
2. [Prerequisites & Portable Execution](#2-prerequisites--portable-execution)
3. [How to Launch the Application](#3-how-to-launch-the-application)
4. [Network, User & Password Configuration](#4-network-user--password-configuration)
5. [Dual-Lens View Modes](#5-dual-lens-view-modes)
6. [Digital Zoom & Navigation](#6-digital-zoom--navigation)
7. [Resolution & Image Quality (SD vs HD)](#7-resolution--image-quality-sd-vs-hd)
8. [Two-Way Audio Intercom (Listen & Speak)](#8-two-way-audio-intercom-listen--speak)
9. [Camera Pan/Tilt Control (PTZ)](#9-camera-pantilt-control-ptz)
10. [Gamepad & Controller Support (DualSense & Xbox)](#10-gamepad--controller-support-dualsense--xbox)
11. [Universal MP4 Video Recording](#11-universal-mp4-video-recording)
12. [Night Vision & LED Floodlight Modes](#12-night-vision--led-floodlight-modes)
13. [Automatic Human Tracking Mode](#13-automatic-human-tracking-mode)
14. [Instant Snapshots](#14-instant-snapshots)
15. [Clear Cache & Data (Factory Reset)](#15-clear-cache--data-factory-reset)
16. [Frequently Asked Questions & Troubleshooting](#16-frequently-asked-questions--troubleshooting)

---

## 1. System Overview

The **ICSee Desktop Viewer** is a high-performance Windows client designed for viewing, recording, and controlling IP security cameras using Xiongmai / ICSee technology. Instead of running clunky web browser plugins or obsolete ActiveX controls, it communicates directly using standard low-latency protocols:
- **ONVIF (Port 8899):** Camera discovery, media profiles, and motorized PTZ steering.
- **RTSP (Port 554):** Real-time hardware-decoded video streaming.
- **Sofia NetSDK (Port 34567):** Ultra-fast ~60ms command dispatch, human tracking, LED lighting, and two-way voice intercom.

The client is optimized for dual-sensor cameras (such as the `XM535_X6E-WEQ_8M`), multiplexing the upper motorized PTZ lens and lower wide-angle lens seamlessly.

---

## 2. Prerequisites & Portable Execution

### System Requirements
- **Operating System:** Windows 10 or Windows 11 (64-bit).
- **Network:** PC and camera must be connected to the same local network (Ethernet or Wi-Fi).

### Portable Standalone Version (No Python required)
1. Download the release archive `ICSee_Viewer_v1.0.0_Portable.zip`.
2. Extract the folder to any drive or USB flash drive.
3. Double-click `ICSee_Viewer.exe`.

### Running from Source Code (Python Developers)
- Requires Python 3.10 or higher.
- Install requirements via `pip install -r requirements.txt`.
- Launch with `python app.py`.

---

## 3. How to Launch the Application

1. **Portable Executable:** Double-click `ICSee_Viewer.exe`.
2. **Silent Background Script:** Double-click `Iniciar_Camera.bat`.
3. **Debug Console Mode:** Double-click `Iniciar_Com_Console.bat` or run `python app.py` in terminal.

---

## 4. Network, User & Password Configuration

### Factory Default Credentials
- **Username:** `admin`
- **Password:** *(blank / empty)*

### Setting Up Password-Protected Cameras
If you set a password in the ICSee mobile app (**Advanced Settings > NVR/IPC > Password**):
1. Click the **⚙️** (Settings) icon at the top right.
2. Enter the parameters:
   - **IP:** Camera local IP (e.g., `192.168.1.100`).
   - **Port:** `8899`.
   - **User:** Username (e.g., `admin`).
   - **Password:** Enter your camera password (use the `👁️` toggle to verify).
   - **Language:** Select your preferred language (10 native languages supported).
3. Click **💾 Save and Connect**.

---

## 5. Dual-Lens View Modes

- **Normal Mode (Vertical `⯀`):** Displays both lenses stacked vertically (PTZ camera on top, panoramic camera on bottom).
- **Side-by-Side Mode (`⚏`):** Displays both lenses horizontally in wide panoramic view.
- **Full View on Single Lens:** Double-click the top/left lens to expand it to the entire window; double-click the bottom/right lens to expand it; double-click again to return to dual-lens view.

---

## 6. Digital Zoom & Navigation

- **Zoom In / Out:** Hold `Ctrl` and scroll the **Mouse Wheel** to zoom up to **5.0x** centered at your cursor.
- **Pan / Move:** Click and drag with the left mouse button to inspect any portion of the frame.
- **Reset Zoom:** Double-click anywhere on the zoomed video to return to 1.0x view.

---

## 7. Resolution & Image Quality (SD vs HD)

- **⚡ SD (Fluid):** `640x720` resolution (~15 FPS). Instantaneous low-latency response with minimal bandwidth consumption. Shortcut: `L1` / `LB`.
- **🌟 HD (Ultra):** `2304x2592` resolution (8MP Ultra). Maximum crispness for identifying license plates, faces, and fine details. Shortcut: `R1` / `RB`.

---

## 8. Two-Way Audio Intercom (Listen & Speak)

- **🔊 Listen Audio:** Click once to start listening to the camera's built-in microphone through PC speakers. Click again to mute.
- **🎙️ Talk to Camera:** Click once to start hands-free continuous voice transmission from your PC microphone to the camera's external speaker. A digital 3.5x gain ensures clear audibility outdoors. Click again to stop.

---

## 9. Camera Pan/Tilt Control (PTZ)

- **On-Screen D-Pad:** Click `▲`, `▼`, `◀`, `▶` to rotate the motorized lens.
- **Keyboard Arrows:** Use `↑`, `↓`, `←`, `→` keys for smooth navigation.
- **Quick Turn:** Click `↶ Left` or `Right ↷` for calibrated 45-degree rotational steps.
- **Invert Horizontal:** Option in Settings to align left/right rotation with your physical point of view.

---

## 10. Gamepad & Controller Support (DualSense & Xbox)

Full native plug-and-play support for **PS5 DualSense**, **PS4 DualShock 4**, and **Xbox Series/One/360** controllers:
- **Left Thumbstick:** Smooth proportional 360-degree analog PTZ movement.
- **Circle (`○`) / `B`:** Pause / Resume video.
- **`L2` / `LT`:** Expand top/left lens.
- **`R2` / `RT`:** Expand bottom/right lens.
- **Triangle (`△`) / `Y`:** Take instant snapshot.
- **Square (`□`) / `X`:** Switch Normal / Side-by-Side layout.
- **`L1` / `LB`:** Switch to SD Fluid stream.
- **`R1` / `RB`:** Switch to HD Ultra stream.

---

## 11. Universal MP4 Video Recording

- Records directly to user's **Videos** folder (`Videos\ICSee_Gravacao_*.mp4`).
- Supports scheduled duration presets: **Continuous**, **15m**, **30m**, **1h**, **2h**, **4h**, **6h**, **8h**, **10h**, **12h**, and **24h**.
- **Auto PC Shutdown:** Optional checkbox to shut down the computer automatically when recording completes (with a 60s abort prompt).

---

## 12. Night Vision & LED Floodlight Modes

- **🌙 Night Mode:** Standard infrared night vision (monochrome) with floodlights switched off.
- **💡 Floodlight Mode:** Turns on high-intensity white LEDs for crisp full-color night surveillance.

---

## 13. Automatic Human Tracking Mode

Click **🤖 Human Tracking** to toggle the camera's embedded Sofia AI motion tracker. The camera will automatically swivel to follow persons moving across its field of view.

---

## 14. Instant Snapshots

Click **📸 Photo** or press `S` (or `△` / `Y` on controller) to capture an uncompressed snapshot directly to your **Pictures** directory (`Pictures\ICSee_Snapshot_*.png`).

---

## 15. Clear Cache & Data (Factory Reset)

To remove all private information:
1. Open the **⚙️** (Settings) drawer.
2. Click **🧹 Clear Cache / Data**.
3. Confirm the prompt: the application deletes `config.json`, wipes stored IP addresses and passwords, unregisters Windows autostart, and restores clean factory defaults.

---

## 16. Frequently Asked Questions & Troubleshooting

### 1. Does it only detect ICSee cameras?
- The built-in scanner uses the open **ONVIF WS-Discovery** standard (multicast `239.255.255.250:3702`). Any ONVIF-compliant camera (Intelbras, Hikvision, Dahua, Tapo) will be detected and stream video. Proprietary features (white LEDs, 2-way audio, and Sofia human tracking) are Xiongmai/ICSee specific.

### 2. Video is black or says "Authentication Failed"?
- Open **⚙️**, use the `👁️` button to check password case sensitivity, then click **💾 Save and Connect**.

### 3. Where are my recordings and snapshots saved?
- **Photos:** `C:\Users\<YourUser>\Pictures\`
- **Videos:** `C:\Users\<YourUser>\Videos\`
