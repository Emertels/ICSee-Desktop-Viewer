# 📷 ICSee Desktop Viewer

<p align="center">
  <a href="README.md">🇧🇷 Português</a> | <b>🇺🇸 English</b>
</p>

[![Release](https://img.shields.io/badge/Release-v1.0.0-blue.svg)](https://github.com/Emertels/ICSee-Desktop-Viewer/releases)
[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![GUI Framework](https://img.shields.io/badge/GUI-PyQt6-green.svg)](https://riverbankcomputing.com/software/pyqt/)
[![Streaming](https://img.shields.io/badge/Streaming-OpenCV%20%2F%20RTSP-orange.svg)](https://opencv.org/)
[![Recording](https://img.shields.io/badge/Recording-Universal%20MP4-red.svg)](https://en.wikipedia.org/wiki/MP4_file_format)
[![Gamepad Support](https://img.shields.io/badge/Gamepad-DualSense%20%7C%20Xbox-purple.svg)](https://github.com/pygame-community/pygame-ce)
[![i18n](https://img.shields.io/badge/i18n-10%20Languages-success.svg)](#-native-10-languages-support)
[![Portable Build](https://img.shields.io/badge/Build-Portable%20EXE-blueviolet.svg)](https://github.com/Emertels/ICSee-Desktop-Viewer/releases)
[![License](https://img.shields.io/badge/License-MIT-brightgreen.svg)](LICENSE)
[![OS](https://img.shields.io/badge/OS-Windows%2010%20%2F%2011-0078D6.svg)](https://www.microsoft.com/windows)

A modern, lightweight, high-performance, and fully portable desktop client for Windows designed to view, record, and control **ICSee / Xiongmai (XM535 / dual lens)** security cameras and generic **ONVIF** cameras in real-time, **without web browsers** and without obsolete NPAPI/ActiveX plugins.

---

## ✨ Key Features

- **🔍 Smart Auto-Discovery (WS-Discovery):** Automatic network scan using the **ONVIF WS-Discovery** standard and local subnet probe for instant detection of cameras with full names displayed without truncation.
- **⚡ Ultra-Low Latency Streaming:** Direct hardware decoding via **RTSP/FFmpeg** with instant hot-swapping between **Fluid SD (640x720)** and **Ultra HD (2304x2592)** streams.
- **🔊 Full Two-Way Audio (2-Way Intercom):**
  - **🔊 Listen Audio:** One-click to hear incoming audio captured by the camera's microphone in real time through PC speakers/headphones.
  - **🎙️ Talk to Camera (1-Click Continuous Intercom):** Click once to start hands-free continuous voice transmission from your PC microphone to the camera's external speaker (with 3.5x digital gain and soft limiting for outdoor clarity). Click again to stop—no holding down required!
- **🔎 Digital Zoom with `Ctrl` + Mouse Wheel:**
  - Smoothly zoom in up to **5.0x** at your cursor position using `Ctrl` + Mouse Scroll.
  - Pan and navigate freely by dragging with the left mouse button.
  - Double-click to instantly reset zoom back to 1.0x.
- **📐 Dual-Lens Intelligent Multi-View:**
  - **Normal Mode (Vertical):** Top lens (PTZ motorized) stacked over bottom lens (fixed panoramic).
  - **Side-by-Side Mode (Horizontal):** Both lenses rendered side-by-side in wide widescreen aspect ratio.
  - **Double Click / L2 & R2 Triggers:** Instantly expand either the top or bottom lens to full window with 2 quick clicks or gamepad triggers.
- **⏸️ Instant Video Pause & Resume:** Central D-Pad button (`⏸` / `▶`) or `Spacebar` with an elegant gold status overlay.
- **🎥 Universal MP4 Video Recorder with Auto PC Shutdown:**
  - Records directly to user's **Videos** folder with near-zero CPU overhead via background worker.
  - Duration selector: **Continuous (No limit)**, **15 min**, **30 min**, **1h**, **2h**, **4h**, **6h**, **8h**, **10h**, **12h**, and **24h**.
  - **Shut Down PC Option:** Automatically shuts down the computer with a 60s safety countdown when scheduled recording finishes.
- **🤖 Automatic Mode (Sofia AI Human Tracking):**
  - Low-latency asynchronous trigger via Sofia NetSDK protocol to detect and track persons in real time.
- **💡 Night Vision & Floodlight Illumination:**
  - **🌙 Night Mode:** Standard infrared night vision (black & white) with LED floodlights turned off.
  - **💡 Floodlight Mode:** Turns on powerful white LEDs to illuminate the area and record in full color in total darkness.
- **🔄 Remote Hardware Reboot:** One-click button to reboot the camera hardware over the network with scheduled auto-reconnect.
- **🎮 Native Gamepad & Controller Support:**
  - Full native support for **Sony PlayStation DualSense (PS5) / DualShock 4 (PS4)** and **Microsoft Xbox (Series, One, 360)**.
  - Smooth proportional analog camera rotation via left thumbstick.
- **🧹 Clear Cache / Data (Privacy & Factory Reset):**
  - Built-in button in Settings to purge saved passwords, camera IPs, and preferences with 1 click before sharing or moving PCs.
- **🌐 Native 10 Languages Support:**
  - Full multilingual UI available in **Portuguese (Brazil)**, **English**, **Spanish**, **French**, **German**, **Italian**, **Japanese**, **Simplified Chinese**, **Russian**, and **Korean**.
- **🪟 Start with Windows & Start Minimized:** Integrated Windows registry autostart support with option to launch directly to taskbar.
- **📦 100% Portable:** Can be bundled as an autonomous `.exe` that runs directly from USB drives without Python installed.

---

## 📹 Camera Compatibility

| Camera Type | Discovery / Scanning | Video Streaming | PTZ Pan/Tilt Controls | Advanced Features (Audio, LEDs, AI Tracking) |
| :--- | :---: | :---: | :---: | :---: |
| **ICSee / Xiongmai / XMeye (XM535 / Sofia)** | ✅ Automatic (WS-Discovery + Sofia) | ✅ RTSP SD & Ultra HD | ✅ Ultra-fast Sofia (~60ms) | ✅ 100% Supported (2-Way Audio, LEDs, Human Tracking) |
| **Generic ONVIF Cameras (Hikvision, Dahua, Intelbras, Tapo, etc.)** | ✅ Automatic (WS-Discovery) | ✅ Standard ONVIF RTSP | ✅ ONVIF ContinuousMove | ⚠️ Depends on manufacturer ONVIF profile support |

> **Note:** The camera scanner uses the open **ONVIF WS-Discovery** standard (multicast `239.255.255.250:3702`). Any ONVIF-compliant IP camera will be discovered and can stream video. Proprietary hardware controls (white LED floodlights, 2-way audio talkback, and Sofia AI human tracking) are designed specifically for Xiongmai/ICSee chipsets.

---

## 🎮 Controls & Shortcuts Reference

| Action | Keyboard | Mouse / GUI | Sony DualSense (PS5) | Microsoft Xbox |
| :--- | :---: | :---: | :---: | :---: |
| **Pan / Tilt (Rotate)** | `↑` `↓` `←` `→` | D-Pad buttons (`▲` `▼` `◀` `▶`) | Left Analog / D-Pad | Left Analog / D-Pad |
| **Pause / Resume Camera** | `Space` | Center D-Pad button (`⏸` / `▶`) | Circle (`○`) | `B` button |
| **Expand Top / Left Lens** | — | Double-click on top/left lens | `L2` Trigger | `LT` Trigger |
| **Expand Bottom / Right Lens** | — | Double-click on bottom/right lens | `R2` Trigger | `RT` Trigger |
| **Digital Zoom at Cursor** | `Ctrl` + Scroll | `Ctrl` + Mouse Wheel (up to 5.0x) | — | — |
| **Pan / Navigate Zoomed View** | — | Click and drag with left mouse | — | — |
| **Reset Zoom to 1.0x** | — | Double-click on zoomed video | — | — |
| **Restore Both Lenses** | — | Double-click on unzoomed video | `L2` or `R2` | `LT` or `RT` |
| **Quick Rotation Turn** | — | `↶ Left` / `Right ↷` buttons | — | — |
| **Record Video (MP4)** | `R` | `🔴 Start` / `⏹️ Stop` button | — | — |
| **Snapshot (Photo)** | `S` | `📸 Photo` button | Triangle (`△`) | `Y` button |
| **Switch View (Normal / Side-by-Side)** | — | `⯀ Normal` / `⚏ Side-by-Side` | Square (`□`) | `X` button |
| **Fluid SD Quality (640x720)** | — | `⚡ SD` button | `L1` button | `LB` button |
| **Ultra HD Quality (2304x2592)** | — | `🌟 HD` button | `R1` button | `RB` button |
| **Open Tips Panel** | — | `🎮 Tips` button | — | — |
| **Always on Top** | `T` | `📌 Pin` button | — | — |
| **Full Screen** | `F11` | Covers Windows taskbar | — | — |

---

## 🚀 Installation and Execution

### Option 1: Standalone Portable Version (Recommended for End Users)
1. Download the release package (`ICSee_Viewer_v1.0.0_Portable.zip`) from [Releases](https://github.com/Emertels/ICSee-Desktop-Viewer/releases).
2. Extract and launch `ICSee_Viewer.exe`.
3. Ready! Does not require Python or any external dependencies installed.

### Option 2: Running from Source (Developers)

#### Prerequisites
- **Windows 10 or 11 (64-bit)**
- **Python 3.10+**

#### Steps
```bash
# 1. Clone repository
git clone https://github.com/Emertels/ICSee-Desktop-Viewer.git
cd ICSee-Desktop-Viewer

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch application
python app.py
```

### Building the Portable Package (.exe)
To compile your own standalone portable build:
```bash
python build_exe.py
```
The output directory will be created at `dist/ICSee_Viewer/`.

---

## ⚙️ Configuration & Privacy

1. Click the **⚙️** icon at the top right to open settings.
2. Enter connection parameters:
   - **IP:** Camera IP address (e.g. `192.168.1.100`).
   - **Port:** Default `8899`.
   - **User:** Username (factory default: `admin`).
   - **Password:** Password configured on the camera (use `👁️` to reveal).
   - **Language:** Select from 10 available languages.
3. Click **💾 Save and Connect**.
4. **To Wipe Saved Data:** Use the **🧹 Clear Cache / Data** button to instantly restore clean defaults and purge stored passwords and IPs.

---

## 📁 Repository Structure

```text
ICSee-Desktop-Viewer/
├── app.py                  # Application entry point
├── main_window.py          # PyQt6 main GUI window, layouts, recording, canvas
├── camera_manager.py       # ONVIF/Sofia connection manager & RTSP builder
├── audio_manager.py        # Two-way intercom audio receiver & talker
├── i18n.py                 # Multilingual engine supporting 10 languages
├── video_worker.py         # Dedicated OpenCV low-latency decoding thread
├── gamepad_worker.py       # DualSense & Xbox controller driver (pygame-ce)
├── build_exe.py            # Automated portable PyInstaller build script
├── config.example.json     # Clean default configuration template
├── Iniciar_Camera.bat      # Silent Windows launcher
├── Iniciar_Com_Console.bat # Debug console launcher
├── requirements.txt        # Python dependencies
├── LICENSE                 # MIT Open Source License
├── README.md               # Portuguese presentation & guide
├── README.en.md            # English presentation & guide
├── MANUAL.md               # Detailed user manual (Portuguese)
├── MANUAL.en.md            # Detailed user manual (English)
├── AGENTS.md               # Developer & AI architecture specification (Portuguese)
└── AGENTS.en.md            # Developer & AI architecture specification (English)
```

---

## 📄 License

Distributed under the **MIT** License. See [LICENSE](LICENSE) for details.

---

## 👨‍💻 About the Author

Developed and maintained by **Emerson Teles** (known across developer and gaming communities as **Emertels**).

Tech enthusiast, gamer, systems maintenance specialist, and software translator/localizer for Brazilian Portuguese (PT-BR). Developer focused on practical system utilities, gaming tools, intelligent automation, and complete localization solutions that bring modern software to Portuguese-speaking audiences.

### 🛠️ Projects & Contributions

- [AI-Chat-Vault](https://github.com/Emertels/AI-Chat-Vault) — Portable backup and precision recovery for local chats across 20+ agentic AI assistants.
- [Antigravity — Brazilian Portuguese Translation](https://github.com/Emertels/Antigravity-Traducao-PTBR) — Complete Portuguese localization of Google Antigravity Desktop.
- [Codex Router — Brazilian Portuguese Translation](https://github.com/Emertels/CodexRouter-Traducao-PTBR) — Complete translation and localization of Codex Router Control Center.
- [Cursor AI — Brazilian Portuguese Translation](https://github.com/Emertels/Cursor-Traducao-PTBR) — Deep and comprehensive localization of Cursor AI for Brazilian Portuguese.
- [Devin AI — Brazilian Portuguese Translation](https://github.com/Emertels/Devin-Traducao-PTBR) — Complete localization of Devin AI Desktop for Brazilian Portuguese.
- [GPU Tweak III — Brazilian Portuguese Translation](https://github.com/Emertels/GPU-Tweak-III-Traducao-PTBR) — Brazilian Portuguese localization and automated installer for ASUS GPU Tweak III.
- [ICSee Desktop Viewer](https://github.com/Emertels/ICSee-Desktop-Viewer) — Modern and portable desktop application for viewing and controlling ICSee and ONVIF cameras on Windows.
- [Microsoft Photos Fix](https://github.com/Emertels/Microsoft-Photos-Fix) — Advanced PowerShell & C# fix restoring fast launch routes and wallpaper setting for Windows Photos app.
- [PSBBN-Translator](https://github.com/Emertels/PSBBN-Translator) — Multilingual localization suite for the PSBBN Definitive Project (PlayStation 2) across 40 languages.
- [Silent Hill: Homecoming — Brazilian Portuguese Translation](https://github.com/Emertels/Silent-Hill-Homecoming-Traducao-PTBR) — Complete translation and canonical revision for the PC version.
- [Suite-Emuladores](https://github.com/Emertels/Suite-Emuladores) — Autonomous PowerShell automation suite for downloading and updating 56 gaming emulators and frontends on Windows.
- [Xbox 360 Controller Calibration Tool](https://github.com/Emertels/Xbox-360-Controller-Calibration-Tool) — Open-source professional calibration software for Xbox 360 controllers on Windows.
- [ZCode — Brazilian Portuguese Translation](https://github.com/Emertels/ZCode-Traducao-PTBR) — Full Brazilian Portuguese localization for ZCode Desktop.

### 🌐 Connect with me & Official Communities

<div align="left">

[![GitHub](https://img.shields.io/badge/GitHub-Emertels-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/emertels)
[![Website](https://img.shields.io/badge/Website-Emerson_Teles-0070F3?style=for-the-badge&logo=googlechrome&logoColor=white)](https://emertels.github.io)
[![Discord](https://img.shields.io/badge/Discord-Emertels%20Server-5865F2?style=for-the-badge&logo=discord&logoColor=white)](https://emertels.github.io/discord)
[![X / Twitter](https://img.shields.io/badge/X_Twitter-@emertels-000000?style=for-the-badge&logo=x&logoColor=white)](https://x.com/emertels)
[![YouTube](https://img.shields.io/badge/YouTube-Emerson_Teles-FF0000?style=for-the-badge&logo=youtube&logoColor=white)](https://www.youtube.com/@emersonteles2379)
[![Telegram](https://img.shields.io/badge/Telegram-Aplicativos%20Mods-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/apksmodsandroid)
[![Ko-fi](https://img.shields.io/badge/Ko--fi-Apoiar%20Projeto-FF5E5B?style=for-the-badge&logo=kofi&logoColor=white)](https://ko-fi.com/emertels)

</div>

