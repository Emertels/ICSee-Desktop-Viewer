"""
Modern, lightweight desktop GUI for ICSee cameras using PyQt6.
Features:
- Live dual-lens video stream with low latency
- Real-time PTZ control (buttons, keyboard arrows, and Gamepad / DualSense / Xbox controller!)
- Native Windows Immersive Dark Titlebar (No white bar!)
- Fully responsive, automodulating top bar (no overlapping on compression)
- Default startup size: 960 x 560 (with geometry memory)
- Instant 1-Click snapshot: saves directly to Pictures in 1 click with 2-second real-time toast
- Dark theme styled QComboBox with clean borderless drop-down and full tooltips
- Show/Hide password toggle button (👁️ / 🔒)
- Dual-Lens View Modes: [ ⯀ Normal ] vs [ ⚏ Lado a Lado ]
- Dedicated [ ⚡ SD ] and [ 🌟 HD ] quality selector with live resolution badge
"""

import sys
import os
import json
import time
import queue
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

from PyQt6.QtCore import Qt, QTimer, QSize, QPoint, QRect, pyqtSlot, QThread, pyqtSignal, QPointF
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QLineEdit, QSlider, QFrame,
    QCheckBox, QMessageBox, QListView, QSizePolicy, QScrollArea, QToolTip
)
from PyQt6.QtGui import QImage, QPixmap, QColor, QFont, QIcon, QKeyEvent, QPainter, QWheelEvent, QShortcut, QKeySequence

from camera_manager import CameraManager
from video_worker import VideoWorker
from gamepad_worker import GamepadWorker
from audio_manager import CameraAudioReceiver, CameraTalkWorker
from PyQt6.QtMultimedia import QMediaDevices
from i18n import tr, set_language, get_language, LANGUAGES, register_listener

if getattr(sys, "frozen", False):
    APP_DIR = Path(sys.executable).parent
else:
    APP_DIR = Path(__file__).parent

CONFIG_FILE = APP_DIR / "config.json"

DEFAULT_CONFIG = {
    "ip": "192.168.1.10",
    "port": 8899,
    "user": "admin",
    "password": "",
    "quality": "sub",
    "layout_mode": "vertical",
    "speed": 0.5,
    "invert_x": True,
    "invert_y": False,
    "always_on_top": False,
    "start_with_windows": False,
    "start_minimized": False,
    "window_width": 960,
    "window_height": 560,
    "lang": "pt"
}

def set_windows_autostart(enable: bool, minimized: bool = False):
    """Enables or disables automatic launch on Windows startup via HKCU Run registry key."""
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE
        )
        val_name = "ICSeeViewer"
        if enable:
            if getattr(sys, "frozen", False):
                cmd = f'"{sys.executable}"' + (" --minimized" if minimized else "")
            else:
                py_exe = sys.executable
                if "python.exe" in py_exe.lower():
                    pyw = py_exe.lower().replace("python.exe", "pythonw.exe")
                    if Path(pyw).exists():
                        py_exe = pyw
                app_path = str(APP_DIR / "app.py")
                cmd = f'"{py_exe}" "{app_path}"' + (" --minimized" if minimized else "")
            winreg.SetValueEx(key, val_name, 0, winreg.REG_SZ, cmd)
        else:
            try:
                winreg.DeleteValue(key, val_name)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
    except Exception as e:
        print(f"[Autostart] Registry update error: {e}")

def apply_windows_dark_titlebar(window: QMainWindow):
    """Enables Windows 10/11 DWM Immersive Dark Titlebar and custom caption color."""
    try:
        import ctypes
        hwnd = int(window.winId())
        for attr in (20, 19):
            val = ctypes.c_int(1)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, attr, ctypes.byref(val), ctypes.sizeof(val)
            )
        color = ctypes.c_int(0x003b291e)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, 35, ctypes.byref(color), ctypes.sizeof(color)
        )
        text_color = ctypes.c_int(0x00fcfaf8)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, 36, ctypes.byref(text_color), ctypes.sizeof(text_color)
        )
    except Exception:
        pass


class VideoRecorder(QThread):
    """Background MP4 video recorder thread using cv2.VideoWriter with direct BGR frames."""
    progress_updated = pyqtSignal(int, int) # elapsed_sec, max_duration_sec
    recording_finished = pyqtSignal(str, int) # filepath, elapsed_sec
    recording_error = pyqtSignal(str)

    def __init__(self, filepath: str, width: int, height: int, fps: float = 20.0, max_duration_sec: int = 0):
        super().__init__()
        self.filepath = filepath
        self.width = width
        self.height = height
        self.fps = max(10.0, fps)
        self.max_duration_sec = max_duration_sec
        self.frame_queue = queue.Queue(maxsize=150)
        self._running = False
        self._paused = False
        self.elapsed_sec = 0

    def add_frame(self, bgr_frame: np.ndarray):
        if self._running and not self._paused:
            if not self.frame_queue.full():
                self.frame_queue.put(bgr_frame)

    def set_paused(self, paused: bool):
        self._paused = paused

    def stop_recording(self):
        self._running = False

    def run(self):
        self._running = True
        try:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(self.filepath, fourcc, self.fps, (self.width, self.height))
            if not out.isOpened():
                self.recording_error.emit("Erro ao inicializar o arquivo de vídeo MP4.")
                return

            start_time = time.time()
            last_tick = time.time()
            total_paused_time = 0.0
            pause_start = 0.0

            while self._running:
                if self._paused:
                    if pause_start == 0.0:
                        pause_start = time.time()
                    time.sleep(0.05)
                    continue
                else:
                    if pause_start > 0.0:
                        total_paused_time += (time.time() - pause_start)
                        pause_start = 0.0

                try:
                    frame = self.frame_queue.get(timeout=0.08)
                    if isinstance(frame, np.ndarray):
                        if frame.shape[1] == self.width and frame.shape[0] == self.height:
                            out.write(frame)
                        else:
                            out.write(cv2.resize(frame, (self.width, self.height)))
                except queue.Empty:
                    pass

                now = time.time()
                self.elapsed_sec = int((now - start_time) - total_paused_time)
                if now - last_tick >= 1.0:
                    last_tick = now
                    self.progress_updated.emit(self.elapsed_sec, self.max_duration_sec)

                if self.max_duration_sec > 0 and self.elapsed_sec >= self.max_duration_sec:
                    break

            # Flush remaining frames cleanly
            while not self.frame_queue.empty():
                try:
                    frame = self.frame_queue.get_nowait()
                    if isinstance(frame, np.ndarray):
                        if frame.shape[1] == self.width and frame.shape[0] == self.height:
                            out.write(frame)
                        else:
                            out.write(cv2.resize(frame, (self.width, self.height)))
                except Exception:
                    break

            out.release()
            self.recording_finished.emit(self.filepath, self.elapsed_sec)
        except Exception as e:
            self.recording_error.emit(str(e))


class VideoWidget(QWidget):
    """Custom video canvas widget supporting Normal (Vertical), Side-by-Side, and Single-Lens Zoom modes."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 240)
        self.raw_pixmap: Optional[QPixmap] = None
        self.display_pixmap: Optional[QPixmap] = None
        self.layout_mode = "vertical"
        self.single_lens: Optional[str] = None # None, "top", or "bottom"
        self.status_text = "Carregando câmera..."
        self.fps_text = ""
        self.res_text = ""
        self.is_hd = False
        self.is_switching = False
        self.is_flashing = False
        self.is_paused = False
        self.is_recording = False
        self.is_auto_tracking = False
        self.rec_time_text = ""

        # Digital Zoom within expanded single lens view (Ctrl + Mouse Wheel directed at cursor position)
        self.zoom_level: float = 1.0
        self.zoom_vx: float = 0.0
        self.zoom_vy: float = 0.0
        self.drag_start_pos = None
        self.drag_start_vx: float = 0.0
        self.drag_start_vy: float = 0.0
        self.setMouseTracking(True)

        # Toast notification system with fail-safe expiration timestamp (3 seconds default)
        self.toast_text = ""
        self.toast_expires_at = 0.0
        self.toast_timer = QTimer(self)
        self.toast_timer.setSingleShot(True)
        self.toast_timer.timeout.connect(self.clear_toast)

        # Periodic cleanup timer ensuring pop-ups never get stuck on screen
        self.cleanup_timer = QTimer(self)
        self.cleanup_timer.setInterval(200)
        self.cleanup_timer.timeout.connect(self._check_toast_expiry)
        self.cleanup_timer.start()

        self.setStyleSheet("background-color: #090d16;")

    def set_layout_mode(self, mode: str):
        self.layout_mode = mode
        self.single_lens = None # reset zoom on layout mode change
        self.zoom_level = 1.0
        self.zoom_vx = 0.0
        self.zoom_vy = 0.0
        self.drag_start_pos = None
        self.setCursor(Qt.CursorShape.ArrowCursor)
        if self.raw_pixmap and not self.raw_pixmap.isNull():
            self._update_display_pixmap()
            self.update()

    def toggle_single_lens(self, lens: str):
        """Expands chosen lens to fill the video canvas or toggles back to dual-lens view."""
        self.zoom_level = 1.0
        self.zoom_vx = 0.0
        self.zoom_vy = 0.0
        self.drag_start_pos = None
        self.setCursor(Qt.CursorShape.ArrowCursor)

        if self.single_lens == lens:
            self.single_lens = None
            self._update_display_pixmap()
            self.update()
            self.show_toast("🔄 Visão restaurada para as duas lentes!", duration_ms=3000)
        else:
            self.single_lens = lens
            self._update_display_pixmap()
            self.update()
            name = "Superior / Esquerda (PTZ)" if lens == "top" else "Inferior / Direita (Fixa)"
            shortcut = "L2" if lens == "top" else "R2"
            self.show_toast(f"🔍 Lente {name} ampliada no vídeo!\n(Ctrl + Scroll p/ zoom no cursor • Arraste p/ mover • {shortcut}/2 cliques p/ voltar)", duration_ms=3000)

    def wheelEvent(self, event: QWheelEvent):
        """Ctrl + Mouse Wheel zooms in/out centered precisely at the cursor location."""
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if not self.display_pixmap or self.display_pixmap.isNull():
                return super().wheelEvent(event)

            # Auto-expand into single lens if user uses Ctrl+Scroll in dual-camera view
            if self.single_lens is None:
                scaled = self.display_pixmap.scaled(
                    self.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                vx = (self.width() - scaled.width()) // 2
                vy = (self.height() - scaled.height()) // 2
                pos = event.position()
                mx = pos.x() - vx
                my = pos.y() - vy
                if scaled.width() > 0 and scaled.height() > 0 and 0 <= mx < scaled.width() and 0 <= my < scaled.height():
                    if self.layout_mode == "side_by_side":
                        target_lens = "top" if (mx / scaled.width() < 0.5) else "bottom"
                    else:
                        target_lens = "top" if (my / scaled.height() < 0.5) else "bottom"
                    self.toggle_single_lens(target_lens)

            scaled = self.display_pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            vx = (self.width() - scaled.width()) // 2
            vy = (self.height() - scaled.height()) // 2

            pos = event.position()
            mx = pos.x() - vx
            my = pos.y() - vy

            if scaled.width() > 0 and scaled.height() > 0 and 0 <= mx <= scaled.width() and 0 <= my <= scaled.height():
                px = mx / scaled.width()
                py = my / scaled.height()
            else:
                px, py = 0.5, 0.5

            delta = event.angleDelta().y()
            if delta == 0:
                return

            factor = 1.25 if delta > 0 else (1.0 / 1.25)
            new_z = max(1.0, min(5.0, self.zoom_level * factor))

            # Maintain focal point (px, py) stationary under cursor
            vw = 1.0 / self.zoom_level
            vh = 1.0 / self.zoom_level
            sx = self.zoom_vx + px * vw
            sy = self.zoom_vy + py * vh

            new_vw = 1.0 / new_z
            new_vh = 1.0 / new_z
            new_vx = sx - px * new_vw
            new_vy = sy - py * new_vh

            self.zoom_level = new_z
            self.zoom_vx = max(0.0, min(1.0 - new_vw, new_vx))
            self.zoom_vy = max(0.0, min(1.0 - new_vh, new_vy))

            if self.zoom_level <= 1.001:
                self.zoom_level = 1.0
                self.zoom_vx = 0.0
                self.zoom_vy = 0.0
                self.setCursor(Qt.CursorShape.ArrowCursor)
            else:
                self.setCursor(Qt.CursorShape.OpenHandCursor)

            self.update()
            event.accept()
        else:
            super().wheelEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.zoom_level > 1.0:
            self.drag_start_pos = event.position()
            self.drag_start_vx = self.zoom_vx
            self.drag_start_vy = self.zoom_vy
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.drag_start_pos is not None and self.zoom_level > 1.0 and self.display_pixmap:
            scaled = self.display_pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            dx = event.position().x() - self.drag_start_pos.x()
            dy = event.position().y() - self.drag_start_pos.y()
            if scaled.width() > 0 and scaled.height() > 0:
                vw = 1.0 / self.zoom_level
                vh = 1.0 / self.zoom_level
                norm_dx = (dx / scaled.width()) * vw
                norm_dy = (dy / scaled.height()) * vh
                self.zoom_vx = max(0.0, min(1.0 - vw, self.drag_start_vx - norm_dx))
                self.zoom_vy = max(0.0, min(1.0 - vh, self.drag_start_vy - norm_dy))
                self.update()
            event.accept()
            return
        elif self.zoom_level > 1.0:
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.drag_start_pos is not None:
            self.drag_start_pos = None
            if self.zoom_level > 1.0:
                self.setCursor(Qt.CursorShape.OpenHandCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        """Double-clicking either camera expands it, or resets digital zoom if currently magnified."""
        # If currently digitally zoomed in, double-click resets digital zoom back to 1.0x
        if self.zoom_level > 1.05:
            self.zoom_level = 1.0
            self.zoom_vx = 0.0
            self.zoom_vy = 0.0
            self.drag_start_pos = None
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self.show_toast("🔍 Zoom digital redefinido para 1.0x", duration_ms=2000)
            self.update()
            return

        if not self.raw_pixmap or self.raw_pixmap.isNull() or not self.display_pixmap:
            return super().mouseDoubleClickEvent(event)

        scaled = self.display_pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        vx = (self.width() - scaled.width()) // 2
        vy = (self.height() - scaled.height()) // 2

        pos = event.position()
        mx = pos.x() - vx
        my = pos.y() - vy

        # Check if double-click is within active video rectangle
        if mx < 0 or mx >= scaled.width() or my < 0 or my >= scaled.height():
            return

        norm_x = mx / scaled.width()
        norm_y = my / scaled.height()

        # If already in single lens zoom, double-click restores dual-lens view
        if self.single_lens is not None:
            self.toggle_single_lens(self.single_lens)
            return

        # Dual-lens click mapping
        if self.layout_mode == "side_by_side":
            if norm_x < 0.5:
                self.toggle_single_lens("top") # Left is Lens 1 (PTZ)
            else:
                self.toggle_single_lens("bottom") # Right is Lens 2 (Fixa)
        else:
            if norm_y < 0.5:
                self.toggle_single_lens("top") # Top is Lens 1 (PTZ)
            else:
                self.toggle_single_lens("bottom") # Bottom is Lens 2 (Fixa)

    def _update_display_pixmap(self):
        if not self.raw_pixmap or self.raw_pixmap.isNull():
            self.display_pixmap = None
            return

        w = self.raw_pixmap.width()
        h = self.raw_pixmap.height()
        h2 = h // 2

        if self.single_lens == "top":
            # Upper lens (PTZ) fills the video area
            self.display_pixmap = self.raw_pixmap.copy(0, 0, w, h2)
        elif self.single_lens == "bottom":
            # Lower lens (Fixed) fills the video area
            self.display_pixmap = self.raw_pixmap.copy(0, h2, w, h2)
        elif self.layout_mode == "side_by_side":
            top_part = self.raw_pixmap.copy(0, 0, w, h2)
            bottom_part = self.raw_pixmap.copy(0, h2, w, h2)

            combined = QPixmap(w * 2, h2)
            combined.fill(QColor("#090d16"))
            p = QPainter(combined)
            p.drawPixmap(0, 0, top_part)
            p.drawPixmap(w, 0, bottom_part)

            # Divider line between lenses
            p.setPen(QColor(51, 65, 85, 180))
            p.drawLine(w, 0, w, h2)
            p.end()
            self.display_pixmap = combined
        else:
            self.display_pixmap = self.raw_pixmap

    def update_frame(self, pixmap: QPixmap, fps: float, w: int, h: int):
        self.raw_pixmap = pixmap
        self._update_display_pixmap()
        self.is_switching = False
        if fps > 0:
            self.fps_text = f"{fps:.1f} FPS"
        if w > 0 and h > 0:
            self.is_hd = (w > 1000)
            tag = "HD" if self.is_hd else "SD"
            if self.single_lens == "top":
                self.res_text = f"{w}x{h//2} ({tag} Lente PTZ)"
            elif self.single_lens == "bottom":
                self.res_text = f"{w}x{h//2} ({tag} Lente Fixa)"
            elif self.layout_mode == "side_by_side":
                self.res_text = f"{w*2}x{h//2} ({tag} Lado a Lado)"
            else:
                self.res_text = f"{w}x{h} ({tag} Vertical)"
        self.update()

    def trigger_flash(self):
        """Camera shutter flash effect."""
        self.is_flashing = True
        self.update()
        QTimer.singleShot(90, self._stop_flash)

    def _stop_flash(self):
        self.is_flashing = False
        self.update()

    def set_switching(self, switching: bool):
        self.is_switching = switching
        self.update()

    def set_status(self, text: str):
        self.status_text = text
        self.update()

    def set_paused(self, paused: bool):
        self.is_paused = paused
        self.update()

    def set_recording(self, recording: bool, time_text: str = ""):
        self.is_recording = recording
        self.rec_time_text = time_text
        self.update()

    def set_auto_tracking(self, active: bool):
        self.is_auto_tracking = active
        self.update()

    def show_toast(self, text: str, duration_ms: int = 3000):
        """
        Displays toast notification and guarantees auto-dismissal after duration_ms (default 3s).
        """
        self.toast_text = text
        self.toast_expires_at = time.time() + (duration_ms / 1000.0)
        self.toast_timer.stop()
        self.toast_timer.setInterval(duration_ms)
        self.toast_timer.start()
        self.update()

    def clear_toast(self):
        self.toast_text = ""
        self.toast_expires_at = 0.0
        self.update()

    def _check_toast_expiry(self):
        if self.toast_text and self.toast_expires_at > 0:
            if time.time() >= self.toast_expires_at:
                self.clear_toast()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#090d16"))

        if self.display_pixmap and not self.display_pixmap.isNull():
            scaled = self.display_pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2

            if self.zoom_level > 1.0:
                pw = self.display_pixmap.width()
                ph = self.display_pixmap.height()
                vw = 1.0 / self.zoom_level
                vh = 1.0 / self.zoom_level
                src_x = int(self.zoom_vx * pw)
                src_y = int(self.zoom_vy * ph)
                src_w = max(1, int(vw * pw))
                src_h = max(1, int(vh * ph))
                src_rect = QRect(src_x, src_y, src_w, src_h)
                dest_rect = QRect(x, y, scaled.width(), scaled.height())
                painter.drawPixmap(dest_rect, self.display_pixmap, src_rect)
            else:
                painter.drawPixmap(x, y, scaled)

            # Camera shutter flash
            if self.is_flashing:
                painter.fillRect(self.rect(), QColor(255, 255, 255, 130))

            # Switching indicator banner
            if self.is_switching:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(15, 23, 42, 180))
                painter.drawRect(self.rect())

                painter.setPen(QColor("#38bdf8"))
                font = painter.font()
                font.setPointSize(13)
                font.setBold(True)
                painter.setFont(font)
                painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "🔄 Otimizando resolução do vídeo...")

            # FPS & Resolution overlay badge
            badge_text = ""
            if self.fps_text and self.res_text:
                badge_text = f"● {self.fps_text} • {self.res_text}"
            elif self.fps_text:
                badge_text = f"● {self.fps_text}"

            if badge_text and not self.is_switching and not self.is_paused:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(15, 23, 42, 210))
                badge_w = 205 if "Lado" in self.res_text else (175 if self.res_text else 85)
                painter.drawRoundedRect(12, 12, badge_w, 26, 6, 6)

                dot_color = QColor("#38bdf8") if self.is_hd else QColor("#22c55e")
                painter.setPen(dot_color)
                font = painter.font()
                font.setPointSize(9)
                font.setBold(True)
                painter.setFont(font)
                painter.drawText(20, 29, badge_text)

            # Auto-Tracking Badge on Video
            if self.is_auto_tracking and not self.is_paused:
                painter.setPen(QColor(168, 85, 247, 220))
                painter.setBrush(QColor(88, 28, 135, 215)) # Purple badge
                painter.drawRoundedRect(12, 44, 175, 24, 6, 6)
                painter.setPen(QColor("#ffffff"))
                font = painter.font()
                font.setPointSize(8)
                font.setBold(True)
                painter.setFont(font)
                painter.drawText(20, 60, "🤖 Rastreamento Ativo")

            # Live Recording Indicator on Video (Top-Right)
            if self.is_recording and not self.is_paused:
                rec_w = 175
                rx = self.width() - rec_w - 12
                ry = 12
                painter.setPen(QColor(239, 68, 68, 230))
                painter.setBrush(QColor(127, 29, 29, 225))
                painter.drawRoundedRect(rx, ry, rec_w, 26, 6, 6)
                painter.setPen(QColor("#ffffff"))
                font = painter.font()
                font.setPointSize(9)
                font.setBold(True)
                painter.setFont(font)
                painter.drawText(rx + 10, ry + 18, f"● REC {self.rec_time_text}")

            # Single Lens Zoom Badge
            if self.single_lens and not self.is_paused:
                lens_txt = "🔍 Lente Superior (PTZ) • 2 cliques / L2 p/ voltar" if self.single_lens == "top" else "🔍 Lente Inferior (Fixa) • 2 cliques / R2 p/ voltar"
                painter.setPen(QColor(56, 189, 248, 220))
                painter.setBrush(QColor(15, 23, 42, 220))
                bw = 310
                painter.drawRoundedRect(12, self.height() - 44, bw, 24, 6, 6)
                painter.setPen(QColor("#38bdf8"))
                font = painter.font()
                font.setPointSize(8)
                font.setBold(True)
                painter.setFont(font)
                painter.drawText(20, self.height() - 28, lens_txt)

            # Digital Zoom Badge
            if self.zoom_level > 1.0 and not self.is_paused:
                z_txt = f"🔍 Zoom {self.zoom_level:.1f}x [Ctrl+Scroll] • Arraste p/ mover • 2 cliques p/ resetar"
                painter.setPen(QColor(234, 179, 8, 220))
                painter.setBrush(QColor(15, 23, 42, 225))
                font = painter.font()
                font.setPointSize(8)
                font.setBold(True)
                painter.setFont(font)
                fm = painter.fontMetrics()
                bw = fm.horizontalAdvance(z_txt) + 20
                painter.drawRoundedRect(self.width() - bw - 14, self.height() - 44, bw, 24, 6, 6)
                painter.setPen(QColor("#facc15"))
                painter.drawText(self.width() - bw - 4, self.height() - 28, z_txt)

            # Paused Overlay (Golden/Amber theme matching pause button)
            if self.is_paused:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(15, 23, 42, 180))
                painter.drawRect(self.rect())

                badge_w = 340
                badge_h = 70
                bx = (self.width() - badge_w) // 2
                by = (self.height() - badge_h) // 2
                painter.setPen(QColor(250, 204, 21, 245)) # #facc15 vibrant yellow border
                painter.setBrush(QColor(161, 98, 7, 235)) # #a16207 warm amber-yellow background
                painter.drawRoundedRect(bx, by, badge_w, badge_h, 10, 10)

                painter.setPen(QColor("#ffffff"))
                font = painter.font()
                font.setPointSize(12)
                font.setBold(True)
                painter.setFont(font)
                painter.drawText(bx, by + 28, badge_w, 24, Qt.AlignmentFlag.AlignCenter, "⏸️ CÂMERA PAUSADA")
                font.setPointSize(9)
                font.setBold(False)
                painter.setFont(font)
                painter.drawText(bx, by + 50, badge_w, 20, Qt.AlignmentFlag.AlignCenter, "Clique no botão ▶ ou aperte Espaço para retomar")

            # Real-time Toast notification popup (auto-dismisses cleanly, fail-safe timestamp)
            if self.toast_text:
                if time.time() >= self.toast_expires_at:
                    self.toast_text = ""
                    self.toast_expires_at = 0.0
                else:
                    lines = self.toast_text.split("\n")
                    toast_h = 36 if len(lines) == 1 else (24 + len(lines) * 18)
                    toast_w = min(self.width() - 40, 560)
                    tx = (self.width() - toast_w) // 2
                    ty = self.height() - toast_h - 18

                    painter.setPen(QColor(52, 211, 153, 230))
                    painter.setBrush(QColor(6, 78, 59, 235))
                    painter.drawRoundedRect(tx, ty, toast_w, toast_h, 8, 8)

                    painter.setPen(QColor("#ffffff"))
                    font = painter.font()
                    font.setPointSize(9 if len(lines) > 2 else 10)
                    font.setBold(True)
                    painter.setFont(font)
                    rect = QRect(tx + 10, ty, toast_w - 20, toast_h)
                    painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.toast_text)

        else:
            painter.setPen(QColor("#94a3b8"))
            font = painter.font()
            font.setPointSize(12)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.status_text)


class ConnectWorker(QThread):
    finished = pyqtSignal(bool, str)

    def __init__(self, cam_mgr: CameraManager, ip: str, port: int, user: str, password: str):
        super().__init__()
        self.cam_mgr = cam_mgr
        self.ip = ip
        self.port = port
        self.user = user
        self.password = password

    def run(self):
        ok = self.cam_mgr.connect(self.ip, self.port, self.user, self.password)
        self.finished.emit(ok, self.ip)


class DiscoveryWorker(QThread):
    finished = pyqtSignal(list)

    def run(self):
        cams = CameraManager.discover_cameras(timeout=2.0)
        self.finished.emit(cams)


class AutoTrackWorker(QThread):
    finished = pyqtSignal(bool, bool) # success, enabled

    def __init__(self, cam_mgr: CameraManager, enable: bool):
        super().__init__()
        self.cam_mgr = cam_mgr
        self.enable = enable

    def run(self):
        ok = self.cam_mgr.set_auto_tracking(self.enable)
        self.finished.emit(ok, self.enable)


class LightWorker(QThread):
    finished = pyqtSignal(bool, str) # success, mode

    def __init__(self, cam_mgr: CameraManager, mode: str):
        super().__init__()
        self.cam_mgr = cam_mgr
        self.mode = mode

    def run(self):
        ok = self.cam_mgr.set_light_mode(self.mode)
        self.finished.emit(ok, self.mode)


class RebootWorker(QThread):
    finished = pyqtSignal(bool)

    def __init__(self, cam_mgr: CameraManager):
        super().__init__()
        self.cam_mgr = cam_mgr

    def run(self):
        ok = self.cam_mgr.reboot_camera()
        self.finished.emit(ok)


class RebootDialog(QDialog):
    """Custom dark frameless modal dialog for camera reboot confirmation."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("reboot_dlg_title", "🔄 Reiniciar Câmera"))
        self.setFixedSize(380, 160)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setStyleSheet("""
            QDialog {
                background-color: #1e293b;
                border: 1px solid #475569;
                border-radius: 8px;
            }
            QLabel {
                color: #f8fafc;
                background: transparent;
            }
            QPushButton {
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: bold;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 14)
        layout.setSpacing(10)

        # Custom dark header bar with title and close '✕' button
        hdr = QHBoxLayout()
        hdr.setContentsMargins(0, 0, 0, 2)
        lbl_hdr = QLabel(tr("reboot_dlg_title", "🔄 Reiniciar Câmera"))
        lbl_hdr.setStyleSheet("font-size: 12px; font-weight: bold; color: #94a3b8;")
        btn_close = QPushButton("✕")
        btn_close.setFixedSize(24, 24)
        btn_close.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #94a3b8;
                border: none;
                font-size: 13px;
                font-weight: bold;
                padding: 0px;
            }
            QPushButton:hover {
                color: #ef4444;
                background-color: rgba(239, 68, 68, 0.2);
                border-radius: 4px;
            }
        """)
        btn_close.clicked.connect(self.reject)
        hdr.addWidget(lbl_hdr)
        hdr.addStretch()
        hdr.addWidget(btn_close)
        layout.addLayout(hdr)

        top_box = QHBoxLayout()
        top_box.setSpacing(12)

        lbl_icon = QLabel("🔄")
        lbl_icon.setStyleSheet("font-size: 26px; background: transparent;")
        top_box.addWidget(lbl_icon, alignment=Qt.AlignmentFlag.AlignTop)

        text_box = QVBoxLayout()
        text_box.setSpacing(4)
        lbl_title = QLabel(tr("reboot_dlg_msg", "Deseja reiniciar a câmera agora?"))
        lbl_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #f8fafc;")
        text_box.addWidget(lbl_title)

        lbl_sub = QLabel(tr("reboot_dlg_sub", "A reconexão levará cerca de 30 a 50 segundos."))
        lbl_sub.setStyleSheet("font-size: 11px; color: #94a3b8;")
        text_box.addWidget(lbl_sub)
        top_box.addLayout(text_box)
        layout.addLayout(top_box)

        layout.addStretch()

        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)
        btn_box.addStretch()

        btn_cancel = QPushButton(tr("btn_cancel", "Cancelar"))
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #334155;
                color: #f8fafc;
                border: 1px solid #475569;
            }
            QPushButton:hover { background-color: #475569; }
        """)
        btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancel)

        btn_confirm = QPushButton(tr("reboot_dlg_confirm", "Sim, Reiniciar"))
        btn_confirm.setStyleSheet("""
            QPushButton {
                background-color: #dc2626;
                color: #ffffff;
                border: 1px solid #ef4444;
            }
            QPushButton:hover { background-color: #b91c1c; }
        """)
        btn_confirm.clicked.connect(self.accept)
        btn_box.addWidget(btn_confirm)

        layout.addLayout(btn_box)
        self._drag_pos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        event.accept()


class ShutdownDialog(QDialog):
    """Custom dark frameless modal dialog for scheduled shutdown with real-time countdown."""
    def __init__(self, parent=None, countdown_sec=60):
        super().__init__(parent)
        self.setWindowTitle(tr("shut_dlg_title", "⚠️ Desligamento do Computador"))
        self.setFixedSize(400, 175)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.countdown = countdown_sec
        self.cancelled = False
        self.immediate = False

        self.setStyleSheet("""
            QDialog {
                background-color: #1e293b;
                border: 1px solid #475569;
                border-radius: 8px;
            }
            QLabel {
                color: #f8fafc;
                background: transparent;
            }
            QPushButton {
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: bold;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 14)
        layout.setSpacing(10)

        # Custom dark header bar with title and close '✕' button
        hdr = QHBoxLayout()
        hdr.setContentsMargins(0, 0, 0, 2)
        lbl_hdr = QLabel(tr("shut_dlg_title", "⚠️ Desligamento do Computador"))
        lbl_hdr.setStyleSheet("font-size: 12px; font-weight: bold; color: #94a3b8;")
        btn_close = QPushButton("✕")
        btn_close.setFixedSize(24, 24)
        btn_close.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #94a3b8;
                border: none;
                font-size: 13px;
                font-weight: bold;
                padding: 0px;
            }
            QPushButton:hover {
                color: #ef4444;
                background-color: rgba(239, 68, 68, 0.2);
                border-radius: 4px;
            }
        """)
        btn_close.clicked.connect(self._on_cancel)
        hdr.addWidget(lbl_hdr)
        hdr.addStretch()
        hdr.addWidget(btn_close)
        layout.addLayout(hdr)

        top_box = QHBoxLayout()
        top_box.setSpacing(12)

        lbl_icon = QLabel("⚠️")
        lbl_icon.setStyleSheet("font-size: 26px; background: transparent;")
        top_box.addWidget(lbl_icon, alignment=Qt.AlignmentFlag.AlignTop)

        text_box = QVBoxLayout()
        text_box.setSpacing(4)
        lbl_title = QLabel(tr("shut_dlg_msg", "Gravação concluída com sucesso!"))
        lbl_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #f8fafc;")
        text_box.addWidget(lbl_title)

        self.lbl_countdown = QLabel(tr("shut_dlg_countdown", "O computador será desligado em {sec} segundos...").replace("{sec}", str(self.countdown)))
        self.lbl_countdown.setStyleSheet("font-size: 11px; color: #fbbf24; font-weight: bold;")
        text_box.addWidget(self.lbl_countdown)
        top_box.addLayout(text_box)
        layout.addLayout(top_box)

        layout.addStretch()

        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)
        btn_box.addStretch()

        btn_cancel = QPushButton(tr("shut_btn_cancel", "Cancelar Desligamento"))
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #334155;
                color: #f8fafc;
                border: 1px solid #475569;
            }
            QPushButton:hover { background-color: #475569; }
        """)
        btn_cancel.clicked.connect(self._on_cancel)
        btn_box.addWidget(btn_cancel)

        btn_now = QPushButton(tr("shut_btn_now", "Desligar Agora"))
        btn_now.setStyleSheet("""
            QPushButton {
                background-color: #dc2626;
                color: #ffffff;
                border: 1px solid #ef4444;
            }
            QPushButton:hover { background-color: #b91c1c; }
        """)
        btn_now.clicked.connect(self._on_immediate)
        btn_box.addWidget(btn_now)

        layout.addLayout(btn_box)

        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._tick)
        self.timer.start()
        self._drag_pos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        event.accept()

    def _tick(self):
        self.countdown -= 1
        if self.countdown > 0:
            self.lbl_countdown.setText(tr("shut_dlg_countdown", "O computador será desligado em {sec} segundos...").replace("{sec}", str(self.countdown)))
        else:
            self.timer.stop()
            self.accept()

    def _on_cancel(self):
        self.timer.stop()
        self.cancelled = True
        self.reject()

    def _on_immediate(self):
        self.timer.stop()
        self.immediate = True
        self.accept()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ICSee Desktop Viewer - Câmera ao Vivo")

        self.config = self.load_config()
        set_language(self.config.get("lang", "pt"))
        
        # Exact default size requested: 960 x 560
        init_w = self.config.get("window_width", 960)
        init_h = self.config.get("window_height", 560)
        self.resize(init_w, init_h)
        self.setMinimumSize(720, 420)

        # Eliminate default white QMenuBar in QMainWindow
        if self.menuBar():
            self.menuBar().setVisible(False)
            self.menuBar().setFixedHeight(0)

        self.cam_mgr = CameraManager()
        self.worker: Optional[VideoWorker] = None
        self.connect_worker: Optional[ConnectWorker] = None
        self.discovery_worker: Optional[DiscoveryWorker] = None
        self.gamepad_worker: Optional[GamepadWorker] = None
        self.recorder: Optional[VideoRecorder] = None
        self.light_worker: Optional[LightWorker] = None
        self.reboot_worker: Optional[RebootWorker] = None
        self.audio_receiver: Optional[CameraAudioReceiver] = None
        self.talk_worker: Optional[CameraTalkWorker] = None
        self.is_listening_audio = False
        self.is_talking = False
        self.last_qimage: Optional[QImage] = None
        self.current_fps = 0.0
        self.current_w = 0
        self.current_h = 0
        self.active_keys = set()
        self.last_saved_path: Optional[str] = None
        self.gamepad_name = ""
        self.is_camera_paused = False
        self.is_auto_tracking = False
        self.last_frame_time: float = time.time()
        self.scroll_ptz: Optional[QScrollArea] = None
        self.panel_tips: Optional[QFrame] = None

        self.cam_mgr.user = self.config.get("user", "admin")
        self.cam_mgr.password = self.config.get("password", "")
        self.cam_mgr.invert_x = self.config.get("invert_x", True)
        self.cam_mgr.invert_y = self.config.get("invert_y", False)

        self.init_ui()
        self.apply_theme()
        self.init_gamepad()
        register_listener(self.update_ui_texts)
        self.update_ui_texts()

        # Dedicated F11 Global Shortcut covering Windows taskbar
        self.shortcut_f11 = QShortcut(QKeySequence(Qt.Key.Key_F11), self)
        self.shortcut_f11.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self.shortcut_f11.activated.connect(self.toggle_fullscreen)

        # Stream Health Watchdog: verifies that frames continue flowing smoothly
        self.watchdog_timer = QTimer(self)
        self.watchdog_timer.setInterval(2500)
        self.watchdog_timer.timeout.connect(self._check_stream_health)
        self.watchdog_timer.start()

        QTimer.singleShot(100, lambda: apply_windows_dark_titlebar(self))
        QTimer.singleShot(150, self.auto_start)

    def showEvent(self, event):
        super().showEvent(event)
        apply_windows_dark_titlebar(self)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w = self.width()

        # Automodulate top bar buttons on compression to prevent widget collision
        is_compact = (w < 920)
        if hasattr(self, "btn_snapshot"):
            self.btn_snapshot.setText("📸" if is_compact else tr("btn_photo"))
            self.btn_tips.setText("🎮" if is_compact else tr("btn_tips"))
            self.btn_top.setText("📌" if is_compact else tr("btn_pin"))
            self.btn_layout_vert.setText("⯀" if is_compact else tr("btn_normal"))
            self.btn_layout_side.setText("⚏" if is_compact else tr("btn_side"))

        if hasattr(self, "lbl_keys"):
            if w < 920:
                self.lbl_keys.setText(tr("status_shortcuts_compact", "[Setas] PTZ | [2 Cliques/L2/R2] Zoom | [Espaço] Pausa | [S] Foto | [R] REC | [F11] Full"))
            else:
                self.lbl_keys.setText(tr("status_shortcuts", "Atalhos: [↑ ↓ ← →] ou Analógico | [2 Cliques / L2 / R2] Ampliar Lente | [Espaço / ○] Pausar | [S / △] Foto | [R] Gravar | [F11] Full"))

        if not self.isFullScreen() and not self.isMaximized():
            self.config["window_width"] = w
            self.config["window_height"] = self.height()

    def closeEvent(self, event):
        if not self.isFullScreen() and not self.isMaximized():
            self.config["window_width"] = self.width()
            self.config["window_height"] = self.height()
            self.save_config()
        if hasattr(self, "watchdog_timer") and self.watchdog_timer.isActive():
            self.watchdog_timer.stop()
        if self.recorder and self.recorder.isRunning():
            self.recorder.stop_recording()
            self.recorder.wait(1000)
        if self.worker:
            self.worker.stop()
        if self.audio_receiver and self.audio_receiver.isRunning():
            self.audio_receiver.stop()
        if self.talk_worker and self.talk_worker.isRunning():
            self.talk_worker.stop()
        if self.gamepad_worker:
            self.gamepad_worker.stop_worker()
        self.cam_mgr.ptz_stop()
        event.accept()

    def load_config(self) -> dict:
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    res = DEFAULT_CONFIG.copy()
                    res.update(cfg)
                    return res
            except Exception:
                pass
        return DEFAULT_CONFIG.copy()

    def save_config(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Top Bar: Responsive, automodulating layout without widget collision
        top_bar = QWidget()
        top_bar.setObjectName("topBar")
        top_bar.setFixedHeight(48)
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(8, 4, 8, 4)
        top_layout.setSpacing(5)

        # Title
        lbl_title = QLabel("📷 ICSee")
        lbl_title.setObjectName("appTitle")
        top_layout.addWidget(lbl_title)

        # Camera selection dropdown: full width, no truncation / abbreviation
        self.combo_cams = QComboBox()
        self.combo_cams.setObjectName("camSelector")
        self.combo_cams.setMinimumWidth(180)
        self.combo_cams.setMaximumWidth(420)
        self.combo_cams.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.combo_cams.view().clicked.connect(
            lambda idx: (self.combo_cams.setCurrentIndex(idx.row()), self.combo_cams.hidePopup(), self.on_camera_selected(idx.row()))
        )
        self.combo_cams.setToolTip("Câmera Selecionada:\nExibe a câmera ativa com nome e IP completos. Clique para alternar entre câmeras.")
        self.combo_cams.activated.connect(self.on_camera_selected)
        top_layout.addWidget(self.combo_cams)

        # Discover button: compact icon
        self.btn_discover = QPushButton("🔍")
        self.btn_discover.setObjectName("compactBtn")
        self.btn_discover.setToolTip("Buscar Câmeras na Rede (ONVIF):\nVarre a rede local automaticamente para detectar câmeras ICSee.")
        self.btn_discover.clicked.connect(self.run_discovery)
        top_layout.addWidget(self.btn_discover)

        top_layout.addStretch(1)

        # Dual-Lens View Layout Switcher (Vertical vs Side-by-Side)
        layout_box = QFrame()
        layout_box.setObjectName("segmentedBox")
        l_layout = QHBoxLayout(layout_box)
        l_layout.setContentsMargins(2, 2, 2, 2)
        l_layout.setSpacing(2)

        self.btn_layout_vert = QPushButton("⯀ Normal")
        self.btn_layout_vert.setCheckable(True)
        self.btn_layout_vert.setObjectName("segmentBtn")
        self.btn_layout_vert.setToolTip("Modo Normal (Vertical):\nExibe a visão original da câmera, com a lente móvel (PTZ) em cima e a fixa embaixo.\nAtalho: Quadrado (□) / X no controle")
        self.btn_layout_vert.clicked.connect(lambda: self.set_layout_mode("vertical"))

        self.btn_layout_side = QPushButton("⚏ Lado a Lado")
        self.btn_layout_side.setCheckable(True)
        self.btn_layout_side.setObjectName("segmentBtn")
        self.btn_layout_side.setToolTip("Modo Lado a Lado (Horizontal):\nDivide o vídeo ao meio e posiciona as duas lentes lado a lado em visão panorâmica ampla.\nAtalho: Quadrado (□) / X no controle")
        self.btn_layout_side.clicked.connect(lambda: self.set_layout_mode("side_by_side"))

        init_layout = self.config.get("layout_mode", "vertical")
        self.btn_layout_vert.setChecked(init_layout == "vertical")
        self.btn_layout_side.setChecked(init_layout == "side_by_side")

        l_layout.addWidget(self.btn_layout_vert)
        l_layout.addWidget(self.btn_layout_side)
        top_layout.addWidget(layout_box)

        # Dedicated SD / HD Quality Switcher
        quality_box = QFrame()
        quality_box.setObjectName("segmentedBox")
        q_layout = QHBoxLayout(quality_box)
        q_layout.setContentsMargins(2, 2, 2, 2)
        q_layout.setSpacing(2)

        self.btn_sd = QPushButton("⚡ SD")
        self.btn_sd.setCheckable(True)
        self.btn_sd.setObjectName("segmentBtn")
        self.btn_sd.setToolTip("Modo Fluido (640x720):\nTransmissão ultraleve com resposta instantânea e consumo mínimo de CPU/rede.\nAtalho: L1 / LB no controle")
        self.btn_sd.clicked.connect(lambda: self.set_quality("sub"))

        self.btn_hd = QPushButton("🌟 HD")
        self.btn_hd.setCheckable(True)
        self.btn_hd.setObjectName("segmentBtn")
        self.btn_hd.setToolTip("Modo Alta Resolução (2304x2592):\nMáxima nitidez dos sensores de 8 MP para ver detalhes finos e rostos.\nAtalho: R1 / RB no controle")
        self.btn_hd.clicked.connect(lambda: self.set_quality("main"))

        initial_q = self.config.get("quality", "sub")
        self.btn_sd.setChecked(initial_q == "sub")
        self.btn_hd.setChecked(initial_q == "main")

        q_layout.addWidget(self.btn_sd)
        q_layout.addWidget(self.btn_hd)
        top_layout.addWidget(quality_box)

        # Always on Top toggle
        self.btn_top = QPushButton("📌 Fixar")
        self.btn_top.setObjectName("btnToggle")
        self.btn_top.setCheckable(True)
        self.btn_top.setChecked(self.config.get("always_on_top", False))
        self.btn_top.setToolTip("Fixar Janela Sempre no Topo (Always on Top):\nMantém a janela da câmera visível sobre todos os outros programas.\nAtalho: Tecla T")
        self.btn_top.clicked.connect(self.toggle_always_on_top)
        top_layout.addWidget(self.btn_top)

        # Instant 1-Click Snapshot button
        self.btn_snapshot = QPushButton("📸 Foto")
        self.btn_snapshot.setToolTip("Captura Instantânea em 1 Clique:\nTira uma foto da visão atual e salva diretamente na sua pasta Imagens.\nAtalho: Tecla S ou Triângulo (△) / Y no controle")
        self.btn_snapshot.clicked.connect(self.take_snapshot)
        top_layout.addWidget(self.btn_snapshot)

        # Control Tips button
        self.btn_tips = QPushButton("🎮 Dicas")
        self.btn_tips.setToolTip("Guia Rápido de Controles e Atalhos:\nExibe os botões do controle DualSense/Xbox e atalhos do teclado.")
        self.btn_tips.clicked.connect(self.toggle_tips_panel)
        top_layout.addWidget(self.btn_tips)

        # Settings button
        self.btn_settings = QPushButton("⚙️")
        self.btn_settings.setObjectName("compactBtn")
        self.btn_settings.setToolTip("Configurações da Câmera:\nAbre o painel de IP, porta, usuário, senha, inversão PTZ e inicialização com o Windows.")
        self.btn_settings.clicked.connect(self.toggle_settings_panel)
        top_layout.addWidget(self.btn_settings)

        main_layout.addWidget(top_bar)

        # 2. Settings Collapsible Panel (Responsive 2-Row Layout)
        self.panel_settings = QFrame()
        self.panel_settings.setObjectName("settingsPanel")
        self.panel_settings.setVisible(False)
        sett_layout = QVBoxLayout(self.panel_settings)
        sett_layout.setContentsMargins(14, 8, 14, 8)
        sett_layout.setSpacing(6)

        # Row 1: Connection Settings
        row1 = QHBoxLayout()
        row1.setSpacing(8)

        self.lbl_conn = QLabel(tr("sett_conn", "🌐 Conexão:"))
        self.lbl_conn.setStyleSheet("font-weight: bold; color: #38bdf8;")
        row1.addWidget(self.lbl_conn)

        self.lbl_ip = QLabel(tr("sett_ip", "IP:"))
        row1.addWidget(self.lbl_ip)
        self.edit_ip = QLineEdit(self.config.get("ip", "192.168.1.10"))
        self.edit_ip.setFixedWidth(115)
        self.edit_ip.setToolTip("Endereço IP local da câmera na sua rede")
        row1.addWidget(self.edit_ip)

        self.lbl_port = QLabel(tr("sett_port", "Porta:"))
        row1.addWidget(self.lbl_port)
        self.edit_port = QLineEdit(str(self.config.get("port", 8899)))
        self.edit_port.setFixedWidth(50)
        self.edit_port.setToolTip("Porta ONVIF padrão (8899)")
        row1.addWidget(self.edit_port)

        self.lbl_user = QLabel(tr("sett_user", "Usuário:"))
        row1.addWidget(self.lbl_user)
        self.edit_user = QLineEdit(self.config.get("user", "admin"))
        self.edit_user.setFixedWidth(75)
        self.edit_user.setToolTip("Nome do usuário cadastrado na câmera (padrão: admin)")
        row1.addWidget(self.edit_user)

        self.lbl_pass = QLabel(tr("sett_pass", "Senha:"))
        row1.addWidget(self.lbl_pass)
        pw_box = QHBoxLayout()
        pw_box.setSpacing(2)
        self.edit_pass = QLineEdit(self.config.get("password", ""))
        self.edit_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.edit_pass.setFixedWidth(100)
        self.edit_pass.setToolTip("Senha cadastrada na câmera (opção NVR/IPC no app)")
        pw_box.addWidget(self.edit_pass)

        # Toggle password visibility button
        self.btn_toggle_pw = QPushButton("👁️")
        self.btn_toggle_pw.setObjectName("iconBtn")
        self.btn_toggle_pw.setToolTip("Mostrar / Ocultar Senha")
        self.btn_toggle_pw.setFixedSize(28, 26)
        self.btn_toggle_pw.clicked.connect(self.toggle_password_visibility)
        pw_box.addWidget(self.btn_toggle_pw)
        row1.addLayout(pw_box)

        row1.addStretch()
        sett_layout.addLayout(row1)

        # Row 2: Preferences & Save
        row2 = QHBoxLayout()
        row2.setSpacing(14)

        self.lbl_pref = QLabel(tr("sett_options", "⚙️ Opções:"))
        self.lbl_pref.setStyleSheet("font-weight: bold; color: #38bdf8;")
        row2.addWidget(self.lbl_pref)

        self.chk_invert_x = QCheckBox("Inverter Horizontal (PTZ)")
        self.chk_invert_x.setChecked(self.config.get("invert_x", True))
        self.chk_invert_x.setToolTip("Inverter Horizontal:\nCorrige a rotação para que esquerda/direita na tela correspondam à sua perspectiva física.")
        self.chk_invert_x.toggled.connect(self.on_invert_toggled)
        row2.addWidget(self.chk_invert_x)

        self.chk_autostart = QCheckBox("Iniciar com o Windows")
        self.chk_autostart.setChecked(self.config.get("start_with_windows", False))
        self.chk_autostart.setToolTip("Iniciar com o Windows:\nFaz o aplicativo abrir automaticamente ao ligar o computador.")
        self.chk_autostart.toggled.connect(self.on_autostart_toggled)
        row2.addWidget(self.chk_autostart)

        self.chk_start_minimized = QCheckBox("Iniciar Minimizado")
        self.chk_start_minimized.setChecked(self.config.get("start_minimized", False))
        self.chk_start_minimized.setToolTip("Iniciar Minimizado:\nInicia o aplicativo minimizado na barra de tarefas (evita abrir em tela cheia).")
        self.chk_start_minimized.toggled.connect(self.on_start_minimized_toggled)
        row2.addWidget(self.chk_start_minimized)

        self.lbl_lang_setting = QLabel(tr("lbl_language", "🌐 Idioma:"))
        self.lbl_lang_setting.setStyleSheet("font-weight: bold; color: #38bdf8;")
        row2.addWidget(self.lbl_lang_setting)

        self.combo_lang = QComboBox()
        self.combo_lang.setFixedWidth(135)
        self.combo_lang.setToolTip("Selecione o idioma da interface (10 idiomas nativos)")
        for code, label in LANGUAGES:
            self.combo_lang.addItem(label, code)
        cur_lang = self.config.get("lang", "pt")
        idx = next((i for i, (c, _) in enumerate(LANGUAGES) if c == cur_lang), 0)
        self.combo_lang.setCurrentIndex(idx)
        self.combo_lang.currentIndexChanged.connect(self.on_language_changed)
        row2.addWidget(self.combo_lang)

        row2.addStretch()

        self.btn_reset_cache = QPushButton(tr("btn_reset_cache", "🧹 Limpar Dados / Cache"))
        self.btn_reset_cache.setObjectName("btnResetCache")
        self.btn_reset_cache.setToolTip("Limpar Dados / Cache:\nApaga todas as credenciais salvas, histórico e restaura os padrões limpos.")
        self.btn_reset_cache.clicked.connect(self.prompt_reset_cache)
        row2.addWidget(self.btn_reset_cache)

        self.btn_apply = QPushButton(tr("btn_save_connect", "💾 Salvar e Conectar"))
        self.btn_apply.setObjectName("primaryButton")
        self.btn_apply.setToolTip("Salvar e Conectar:\nGrava as configurações imediatamente e reconecta à câmera.")
        self.btn_apply.clicked.connect(self.apply_manual_settings)
        row2.addWidget(self.btn_apply)

        sett_layout.addLayout(row2)
        main_layout.addWidget(self.panel_settings)

        # 3. Tips Collapsible Panel
        self.panel_tips = QFrame()
        self.panel_tips.setObjectName("tipsPanel")
        self.panel_tips.setVisible(False)
        tips_main_layout = QVBoxLayout(self.panel_tips)
        tips_main_layout.setContentsMargins(14, 10, 14, 10)
        tips_main_layout.setSpacing(8)

        # Header with close button
        tips_header = QHBoxLayout()
        self.lbl_tips_head = QLabel(tr("tips_title", "🎮 Guia Rápido de Controles e Atalhos"))
        self.lbl_tips_head.setStyleSheet("font-size: 14px; font-weight: bold; color: #38bdf8;")
        tips_header.addWidget(self.lbl_tips_head)
        tips_header.addStretch()

        self.btn_close_tips = QPushButton(tr("tips_close", "✕ Fechar"))
        self.btn_close_tips.setObjectName("compactBtn")
        self.btn_close_tips.setToolTip("Ocultar painel de dicas")
        self.btn_close_tips.clicked.connect(self.toggle_tips_panel)
        tips_header.addWidget(self.btn_close_tips)
        tips_main_layout.addLayout(tips_header)

        # 2 Column Cards: Gamepad and Keyboard
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(12)

        # Card 1: Gamepad
        card_gp = QFrame()
        card_gp.setObjectName("tipCard")
        gp_box = QVBoxLayout(card_gp)
        gp_box.setContentsMargins(10, 8, 10, 8)
        gp_box.setSpacing(4)
        self.lbl_gp_t = QLabel(tr("tips_gamepad_title", "🎮 Controles DualSense (PS5/PS4) & Xbox"))
        self.lbl_gp_t.setStyleSheet("font-weight: bold; color: #a78bfa; font-size: 12px;")
        gp_box.addWidget(self.lbl_gp_t)

        self.tips_gp_labels = [
            (QLabel(), "tips_gp_stick", "🕹️ <b>Analógico / D-Pad:</b> Girar câmera (sensibilidade analógica)"),
            (QLabel(), "tips_gp_pause", "⏸️ <b>Círculo (○) / B:</b> Pausar / Retomar Câmera"),
            (QLabel(), "tips_gp_l2", "🔍 <b>Gatilho L2 / LT:</b> Ampliar / Restaurar Câmera Superior/Esquerda"),
            (QLabel(), "tips_gp_r2", "🔍 <b>Gatilho R2 / RT:</b> Ampliar / Restaurar Câmera Inferior/Direita"),
            (QLabel(), "tips_gp_photo", "📸 <b>Triângulo (△) / Y:</b> Foto instantânea (pasta Imagens)"),
            (QLabel(), "tips_gp_mode", "📐 <b>Quadrado (□) / X:</b> Alternar Normal ↔ Lado a Lado"),
            (QLabel(), "tips_gp_l1", "⚡ <b>Gatilho L1 / LB:</b> Ativar modo SD Fluido (640x720)"),
            (QLabel(), "tips_gp_r1", "🌟 <b>Gatilho R1 / RB:</b> Ativar modo HD Ultra (2304x2592)"),
        ]
        for lbl, key, default in self.tips_gp_labels:
            lbl.setText(tr(key, default))
            gp_box.addWidget(lbl)
        cards_layout.addWidget(card_gp, stretch=1)

        # Card 2: Keyboard & Mouse
        card_kb = QFrame()
        card_kb.setObjectName("tipCard")
        kb_box = QVBoxLayout(card_kb)
        kb_box.setContentsMargins(10, 8, 10, 8)
        kb_box.setSpacing(4)
        self.lbl_kb_t = QLabel(tr("tips_kb_title", "⌨️ Teclado & Mouse"))
        self.lbl_kb_t.setStyleSheet("font-weight: bold; color: #38bdf8; font-size: 12px;")
        kb_box.addWidget(self.lbl_kb_t)

        self.tips_kb_labels = [
            (QLabel(), "tips_kb_click", "🖱️ <b>Dois cliques no vídeo:</b> Ampliar câmera escolhida (2 cliques p/ voltar)"),
            (QLabel(), "tips_kb_arrows", "⬆️⬇️⬅️➡️ <b>Setas do Teclado:</b> Girar câmera PTZ"),
            (QLabel(), "tips_kb_space", "⏸️ <b>Barra de Espaço:</b> Pausar / Retomar Câmera"),
            (QLabel(), "tips_kb_s", "📸 <b>Tecla S:</b> Foto instantânea em 1 clique"),
            (QLabel(), "tips_kb_r", "🎥 <b>Tecla R:</b> Iniciar / Parar gravação de vídeo"),
            (QLabel(), "tips_kb_t", "📌 <b>Tecla T:</b> Fixar janela sempre no topo"),
            (QLabel(), "tips_kb_f11", "🖥️ <b>Tecla F11:</b> Alternar modo Tela Cheia"),
        ]
        for lbl, key, default in self.tips_kb_labels:
            lbl.setText(tr(key, default))
            kb_box.addWidget(lbl)
        cards_layout.addWidget(card_kb, stretch=1)

        tips_main_layout.addLayout(cards_layout)
        main_layout.addWidget(self.panel_tips)

        # 4. Center Area: Video + PTZ Controls with Scroll Area
        center_widget = QWidget()
        center_layout = QHBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)

        # Video Canvas
        self.video_widget = VideoWidget()
        self.video_widget.set_layout_mode(init_layout)
        center_layout.addWidget(self.video_widget, stretch=1)

        # PTZ Side Panel inside QScrollArea (prevents squishing or overlapping)
        self.panel_ptz = QFrame()
        self.panel_ptz.setObjectName("ptzPanel")
        ptz_layout = QVBoxLayout(self.panel_ptz)
        ptz_layout.setContentsMargins(8, 8, 8, 8)
        ptz_layout.setSpacing(5)

        self.lbl_ptz_title = QLabel(tr("ptz_title", "🎮 Controle de Giro (PTZ)"))
        self.lbl_ptz_title.setObjectName("sectionTitle")
        ptz_layout.addWidget(self.lbl_ptz_title)

        self.lbl_hint = QLabel(tr("ptz_hint", "Setas do teclado, botões ou controle!"))
        self.lbl_hint.setWordWrap(True)
        self.lbl_hint.setObjectName("hintText")
        ptz_layout.addWidget(self.lbl_hint)

        # D-Pad Grid Layout for PTZ Buttons
        dpad_container = QWidget()
        dpad_container.setFixedSize(180, 180)
        dpad_layout = QVBoxLayout(dpad_container)
        dpad_layout.setContentsMargins(0, 0, 0, 0)
        dpad_layout.setSpacing(6)

        # Row 1: Up
        r1 = QHBoxLayout()
        r1.addStretch()
        self.btn_up = QPushButton("▲")
        self.btn_up.setObjectName("dpadBtn")
        self.btn_up.setToolTip("Cima (Segure para virar para cima)\nAtalho: Seta Cima ou Analógico")
        self.setup_ptz_button(self.btn_up, "up")
        r1.addWidget(self.btn_up)
        r1.addStretch()
        dpad_layout.addLayout(r1)

        # Row 2: Left - Stop/Pause - Right
        r2 = QHBoxLayout()
        self.btn_left = QPushButton("◀")
        self.btn_left.setObjectName("dpadBtn")
        self.btn_left.setToolTip("Esquerda (Segure para virar para a esquerda)\nAtalho: Seta Esquerda ou Analógico")
        self.setup_ptz_button(self.btn_left, "left")
        r2.addWidget(self.btn_left)

        # Center Button: Pause / Resume Camera (⏸ in normal, ▶ in paused)
        self.btn_stop = QPushButton("⏸")
        self.btn_stop.setObjectName("pauseBtn")
        self.btn_stop.setToolTip("Pausar / Retomar Câmera:\nClique para pausar ou retomar a transmissão ao vivo da câmera.\nAtalho: Barra de Espaço ou Círculo (○) / B no controle")
        self.btn_stop.clicked.connect(self.toggle_camera_pause)
        r2.addWidget(self.btn_stop)

        self.btn_right = QPushButton("▶")
        self.btn_right.setObjectName("dpadBtn")
        self.btn_right.setToolTip("Direita (Segure para virar para a direita)\nAtalho: Seta Direita ou Analógico")
        self.setup_ptz_button(self.btn_right, "right")
        r2.addWidget(self.btn_right)
        dpad_layout.addLayout(r2)

        # Row 3: Down
        r3 = QHBoxLayout()
        r3.addStretch()
        self.btn_down = QPushButton("▼")
        self.btn_down.setObjectName("dpadBtn")
        self.btn_down.setToolTip("Baixo (Segure para virar para baixo)\nAtalho: Seta Baixo ou Analógico")
        self.setup_ptz_button(self.btn_down, "down")
        r3.addWidget(self.btn_down)
        r3.addStretch()
        dpad_layout.addLayout(r3)

        ptz_layout.addWidget(dpad_container, alignment=Qt.AlignmentFlag.AlignCenter)

        # Speed slider
        self.lbl_vel = QLabel(tr("speed_label", "Velocidade do Giro:"))
        self.lbl_vel.setToolTip("Ajuste a velocidade de rotação dos motores da câmera")
        ptz_layout.addWidget(self.lbl_vel)

        self.slider_speed = QSlider(Qt.Orientation.Horizontal)
        self.slider_speed.setRange(1, 10)
        self.slider_speed.setValue(int(self.config.get("speed", 0.5) * 10))
        self.slider_speed.setToolTip("Arraste para ajustar a velocidade do giro (Lento 🐢 até Rápido 🐇)")
        self.slider_speed.valueChanged.connect(self.on_speed_changed)
        ptz_layout.addWidget(self.slider_speed)

        speed_labels = QHBoxLayout()
        self.lbl_slow = QLabel(tr("speed_slow", "Lento 🐢"))
        self.lbl_slow.setStyleSheet("font-size: 11px; color: #64748b;")
        self.lbl_fast = QLabel(tr("speed_fast", "Rápido 🐇"))
        self.lbl_fast.setStyleSheet("font-size: 11px; color: #64748b;")
        speed_labels.addWidget(self.lbl_slow)
        speed_labels.addStretch()
        speed_labels.addWidget(self.lbl_fast)
        ptz_layout.addLayout(speed_labels)

        # Quick Step Buttons
        ptz_layout.addSpacing(4)
        self.lbl_step = QLabel(tr("step_title", "Dar um toque (Giro rápido):"))
        self.lbl_step.setObjectName("subTitle")
        self.lbl_step.setToolTip("Toque único para girar um passo curto calibrado")
        ptz_layout.addWidget(self.lbl_step)

        step_box = QHBoxLayout()
        step_box.setSpacing(4)
        self.btn_step_l = QPushButton(tr("btn_step_left", "↶ Esquerda"))
        self.btn_step_l.setObjectName("stepBtn")
        self.btn_step_l.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.btn_step_l.setToolTip("Giro rápido de 0.35s para a esquerda")
        self.btn_step_l.clicked.connect(lambda: self.cam_mgr.ptz_step("left", self.get_speed(), 0.35))
        self.btn_step_r = QPushButton(tr("btn_step_right", "Direita ↷"))
        self.btn_step_r.setObjectName("stepBtn")
        self.btn_step_r.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.btn_step_r.setToolTip("Giro rápido de 0.35s para a direita")
        self.btn_step_r.clicked.connect(lambda: self.cam_mgr.ptz_step("right", self.get_speed(), 0.35))
        step_box.addWidget(self.btn_step_l, 1)
        step_box.addWidget(self.btn_step_r, 1)
        ptz_layout.addLayout(step_box)

        # Auto-Tracking (Human Detection) Section
        ptz_layout.addSpacing(6)
        track_box = QFrame()
        track_box.setObjectName("toolCard")
        track_layout = QVBoxLayout(track_box)
        track_layout.setContentsMargins(8, 8, 8, 8)
        track_layout.setSpacing(4)

        self.lbl_track = QLabel(tr("track_title", "🤖 Rastreamento Humano:"))
        self.lbl_track.setObjectName("subTitle")
        track_layout.addWidget(self.lbl_track)

        self.chk_autotrack = QCheckBox(tr("track_chk", "Modo Automático (Pessoas)"))
        self.chk_autotrack.setToolTip("Modo Automático Inteligente:\nA câmera detecta pessoas automaticamente e gira os motores para acompanhá-las em tempo real.")
        self.chk_autotrack.toggled.connect(self.toggle_auto_tracking)
        track_layout.addWidget(self.chk_autotrack)
        ptz_layout.addWidget(track_box)

        # Recording Section (MP4, presets 15m to 24h or unlimited)
        ptz_layout.addSpacing(6)
        rec_box = QFrame()
        rec_box.setObjectName("toolCard")
        rec_layout = QVBoxLayout(rec_box)
        rec_layout.setContentsMargins(8, 8, 8, 8)
        rec_layout.setSpacing(5)

        self.lbl_rec_title = QLabel(tr("rec_title", "🎥 Gravação de Vídeo (MP4):"))
        self.lbl_rec_title.setObjectName("subTitle")
        rec_layout.addWidget(self.lbl_rec_title)

        dur_box = QHBoxLayout()
        dur_box.setSpacing(4)
        self.lbl_dur = QLabel(tr("rec_dur", "Duração:"))
        self.lbl_dur.setStyleSheet("font-size: 11px; color: #94a3b8;")
        dur_box.addWidget(self.lbl_dur)

        self.combo_rec_duration = QComboBox()
        self.combo_rec_duration.setObjectName("recDurationCombo")
        self.combo_rec_duration.setMinimumHeight(28)
        self.combo_rec_duration.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        self.combo_rec_duration.view().clicked.connect(
            lambda idx: (self.combo_rec_duration.setCurrentIndex(idx.row()), self.combo_rec_duration.hidePopup())
        )

        self.combo_rec_duration.setToolTip("Tempo de Gravação / Interrupção Programada:\nEscolha após quanto tempo interromper a gravação automaticamente, ou grave sem limite.")
        self.combo_rec_duration.currentIndexChanged.connect(self.on_rec_duration_changed)
        dur_box.addWidget(self.combo_rec_duration, 1)
        rec_layout.addLayout(dur_box)

        self.btn_record = QPushButton(tr("btn_start_rec", "🔴 Iniciar Gravação"))
        self.btn_record.setObjectName("btnRecord")
        self.btn_record.setMinimumHeight(32)
        self.btn_record.setToolTip("Gravação de Vídeo em Formato Universal MP4:\nGrava o vídeo diretamente na sua pasta Vídeos.\nAtalho: Tecla R")
        self.btn_record.clicked.connect(self.toggle_recording)
        rec_layout.addWidget(self.btn_record)

        self.chk_shutdown_after_rec = QCheckBox(tr("rec_chk_shutdown", "Desligar PC ao concluir"))
        self.chk_shutdown_after_rec.setToolTip("Desligar o Computador ao Concluir:\nQuando a gravação com tempo programado terminar (ex: 30m, 1h, 10h), o computador será desligado automaticamente.")
        rec_layout.addWidget(self.chk_shutdown_after_rec)

        self.lbl_rec_status = QLabel(tr("rec_status_saved", "📁 Salva na pasta Vídeos"))
        self.lbl_rec_status.setStyleSheet("color: #94a3b8; font-size: 11px;")
        self.lbl_rec_status.setWordWrap(True)
        rec_layout.addWidget(self.lbl_rec_status)
        ptz_layout.addWidget(rec_box)

        # Lighting & Night Vision Section (Modo Noturno vs Modo Iluminado)
        ptz_layout.addSpacing(6)
        light_box = QFrame()
        light_box.setObjectName("toolCard")
        light_layout = QVBoxLayout(light_box)
        light_layout.setContentsMargins(8, 8, 8, 8)
        light_layout.setSpacing(5)

        self.lbl_light_title = QLabel(tr("light_title", "💡 Iluminação & Visão Noturna:"))
        self.lbl_light_title.setObjectName("subTitle")
        light_layout.addWidget(self.lbl_light_title)

        light_seg_box = QFrame()
        light_seg_box.setObjectName("segmentedBox")
        seg_layout = QHBoxLayout(light_seg_box)
        seg_layout.setContentsMargins(2, 2, 2, 2)
        seg_layout.setSpacing(2)

        self.btn_light_night = QPushButton(tr("light_night", "🌙 Noturno"))
        self.btn_light_night.setCheckable(True)
        self.btn_light_night.setChecked(True)
        self.btn_light_night.setObjectName("segmentBtn")
        self.btn_light_night.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.btn_light_night.setToolTip("Modo Noturno (Infravermelho):\nVisão noturna infravermelha padrão em preto e branco, com a luz branca apagada.")
        self.btn_light_night.clicked.connect(lambda: self.set_light_mode("night"))

        self.btn_light_on = QPushButton(tr("light_flood", "💡 Iluminado"))
        self.btn_light_on.setCheckable(True)
        self.btn_light_on.setObjectName("segmentBtn")
        self.btn_light_on.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.btn_light_on.setToolTip("Modo Iluminado (Luz Acesa):\nAcende os holofotes de luz branca LED da câmera para iluminar o local e transmitir em cores.")
        self.btn_light_on.clicked.connect(lambda: self.set_light_mode("light"))

        seg_layout.addWidget(self.btn_light_night, 1)
        seg_layout.addWidget(self.btn_light_on, 1)
        light_layout.addWidget(light_seg_box)
        ptz_layout.addWidget(light_box)

        # Audio & Intercom Section (Ouvir som da câmera & Falar no microfone)
        ptz_layout.addSpacing(6)
        audio_box = QFrame()
        audio_box.setObjectName("toolCard")
        audio_layout = QVBoxLayout(audio_box)
        audio_layout.setContentsMargins(8, 8, 8, 8)
        audio_layout.setSpacing(5)

        self.lbl_audio_title = QLabel(tr("audio_title", "🎙️ Áudio & Interfone:"))
        self.lbl_audio_title.setObjectName("subTitle")
        audio_layout.addWidget(self.lbl_audio_title)

        audio_btn_box = QHBoxLayout()
        audio_btn_box.setSpacing(4)

        self.btn_listen_cam = QPushButton(tr("btn_listen", "🔇 Ouvir"))
        self.btn_listen_cam.setCheckable(True)
        self.btn_listen_cam.setObjectName("btnAudioListen")
        self.btn_listen_cam.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.btn_listen_cam.setMinimumHeight(32)
        self.btn_listen_cam.setToolTip("Ouvir Áudio da Câmera:\nTransmite o som do microfone da câmera em tempo real para as caixas de som do computador.")
        self.btn_listen_cam.toggled.connect(self.toggle_listen_camera)
        audio_btn_box.addWidget(self.btn_listen_cam, 1)

        self.btn_talk_cam = QPushButton(tr("btn_talk", "🎙️ Falar"))
        self.btn_talk_cam.setCheckable(True)
        self.btn_talk_cam.setObjectName("btnAudioTalk")
        self.btn_talk_cam.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.btn_talk_cam.setMinimumHeight(32)
        self.btn_talk_cam.setToolTip("Falar na Câmera (Intercomunicador):\nClique uma vez para ativar a fala ininterrupta no microfone do PC.\nSua voz sairá no alto-falante da câmera.\nClique novamente para desligar.")
        self.btn_talk_cam.toggled.connect(self.toggle_talking)
        audio_btn_box.addWidget(self.btn_talk_cam, 1)

        audio_layout.addLayout(audio_btn_box)

        self.lbl_audio_hint = QLabel(tr("audio_mic_ready", "🎤 Microfone do PC pronto"))
        self.lbl_audio_hint.setStyleSheet("color: #94a3b8; font-size: 11px;")
        self.lbl_audio_hint.setWordWrap(True)
        audio_layout.addWidget(self.lbl_audio_hint)
        ptz_layout.addWidget(audio_box)
        self.update_mic_hint()

        # Camera Reboot Section
        ptz_layout.addSpacing(4)
        self.btn_reboot = QPushButton(tr("btn_reboot", "🔄 Reiniciar Câmera"))
        self.btn_reboot.setObjectName("btnReboot")
        self.btn_reboot.setToolTip("Reiniciar Câmera:\nEnvia o comando de reinicialização para o hardware da câmera.")
        self.btn_reboot.clicked.connect(self.prompt_reboot_camera)
        ptz_layout.addWidget(self.btn_reboot)

        ptz_layout.addStretch()

        self.btn_hide_ptz = QPushButton(tr("btn_hide_controls", "Esconder Controles ▶"))
        self.btn_hide_ptz.setObjectName("linkButton")
        self.btn_hide_ptz.setToolTip("Ocultar painel lateral de controles")
        self.btn_hide_ptz.clicked.connect(self.toggle_ptz_panel)
        ptz_layout.addWidget(self.btn_hide_ptz)

        # Wrap in QScrollArea (prevents squishing or overlapping)
        self.scroll_ptz = QScrollArea()
        self.scroll_ptz.setObjectName("ptzScrollArea")
        self.scroll_ptz.setWidget(self.panel_ptz)
        self.scroll_ptz.setWidgetResizable(True)
        self.scroll_ptz.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_ptz.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_ptz.setFixedWidth(290)

        center_layout.addWidget(self.scroll_ptz)
        main_layout.addWidget(center_widget, stretch=1)

        # 5. Status Bar
        self.status_bar = QWidget()
        self.status_bar.setObjectName("statusBar")
        self.status_bar.setFixedHeight(28)
        stat_layout = QHBoxLayout(self.status_bar)
        stat_layout.setContentsMargins(12, 0, 12, 0)

        self.lbl_status = QLabel("🟢 Pronto")
        self.lbl_status.setObjectName("statusLabel")
        stat_layout.addWidget(self.lbl_status)

        self.lbl_cam_details = QLabel("")
        self.lbl_cam_details.setStyleSheet("color: #94a3b8; font-size: 11px;")
        stat_layout.addWidget(self.lbl_cam_details)

        # Gamepad connected badge
        self.lbl_gamepad = QLabel("")
        self.lbl_gamepad.setStyleSheet("color: #38bdf8; font-weight: bold; font-size: 11px;")
        stat_layout.addWidget(self.lbl_gamepad)

        stat_layout.addStretch()

        self.btn_show_ptz = QPushButton(tr("btn_show_controls", "◀ Mostrar Controles PTZ"))
        self.btn_show_ptz.setObjectName("linkButton")
        self.btn_show_ptz.setVisible(False)
        self.btn_show_ptz.clicked.connect(self.toggle_ptz_panel)
        stat_layout.addWidget(self.btn_show_ptz)

        self.lbl_keys = QLabel(tr("status_shortcuts", "Atalhos: [↑ ↓ ← →] ou Analógico | [2 Cliques / L2 / R2] Ampliar Lente | [Espaço / ○] Pausar | [S / △] Foto | [R] Gravar | [F11] Tela Cheia"))
        self.lbl_keys.setStyleSheet("color: #64748b; font-size: 11px;")
        self.lbl_keys.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        self.lbl_keys.setToolTip("Clique em '🎮 Dicas' no topo para ver o guia completo de controles e atalhos.")
        stat_layout.addWidget(self.lbl_keys)

        main_layout.addWidget(self.status_bar)

        if self.config.get("always_on_top", False):
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)

    def init_gamepad(self):
        """Initializes Gamepad / DualSense / Xbox controller worker."""
        self.gamepad_worker = GamepadWorker()
        self.gamepad_worker.connected.connect(self.on_gamepad_connected)
        self.gamepad_worker.disconnected.connect(self.on_gamepad_disconnected)
        self.gamepad_worker.move.connect(self.on_gamepad_move)
        self.gamepad_worker.ptz_stop.connect(self.cam_mgr.ptz_stop)
        self.gamepad_worker.action_pause.connect(self.toggle_camera_pause)
        self.gamepad_worker.action_zoom_lens.connect(self.video_widget.toggle_single_lens)
        self.gamepad_worker.action_snapshot.connect(self.take_snapshot)
        self.gamepad_worker.action_quality.connect(self.set_quality)
        self.gamepad_worker.action_layout.connect(self.toggle_layout_mode)
        self.gamepad_worker.start()

    def on_gamepad_connected(self, name: str):
        self.gamepad_name = name
        self.lbl_gamepad.setText(f"🎮 {name}")
        self.video_widget.show_toast(f"🎮 Controle Conectado: {name}!", 3000)

    def on_gamepad_disconnected(self):
        self.gamepad_name = ""
        self.lbl_gamepad.setText("")

    def on_gamepad_move(self, direction: str, speed: float):
        effective_speed = min(1.0, max(0.2, self.get_speed() * speed))
        self.cam_mgr.ptz_move(direction, effective_speed)

    def toggle_password_visibility(self):
        if self.edit_pass.echoMode() == QLineEdit.EchoMode.Password:
            self.edit_pass.setEchoMode(QLineEdit.EchoMode.Normal)
            self.btn_toggle_pw.setText("🔒")
        else:
            self.edit_pass.setEchoMode(QLineEdit.EchoMode.Password)
            self.btn_toggle_pw.setText("👁️")

    def toggle_layout_mode(self):
        cur = self.config.get("layout_mode", "vertical")
        new_mode = "side_by_side" if cur == "vertical" else "vertical"
        self.set_layout_mode(new_mode)

    def setup_ptz_button(self, btn: QPushButton, direction: str):
        def on_press():
            self.cam_mgr.ptz_move(direction, self.get_speed())

        def on_release():
            self.cam_mgr.ptz_stop()

        btn.pressed.connect(on_press)
        btn.released.connect(on_release)

    def get_speed(self) -> float:
        return max(0.1, self.slider_speed.value() / 10.0)

    def on_speed_changed(self, val):
        self.config["speed"] = val / 10.0
        self.save_config()

    def on_invert_toggled(self, checked):
        self.config["invert_x"] = checked
        self.cam_mgr.invert_x = checked
        self.save_config()

    def set_layout_mode(self, mode: str):
        self.config["layout_mode"] = mode
        self.save_config()

        self.btn_layout_vert.setChecked(mode == "vertical")
        self.btn_layout_side.setChecked(mode == "side_by_side")

        self.video_widget.set_layout_mode(mode)
        mode_label = "Lado a Lado (Horizontal)" if mode == "side_by_side" else "Normal (Vertical)"
        self.video_widget.show_toast(f"📐 Modo de visão: {mode_label}", duration_ms=3000)

    def toggle_ptz_panel(self):
        target = self.scroll_ptz if self.scroll_ptz else self.panel_ptz
        is_visible = target.isVisible()
        target.setVisible(not is_visible)
        self.btn_show_ptz.setVisible(is_visible)
        if hasattr(self, "btn_hide_ptz"):
            self.btn_hide_ptz.setText(tr("btn_show_controls") if is_visible else tr("btn_hide_controls"))
        if hasattr(self, "btn_show_ptz"):
            self.btn_show_ptz.setText(tr("btn_show_controls"))

    def toggle_settings_panel(self):
        self.panel_settings.setVisible(not self.panel_settings.isVisible())

    def toggle_always_on_top(self):
        is_checked = self.btn_top.isChecked()
        self.config["always_on_top"] = is_checked
        self.save_config()
        
        pos = self.pos()
        size = self.size()
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, is_checked)
        self.show()
        self.move(pos)
        self.resize(size)
        apply_windows_dark_titlebar(self)

    def set_quality(self, quality: str):
        if quality == self.config.get("quality"):
            return

        self.config["quality"] = quality
        self.save_config()

        self.btn_sd.setChecked(quality == "sub")
        self.btn_hd.setChecked(quality == "main")

        self.btn_sd.setEnabled(False)
        self.btn_hd.setEnabled(False)
        QTimer.singleShot(1400, lambda: (self.btn_sd.setEnabled(True), self.btn_hd.setEnabled(True)))

        token = self.cam_mgr.get_token_for_quality(quality)
        self.cam_mgr.set_profile_by_token(token)
        new_url = self.cam_mgr.get_rtsp_url(token)

        q_name = "HD Ultra (2304x2592)" if quality == "main" else "SD Fluido (640x720)"
        self.lbl_status.setText(f"🟡 Alternando para {q_name}...")
        self.video_widget.set_switching(True)

        if self.worker:
            self.worker.switch_url(new_url)
        else:
            self.start_stream(new_url)

    def auto_start(self):
        saved_ip = self.config.get("ip", "192.168.1.10")
        user = self.config.get("user", "admin")
        pwd = self.config.get("password", "")
        
        full_label = f"Câmera ({saved_ip})"
        self.combo_cams.addItem(full_label, saved_ip)
        self.combo_cams.setToolTip(full_label)
        self.connect_to_camera(saved_ip, self.config.get("port", 8899), user, pwd)
        QTimer.singleShot(2500, self.run_discovery)

    def run_discovery(self):
        self.btn_discover.setEnabled(False)
        self.lbl_status.setText("🔍 Varrendo rede local para detectar câmeras ICSee...")

        if self.discovery_worker and self.discovery_worker.isRunning():
            self.discovery_worker.wait()

        self.discovery_worker = DiscoveryWorker()
        self.discovery_worker.finished.connect(self.on_discovery_finished)
        self.discovery_worker.start()

    def on_discovery_finished(self, cameras):
        self.btn_discover.setEnabled(True)

        if not cameras:
            self.lbl_status.setText("Nenhuma nova câmera detectada automaticamente.")
            return

        current_ip = self.cam_mgr.ip or self.config.get("ip", "192.168.1.10")
        cameras.sort(key=lambda c: 0 if c['ip'] == current_ip else 1)

        self.combo_cams.blockSignals(True)
        self.combo_cams.clear()

        selected_idx = 0
        for i, cam in enumerate(cameras):
            ip = cam['ip']
            name = cam.get('name', f"ICSee ({ip})")
            self.combo_cams.addItem(name, ip)
            self.combo_cams.setItemData(i, name, Qt.ItemDataRole.ToolTipRole)
            if ip == current_ip:
                selected_idx = i

        self.combo_cams.setCurrentIndex(selected_idx)
        self.combo_cams.setToolTip(self.combo_cams.currentText())
        self.combo_cams.blockSignals(False)

        count = len(cameras)
        self.lbl_status.setText(f"🟢 {count} câmera(s) disponível(is) na rede.")

    def on_autostart_toggled(self, checked: bool):
        self.config["start_with_windows"] = checked
        self.save_config()
        set_windows_autostart(checked, self.config.get("start_minimized", False))
        state = "ativado" if checked else "desativado"
        self.video_widget.show_toast(f"⚙️ Iniciar com o Windows: {state}!", duration_ms=3000)

    def on_start_minimized_toggled(self, checked: bool):
        self.config["start_minimized"] = checked
        self.save_config()
        set_windows_autostart(self.config.get("start_with_windows", False), checked)
        state = "ativado" if checked else "desativado"
        self.video_widget.show_toast(f"⚙️ Iniciar Minimizado: {state}!", duration_ms=3000)

    def on_camera_selected(self, index):
        ip = self.combo_cams.currentData()
        self.combo_cams.setToolTip(self.combo_cams.currentText())
        if ip and ip != self.cam_mgr.ip:
            self.config["ip"] = ip
            self.edit_ip.setText(ip)
            self.save_config()
            self.connect_to_camera(ip, self.config.get("port", 8899), self.config.get("user", "admin"), self.config.get("password", ""))

    def apply_manual_settings(self):
        ip = self.edit_ip.text().strip()
        port = int(self.edit_port.text().strip() or "8899")
        user = self.edit_user.text().strip().lower()
        password = self.edit_pass.text().strip()
        autostart = self.chk_autostart.isChecked()
        start_minimized = self.chk_start_minimized.isChecked()

        self.config["ip"] = ip
        self.config["port"] = port
        self.config["user"] = user
        self.config["password"] = password
        self.config["start_with_windows"] = autostart
        self.config["start_minimized"] = start_minimized
        self.save_config()

        set_windows_autostart(autostart, start_minimized)
        self.video_widget.show_toast("💾 Configurações salvas com sucesso!", duration_ms=3000)

        self.is_camera_paused = False
        self.video_widget.set_paused(False)
        self.connect_to_camera(ip, port, user, password)
        self.panel_settings.setVisible(False)

    def prompt_reset_cache(self):
        reply = QMessageBox.question(
            self,
            tr("msg_reset_title"),
            tr("msg_reset_body"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            # 1. Reset configuration
            self.config = DEFAULT_CONFIG.copy()
            try:
                if CONFIG_FILE.exists():
                    CONFIG_FILE.unlink()
            except Exception as e:
                print(f"Erro ao remover arquivo de config: {e}")
            self.save_config()

            # 2. Reset autostart in registry
            set_windows_autostart(False, False)

            # 3. Update input fields in Settings UI
            self.edit_ip.setText(DEFAULT_CONFIG["ip"])
            self.edit_port.setText(str(DEFAULT_CONFIG["port"]))
            self.edit_user.setText(DEFAULT_CONFIG["user"])
            self.edit_pass.setText("")
            self.chk_invert_x.setChecked(DEFAULT_CONFIG["invert_x"])
            self.chk_autostart.setChecked(False)
            self.chk_start_minimized.setChecked(False)

            # 4. Stop any current stream and audio
            if hasattr(self, "audio_receiver") and self.audio_receiver:
                try:
                    self.audio_receiver.stop()
                except Exception:
                    pass
            if hasattr(self, "audio_talker") and self.audio_talker:
                try:
                    self.audio_talker.stop()
                except Exception:
                    pass
            if hasattr(self, "worker") and self.worker:
                try:
                    self.worker.stop()
                except Exception:
                    pass

            # 5. Reset camera combo
            self.combo_cams.blockSignals(True)
            self.combo_cams.clear()
            self.combo_cams.addItem("Câmera Padrão", DEFAULT_CONFIG["ip"])
            self.combo_cams.blockSignals(False)

            self.lbl_status.setText("🧹 Dados e cache apagados com sucesso.")
            self.video_widget.show_toast("🧹 Cache e credenciais apagados!", duration_ms=4000)
            QMessageBox.information(
                self,
                tr("msg_reset_title"),
                tr("msg_reset_success")
            )

    def on_language_changed(self, index: int):
        code = self.combo_lang.itemData(index)
        if code:
            set_language(code)
            self.config["lang"] = code
            self.save_config()
            self.update_ui_texts()
            self.video_widget.show_toast(f"🌐 {self.combo_lang.currentText()}", duration_ms=2500)

    def update_duration_combo(self):
        if not hasattr(self, "combo_rec_duration"):
            return
        cur_idx = self.combo_rec_duration.currentIndex()
        if cur_idx < 0:
            cur_idx = 0
        self.combo_rec_duration.blockSignals(True)
        self.combo_rec_duration.clear()
        
        m_str = tr("dur_min", "minutos")
        h_str = tr("dur_hour", "hora")
        hs_str = tr("dur_hours", "horas")
        
        self.combo_rec_duration.addItem(tr("dur_unlimited", "Sem limite (Manual)"), 0)
        self.combo_rec_duration.addItem(f"15 {m_str}", 15 * 60)
        self.combo_rec_duration.addItem(f"30 {m_str}", 30 * 60)
        self.combo_rec_duration.addItem(f"1 {h_str}", 60 * 60)
        self.combo_rec_duration.addItem(f"2 {hs_str}", 120 * 60)
        self.combo_rec_duration.addItem(f"4 {hs_str}", 240 * 60)
        self.combo_rec_duration.addItem(f"6 {hs_str}", 360 * 60)
        self.combo_rec_duration.addItem(f"8 {hs_str}", 480 * 60)
        self.combo_rec_duration.addItem(f"10 {hs_str} ({tr('rec_chk_shutdown', 'Desligar PC')})", 600 * 60)
        self.combo_rec_duration.addItem(f"12 {hs_str}", 720 * 60)
        self.combo_rec_duration.addItem(f"24 {hs_str}", 1440 * 60)
        
        if cur_idx < self.combo_rec_duration.count():
            self.combo_rec_duration.setCurrentIndex(cur_idx)
        self.combo_rec_duration.blockSignals(False)

    def update_ui_texts(self):
        self.setWindowTitle(tr("app_title"))
        w = self.width()
        is_compact = (w < 920)

        # Top Bar
        if hasattr(self, "btn_snapshot"):
            self.btn_snapshot.setText("📸" if is_compact else tr("btn_photo"))
            self.btn_snapshot.setToolTip(tr("tip_photo"))
        if hasattr(self, "btn_sd"):
            self.btn_sd.setText(tr("btn_sd"))
            self.btn_sd.setToolTip(tr("tip_sd"))
        if hasattr(self, "btn_hd"):
            self.btn_hd.setText(tr("btn_hd"))
            self.btn_hd.setToolTip(tr("tip_hd"))
        if hasattr(self, "btn_layout_vert"):
            self.btn_layout_vert.setText("⯀" if is_compact else tr("btn_normal"))
            self.btn_layout_vert.setToolTip(tr("tip_normal"))
        if hasattr(self, "btn_layout_side"):
            self.btn_layout_side.setText("⚏" if is_compact else tr("btn_side"))
            self.btn_layout_side.setToolTip(tr("tip_side"))
        if hasattr(self, "btn_top"):
            self.btn_top.setText("📌" if is_compact else tr("btn_pin"))
            self.btn_top.setToolTip(tr("tip_pin"))
        if hasattr(self, "btn_tips"):
            self.btn_tips.setText("🎮" if is_compact else tr("btn_tips"))
            self.btn_tips.setToolTip(tr("tip_tips"))
        if hasattr(self, "btn_discover"):
            self.btn_discover.setToolTip(tr("tip_discover"))

        # Settings Drawer (Row 1)
        if hasattr(self, "lbl_conn"):
            self.lbl_conn.setText(tr("sett_conn"))
        if hasattr(self, "lbl_ip"):
            self.lbl_ip.setText(tr("sett_ip"))
        if hasattr(self, "lbl_port"):
            self.lbl_port.setText(tr("sett_port"))
        if hasattr(self, "lbl_user"):
            self.lbl_user.setText(tr("sett_user"))
        if hasattr(self, "lbl_pass"):
            self.lbl_pass.setText(tr("sett_pass"))

        # Settings Drawer (Row 2)
        if hasattr(self, "lbl_pref"):
            self.lbl_pref.setText(tr("sett_options"))
        if hasattr(self, "chk_invert_x"):
            self.chk_invert_x.setText(tr("chk_invert_x"))
        if hasattr(self, "chk_autostart"):
            self.chk_autostart.setText(tr("chk_autostart"))
        if hasattr(self, "chk_start_minimized"):
            self.chk_start_minimized.setText(tr("chk_start_minimized"))
        if hasattr(self, "lbl_lang_setting"):
            self.lbl_lang_setting.setText(tr("lbl_language"))
        if hasattr(self, "btn_reset_cache"):
            self.btn_reset_cache.setText(tr("btn_reset_cache"))
        if hasattr(self, "btn_apply"):
            self.btn_apply.setText(tr("btn_save_connect"))

        # Right Panel - PTZ
        if hasattr(self, "lbl_ptz_title"):
            self.lbl_ptz_title.setText(tr("ptz_title"))
        if hasattr(self, "lbl_hint"):
            self.lbl_hint.setText(tr("ptz_hint"))
        if hasattr(self, "lbl_vel"):
            self.lbl_vel.setText(tr("speed_label"))
        if hasattr(self, "lbl_slow"):
            self.lbl_slow.setText(tr("speed_slow"))
        if hasattr(self, "lbl_fast"):
            self.lbl_fast.setText(tr("speed_fast"))
        if hasattr(self, "lbl_step"):
            self.lbl_step.setText(tr("step_title"))
        if hasattr(self, "btn_step_l"):
            self.btn_step_l.setText(tr("btn_step_left"))
        if hasattr(self, "btn_step_r"):
            self.btn_step_r.setText(tr("btn_step_right"))

        # Right Panel - Tracking
        if hasattr(self, "lbl_track"):
            self.lbl_track.setText(tr("track_title"))
        if hasattr(self, "chk_autotrack"):
            self.chk_autotrack.setText(tr("track_chk"))

        # Right Panel - Recording
        if hasattr(self, "lbl_rec_title"):
            self.lbl_rec_title.setText(tr("rec_title"))
        if hasattr(self, "lbl_dur"):
            self.lbl_dur.setText(tr("rec_dur"))
        if hasattr(self, "chk_shutdown_after_rec"):
            self.chk_shutdown_after_rec.setText(tr("rec_chk_shutdown"))
        if hasattr(self, "lbl_rec_status") and not (self.recorder and self.recorder.isRunning()):
            self.lbl_rec_status.setText(tr("rec_status_saved"))
        if hasattr(self, "btn_record"):
            if not self.recorder or not self.recorder.isRunning():
                self.btn_record.setText(tr("btn_start_rec"))
            else:
                self.btn_record.setText(tr("btn_stop_rec"))
        self.update_duration_combo()

        # Right Panel - Lighting
        if hasattr(self, "lbl_light_title"):
            self.lbl_light_title.setText(tr("light_title"))
        if hasattr(self, "btn_light_night"):
            self.btn_light_night.setText(tr("light_night"))
        if hasattr(self, "btn_light_on"):
            self.btn_light_on.setText(tr("light_flood"))

        # Right Panel - Audio
        if hasattr(self, "lbl_audio_title"):
            self.lbl_audio_title.setText(tr("audio_title"))
        if hasattr(self, "btn_listen_cam"):
            if not self.btn_listen_cam.isChecked():
                self.btn_listen_cam.setText(tr("btn_listen"))
            else:
                self.btn_listen_cam.setText(tr("btn_listening"))
        if hasattr(self, "btn_talk_cam"):
            if not self.btn_talk_cam.isChecked():
                self.btn_talk_cam.setText(tr("btn_talk"))
            else:
                self.btn_talk_cam.setText(tr("btn_talking"))
            self.btn_talk_cam.setToolTip(tr("tip_talk"))

        # Right Panel - Reboot & Hide
        if hasattr(self, "btn_reboot"):
            self.btn_reboot.setText(tr("btn_reboot"))
        if hasattr(self, "btn_hide_ptz"):
            vis = self.scroll_ptz.isVisible() if hasattr(self, "scroll_ptz") and self.scroll_ptz else True
            self.btn_hide_ptz.setText(tr("btn_hide_controls") if vis else tr("btn_show_controls"))
        if hasattr(self, "btn_show_ptz"):
            self.btn_show_ptz.setText(tr("btn_show_controls"))

        # Tips Panel
        if hasattr(self, "lbl_tips_head"):
            self.lbl_tips_head.setText(tr("tips_title"))
        if hasattr(self, "btn_close_tips"):
            self.btn_close_tips.setText(tr("tips_close"))
        if hasattr(self, "lbl_gp_t"):
            self.lbl_gp_t.setText(tr("tips_gamepad_title"))
        if hasattr(self, "lbl_kb_t"):
            self.lbl_kb_t.setText(tr("tips_kb_title"))
        if hasattr(self, "tips_gp_labels"):
            for lbl, key, default in self.tips_gp_labels:
                lbl.setText(tr(key, default))
        if hasattr(self, "tips_kb_labels"):
            for lbl, key, default in self.tips_kb_labels:
                lbl.setText(tr(key, default))

        # Status Bar
        if hasattr(self, "lbl_keys"):
            if is_compact:
                self.lbl_keys.setText(tr("status_shortcuts_compact"))
            else:
                self.lbl_keys.setText(tr("status_shortcuts"))
        if hasattr(self, "lbl_status") and (self.lbl_status.text().startswith("🟢") or self.lbl_status.text() == "🟢 Pronto"):
            self.lbl_status.setText(tr("status_ready"))

    def connect_to_camera(self, ip: str, port: int = 8899, user: Optional[str] = None, password: Optional[str] = None):
        if user is None:
            user = self.config.get("user", "admin")
        if password is None:
            password = self.config.get("password", "")

        self.video_widget.set_status(f"Conectando à câmera em {ip}...")
        self.lbl_status.setText(f"🟡 Conectando a {ip} com usuário '{user}'...")

        if self.connect_worker and self.connect_worker.isRunning():
            self.connect_worker.wait()

        self.connect_worker = ConnectWorker(self.cam_mgr, ip, port, user, password)
        self.connect_worker.finished.connect(self.on_connected_result)
        self.connect_worker.start()

    def on_connected_result(self, success: bool, ip: str):
        if not success:
            self.video_widget.set_status(f"Erro ao conectar com {ip}.\nVerifique se o usuário e senha estão corretos.")
            self.lbl_status.setText(f"🔴 Falha na autenticação com {ip}")
            return

        model = self.cam_mgr.device_info.get("Model", "ICSee")
        serial = self.cam_mgr.device_info.get("Serial", "")
        self.lbl_cam_details.setText(f"Modelo: {model} | Serial: {serial}")

        quality = self.config.get("quality", "sub")
        token = self.cam_mgr.get_token_for_quality(quality)
        self.cam_mgr.set_profile_by_token(token)
        rtsp_url = self.cam_mgr.get_rtsp_url(token)

        self.start_stream(rtsp_url)

        # Check active hardware auto-tracking status
        is_track = self.cam_mgr.get_auto_tracking()
        self.chk_autotrack.blockSignals(True)
        self.chk_autotrack.setChecked(is_track)
        self.chk_autotrack.blockSignals(False)
        self.video_widget.set_auto_tracking(is_track)
        self.is_auto_tracking = is_track

        # Check active lighting / night vision status
        light_mode = self.cam_mgr.get_light_mode()
        self.btn_light_night.blockSignals(True)
        self.btn_light_on.blockSignals(True)
        self.btn_light_night.setChecked(light_mode != "light")
        self.btn_light_on.setChecked(light_mode == "light")
        self.btn_light_night.blockSignals(False)
        self.btn_light_on.blockSignals(False)

        # Ensure camera is in active streaming state
        self.is_camera_paused = False
        self.video_widget.set_paused(False)

    def start_stream(self, rtsp_url: str):
        if self.worker:
            self.worker.stop()
            self.worker = None

        self.worker = VideoWorker(rtsp_url)
        self.worker.frame_ready.connect(self.on_frame_ready)
        self.worker.fps_updated.connect(self.on_fps_updated)
        self.worker.status_changed.connect(self.on_worker_status)
        self.worker.start()

    def on_frame_ready(self, q_img: QImage, w: int, h: int, raw_frame: Optional[np.ndarray] = None):
        self.last_frame_time = time.time()
        if self.is_camera_paused:
            return

        pixmap = QPixmap.fromImage(q_img)
        self.current_w = w
        self.current_h = h
        self.video_widget.update_frame(pixmap, self.current_fps, w, h)
        self.last_qimage = q_img

        # Feed frame into background video recorder if active (pure contiguous NumPy BGR)
        if self.recorder and self.recorder.isRunning() and not self.is_camera_paused and raw_frame is not None:
            try:
                rf_h, rf_w = raw_frame.shape[:2]
                rf_h2 = rf_h // 2
                if self.video_widget.single_lens == "top":
                    rec_frame = np.ascontiguousarray(raw_frame[0:rf_h2, :])
                elif self.video_widget.single_lens == "bottom":
                    rec_frame = np.ascontiguousarray(raw_frame[rf_h2:rf_h, :])
                elif self.video_widget.layout_mode == "side_by_side":
                    top_part = raw_frame[0:rf_h2, :]
                    bottom_part = raw_frame[rf_h2:rf_h, :]
                    rec_frame = np.ascontiguousarray(np.hstack((top_part, bottom_part)))
                else:
                    rec_frame = np.ascontiguousarray(raw_frame)
                self.recorder.add_frame(rec_frame)
            except Exception as e:
                print(f"[Recorder] Frame processing error: {e}")

    @pyqtSlot(float)
    def on_fps_updated(self, fps: float):
        self.current_fps = fps

    @pyqtSlot(str)
    def on_worker_status(self, status: str):
        if status == "connected":
            self.video_widget.set_switching(False)
            q_label = "HD Ultra" if self.current_w > 1000 else "SD Fluido"
            res_str = f" • {self.current_w}x{self.current_h} ({q_label})" if self.current_w > 0 else ""
            self.lbl_status.setText(f"🟢 Vídeo conectado{res_str}")
        elif status == "switching":
            self.video_widget.set_switching(True)
            self.lbl_status.setText("🔄 Sincronizando vídeo...")
        elif status == "connecting":
            self.lbl_status.setText("🟡 Conectando fluxo de vídeo...")
            if not self.video_widget.raw_pixmap:
                self.video_widget.set_status("Carregando fluxo de vídeo...")
        elif status == "disconnected":
            self.lbl_status.setText("🔴 Vídeo desconectado")
            self.video_widget.set_status("Conexão perdida. Tentando reconectar...")
        elif status == "error":
            self.lbl_status.setText("⚠️ Erro de leitura do fluxo")

    def toggle_tips_panel(self):
        """Toggles the collapsible Control Tips & Shortcuts panel."""
        if hasattr(self, "panel_tips"):
            self.panel_tips.setVisible(not self.panel_tips.isVisible())

    def toggle_camera_pause(self):
        """Toggles live camera playback Pause and Resume with feedback and 3s toast."""
        self.cam_mgr.ptz_stop()
        if not self.is_camera_paused:
            self.is_camera_paused = True
            self.video_widget.set_paused(True)
            if self.recorder and self.recorder.isRunning():
                self.recorder.set_paused(True)
            self.btn_stop.setText("▶")
            self.btn_stop.setToolTip("Retomar Câmera (Clique para retomar a transmissão ao vivo)\nAtalho: Barra de Espaço ou Círculo (○) / B no controle")
            self.btn_stop.setStyleSheet("background-color: #eab308; border: 2px solid #fde047; color: #0f172a; font-weight: bold;")
            self.video_widget.show_toast("⏸️ Câmera Pausada!\nClique no botão ▶ ou aperte Espaço para retomar.", duration_ms=3000)
            self.lbl_status.setText("⏸️ Câmera pausada")
        else:
            self.is_camera_paused = False
            self.video_widget.set_paused(False)
            if self.recorder and self.recorder.isRunning():
                self.recorder.set_paused(False)
            self.btn_stop.setText("⏸")
            self.btn_stop.setToolTip("Pausar Câmera (Clique para pausar a transmissão ao vivo)\nAtalho: Barra de Espaço ou Círculo (○) / B no controle")
            self.btn_stop.setStyleSheet("")
            self.video_widget.show_toast("▶️ Câmera Iniciada!\nTransmissão ao vivo retomada.", duration_ms=3000)
            self.lbl_status.setText("🟢 Vídeo ao vivo")

    def toggle_auto_tracking(self, checked: bool):
        """Toggles native humanoid automatic detection and tracking on camera hardware asynchronously."""
        self.is_auto_tracking = checked
        self.video_widget.set_auto_tracking(checked)
        self.lbl_status.setText("🤖 Atualizando rastreamento..." if checked else "🟢 Desativando rastreamento...")

        if hasattr(self, "track_worker") and self.track_worker and self.track_worker.isRunning():
            self.track_worker.wait()

        self.track_worker = AutoTrackWorker(self.cam_mgr, checked)
        self.track_worker.finished.connect(self.on_auto_track_finished)
        self.track_worker.start()

    def on_auto_track_finished(self, success: bool, enabled: bool):
        if enabled:
            self.video_widget.show_toast("🤖 Modo Automático Ativado!\nA câmera agora detecta e segue pessoas em tempo real.", duration_ms=3000)
            self.lbl_status.setText("🤖 Modo Automático (Rastreamento Ativo)")
        else:
            self.cam_mgr.ptz_stop()
            self.video_widget.show_toast("🤖 Modo Automático Desativado!\nControle manual restabelecido.", duration_ms=3000)
            self.lbl_status.setText("🟢 Controle Manual")

    def toggle_recording(self):
        """Starts or stops MP4 video recording directly into the Videos folder."""
        if hasattr(self, "watchdog_timer") and self.watchdog_timer.isActive():
            self.watchdog_timer.stop()
        if self.recorder and self.recorder.isRunning():
            self.btn_record.setText("⏳ Interrompendo gravação...")
            self.btn_record.setStyleSheet("background-color: #d97706; border-color: #f59e0b; font-weight: bold; color: white;")
            self.btn_record.setEnabled(False)
            self.video_widget.show_toast("⏹️ Interrompendo gravação e salvando arquivo...", duration_ms=2500)
            self.recorder.stop_recording()
        else:
            try:
                if not self.video_widget.display_pixmap or self.video_widget.display_pixmap.isNull():
                    self.video_widget.show_toast("⚠️ Aguarde o vídeo carregar para iniciar a gravação.", duration_ms=3000)
                    return

                videos_dir = Path.home() / "Videos"
                if not videos_dir.exists():
                    videos_dir.mkdir(parents=True, exist_ok=True)

                mode_tag = "LadoALado" if self.video_widget.layout_mode == "side_by_side" else "Normal"
                if self.video_widget.single_lens == "top":
                    mode_tag = "LenteSuperior"
                elif self.video_widget.single_lens == "bottom":
                    mode_tag = "LenteInferior"

                timestamp = time.strftime('%Y-%m-%d_%H-%M-%S')
                filename = f"Gravacao_ICSee_{mode_tag}_{timestamp}.mp4"
                filepath = str(videos_dir / filename)

                if self.video_widget.single_lens in ("top", "bottom"):
                    w = self.current_w
                    h = self.current_h // 2
                elif self.video_widget.layout_mode == "side_by_side":
                    w = self.current_w * 2
                    h = self.current_h // 2
                else:
                    w = self.current_w
                    h = self.current_h

                # Ensure dimensions are valid and even for video encoding
                w = max(320, w if (w % 2 == 0) else (w - 1))
                h = max(240, h if (h % 2 == 0) else (h - 1))

                fps = self.current_fps if self.current_fps >= 10.0 else 20.0
                max_sec = self.combo_rec_duration.currentData() or 0

                dur_label = self.combo_rec_duration.currentText()
                self.recorder = VideoRecorder(filepath, w, h, fps, max_sec)
                self.recorder.progress_updated.connect(self.on_recording_progress)
                self.recorder.recording_finished.connect(self.on_recording_finished)
                self.recorder.recording_error.connect(self.on_recording_error)
                self.recorder.start()

                self.btn_record.setEnabled(True)
                self.btn_record.setText(tr("btn_stop_rec", "⏹️ Parar Gravação"))
                self.btn_record.setStyleSheet("background-color: #dc2626; border-color: #ef4444; font-weight: bold; color: white;")
                self.btn_record.setToolTip("Interromper Gravação Agora:\nClique aqui para parar a gravação e salvar o vídeo imediatamente.")
                self.combo_rec_duration.setEnabled(False)
                self.video_widget.set_recording(True, "00:00:00")
                shutdown_hint = "\n(PC será desligado ao concluir)" if (self.chk_shutdown_after_rec.isChecked() and max_sec > 0) else ""
                self.video_widget.show_toast(f"🎥 Gravação de vídeo iniciada!\nSalvo em Vídeos (Duração: {dur_label}){shutdown_hint}", duration_ms=3000)
            except Exception as e:
                self.on_recording_error(str(e))

    @pyqtSlot(str)
    def on_recording_error(self, err_msg: str):
        """Safely handles recording background error without crashing the application."""
        self.btn_record.setEnabled(True)
        self.btn_record.setText(tr("btn_start_rec", "🔴 Iniciar Gravação"))
        self.btn_record.setStyleSheet("")
        self.btn_record.setToolTip("Gravação de Vídeo em Formato Universal MP4:\nGrava o vídeo diretamente na sua pasta Vídeos.\nAtalho: Tecla R")
        self.combo_rec_duration.setEnabled(True)
        self.video_widget.set_recording(False)
        self.lbl_rec_status.setText("❌ Erro na gravação")
        self.lbl_status.setText(f"⚠️ Erro ao gravar: {err_msg}")
        self.video_widget.show_toast(f"❌ Erro na gravação de vídeo:\n{err_msg}", duration_ms=3000)

    def on_rec_duration_changed(self, index: int):
        dur_text = self.combo_rec_duration.currentText()
        max_sec = self.combo_rec_duration.currentData()
        if max_sec and max_sec > 0:
            self.video_widget.show_toast(f"⏱️ Tempo de gravação definido:\n{dur_text}", duration_ms=2500)
            self.lbl_rec_status.setText(f"⏱️ {dur_text}")
        else:
            self.video_widget.show_toast("⏱️ Modo de gravação:\nSem limite (Interromper manualmente)", duration_ms=2500)
            self.lbl_rec_status.setText("📁 Gravar sem limite (Manual)")

    @pyqtSlot(int, int)
    def on_recording_progress(self, elapsed_sec: int, max_sec: int):
        el_str = time.strftime('%H:%M:%S', time.gmtime(elapsed_sec))
        if max_sec > 0:
            max_str = time.strftime('%H:%M:%S', time.gmtime(max_sec))
            txt = f"{el_str} / {max_str}"
        else:
            txt = f"{el_str} (Manual)"

        self.video_widget.set_recording(True, el_str)
        self.lbl_rec_status.setText(f"REC ● {txt}")

    @pyqtSlot(str, int)
    def on_recording_finished(self, filepath: str, elapsed_sec: int):
        filename = Path(filepath).name
        self.btn_record.setEnabled(True)
        self.btn_record.setText(tr("btn_start_rec", "🔴 Iniciar Gravação"))
        self.btn_record.setStyleSheet("")
        self.btn_record.setToolTip("Gravação de Vídeo em Formato Universal MP4:\nGrava o vídeo diretamente na sua pasta Vídeos.\nAtalho: Tecla R")
        self.combo_rec_duration.setEnabled(True)
        self.video_widget.set_recording(False)
        self.lbl_rec_status.setText(f"📁 Salvo: {filename}")
        self.lbl_status.setText(f"🎥 Gravação salva: {filename}")

        should_shutdown = self.chk_shutdown_after_rec.isChecked() and (self.combo_rec_duration.currentData() or 0) > 0
        if should_shutdown:
            self.video_widget.show_toast("⏹️ Gravação salva!\n⚠️ O computador será desligado em 60 segundos.", duration_ms=3000)
            self._schedule_pc_shutdown()
        else:
            self.video_widget.show_toast(f"⏹️ Gravação salva na pasta Vídeos!\n{filename}", duration_ms=3000)

    def _schedule_pc_shutdown(self):
        """Initiates safe Windows shutdown with a real-time countdown dialog."""
        try:
            import subprocess
            subprocess.run(["shutdown", "/s", "/t", "60", "/c", "Gravação ICSee concluída. O computador será desligado em 60 segundos."], check=False)

            dlg = ShutdownDialog(self, countdown_sec=60)
            dlg.exec()

            if dlg.cancelled:
                subprocess.run(["shutdown", "/a"], check=False)
                self.video_widget.show_toast("🛑 Desligamento do computador cancelado!", duration_ms=3000)
            elif dlg.immediate:
                subprocess.run(["shutdown", "/s", "/t", "0"], check=False)
        except Exception as e:
            print(f"[Shutdown] Error: {e}")

    def set_light_mode(self, mode: str):
        """Switches lighting between Modo Noturno (IR) and Modo Iluminado (White Light)."""
        self.btn_light_night.setChecked(mode == "night")
        self.btn_light_on.setChecked(mode == "light")

        if hasattr(self, "light_worker") and self.light_worker and self.light_worker.isRunning():
            self.light_worker.wait()

        label = "Modo Iluminado (Luz Acesa)" if mode == "light" else "Modo Noturno (Infravermelho)"
        self.video_widget.show_toast(f"💡 Ativando {label}...", duration_ms=2500)

        self.light_worker = LightWorker(self.cam_mgr, mode)
        self.light_worker.finished.connect(self.on_light_mode_finished)
        self.light_worker.start()

    def on_light_mode_finished(self, success: bool, mode: str):
        if mode == "light":
            self.video_widget.show_toast("💡 Modo Iluminado Ativo!\nLuz branca da câmera acesa.", duration_ms=3000)
            self.lbl_status.setText("💡 Modo Iluminado (Luz Acesa)")
        else:
            self.video_widget.show_toast("🌙 Modo Noturno Ativo!\nInfravermelho ativado (luz apagada).", duration_ms=3000)
            self.lbl_status.setText("🌙 Modo Noturno (Infravermelho)")

    def update_mic_hint(self):
        """Displays detected PC microphone in the audio hint label."""
        try:
            default_mic = QMediaDevices.defaultAudioInput()
            name = default_mic.description() if default_mic else "Microfone Padrão"
            if len(name) > 28:
                name = name[:26] + "..."
            self.lbl_audio_hint.setText(f"🎤 {name}")
        except Exception:
            self.lbl_audio_hint.setText("🎤 Microfone do PC pronto")

    def toggle_listen_camera(self, checked: bool):
        """Toggles listening to live camera microphone audio through PC speakers."""
        self.is_listening_audio = checked
        if checked:
            self.btn_listen_cam.setText(tr("btn_listening", "🔊 Ouvindo"))
            self.btn_listen_cam.setStyleSheet("background-color: #0284c7; border-color: #38bdf8; color: #ffffff; font-weight: bold;")
            self.video_widget.show_toast("🔊 Som da Câmera Ativado!\nOuvindo áudio ao vivo do ambiente.", duration_ms=2500)
            self.lbl_status.setText("🔊 Áudio da câmera ativo")

            if self.audio_receiver and self.audio_receiver.isRunning():
                self.audio_receiver.stop()

            self.audio_receiver = CameraAudioReceiver(self.cam_mgr.ip, 554, self.cam_mgr.user, self.cam_mgr.password)
            self.audio_receiver.status_changed.connect(self.on_audio_receiver_status)
            self.audio_receiver.start()
        else:
            self.btn_listen_cam.setText(tr("btn_listen", "🔇 Ouvir"))
            self.btn_listen_cam.setStyleSheet("")
            self.video_widget.show_toast("🔇 Som da Câmera Desativado.", duration_ms=2500)
            self.lbl_status.setText("🟢 Vídeo ao vivo")

            if self.audio_receiver:
                receiver = self.audio_receiver
                self.audio_receiver = None
                try:
                    receiver.status_changed.disconnect()
                except Exception:
                    pass
                receiver.stop()

    def on_audio_receiver_status(self, status: str):
        if status == "playing":
            self.lbl_status.setText("🔊 Áudio da câmera conectado (Ao vivo)")
        elif status == "error":
            self.lbl_status.setText("⚠️ Erro ao receber áudio da câmera")
            if self.btn_listen_cam.isChecked():
                self.btn_listen_cam.blockSignals(True)
                self.btn_listen_cam.setChecked(False)
                self.btn_listen_cam.setText(tr("btn_listen", "🔇 Ouvir"))
                self.btn_listen_cam.setStyleSheet("")
                self.btn_listen_cam.blockSignals(False)
                if self.audio_receiver:
                    receiver = self.audio_receiver
                    self.audio_receiver = None
                    try:
                        receiver.status_changed.disconnect()
                    except Exception:
                        pass
                    receiver.stop()

    def toggle_talking(self, checked: bool):
        """1-click continuous microphone transmission toggle to camera speaker."""
        self.is_talking = checked
        if checked:
            # Acoustic feedback prevention: mute camera listening while speaking
            if self.audio_receiver and self.audio_receiver.isRunning():
                self.audio_receiver.set_muted(True)

            self.btn_talk_cam.setText(tr("btn_talking", "🔴 Falando"))
            self.btn_talk_cam.setStyleSheet("background-color: #dc2626; border: 1px solid #ef4444; color: #ffffff; font-weight: bold;")
            self.video_widget.show_toast("🎙️ Microfone Ativado!\nFale normalmente no PC. Sua voz está saindo na câmera.\nClique no botão para desligar.", duration_ms=3000)
            self.lbl_status.setText("🎙️ Transmitindo áudio para a câmera (Ao vivo)...")

            if self.talk_worker and self.talk_worker.isRunning():
                self.talk_worker.stop()

            self.talk_worker = CameraTalkWorker(self.cam_mgr.ip, 34567, self.cam_mgr.user, self.cam_mgr.password)
            self.talk_worker.status_changed.connect(self.on_talk_worker_status)
            self.talk_worker.start()
        else:
            self.btn_talk_cam.setText(tr("btn_talk", "🎙️ Falar"))
            self.btn_talk_cam.setStyleSheet("")

            if self.talk_worker:
                worker = self.talk_worker
                self.talk_worker = None
                try:
                    worker.status_changed.disconnect()
                except Exception:
                    pass
                worker.stop()

            # Restore camera audio listening if was active
            if self.audio_receiver and self.audio_receiver.isRunning():
                self.audio_receiver.set_muted(False)

            self.video_widget.show_toast("🎙️ Microfone Desativado.", duration_ms=2000)
            self.lbl_status.setText("🟢 Vídeo ao vivo")

    def on_talk_worker_status(self, status: str):
        if status == "talking":
            self.lbl_status.setText("🎙️ Microfone ativo: sua voz está saindo no alto-falante da câmera!")
        elif status == "error":
            self.lbl_status.setText("⚠️ Erro na comunicação com alto-falante da câmera")
            self.btn_talk_cam.setChecked(False)

    def prompt_reboot_camera(self):
        """Asks for confirmation with modern dark dialog before sending hardware reboot command."""
        dlg = RebootDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.video_widget.show_toast("🔄 Reiniciando câmera... Aguarde a reinicialização.", duration_ms=3000)
            self.lbl_status.setText("🟡 Câmera reiniciando... Reconectando em instantes.")
            self.video_widget.set_switching(True)

            self.reboot_worker = RebootWorker(self.cam_mgr)
            self.reboot_worker.finished.connect(self.on_reboot_sent)
            self.reboot_worker.start()

    def on_reboot_sent(self, success: bool):
        if self.worker:
            self.worker.stop()
            self.worker = None

        self.video_widget.set_status("🔄 Câmera reiniciando...\nTentando reconectar automaticamente...")
        QTimer.singleShot(25000, self.auto_start)

    def _check_stream_health(self):
        """Auto-recovers video stream if frames stop arriving while not paused."""
        if self.is_camera_paused:
            return
        if not self.worker or not self.worker.isRunning():
            return

        now = time.time()
        if self.last_frame_time > 0 and (now - self.last_frame_time) > 4.5:
            print("[Watchdog] Stream stalled. Auto-recovering...")
            self.last_frame_time = now
            token = self.cam_mgr.get_token_for_quality(self.config.get("quality", "sub"))
            rtsp_url = self.cam_mgr.get_rtsp_url(token)
            if self.worker:
                self.worker.switch_url(rtsp_url)

    def take_snapshot(self):
        """
        Instant 1-Click snapshot.
        Saves directly to Pictures/Imagens in 1 click (Side-by-Side or Normal view),
        triggers a camera shutter flash, and displays a real-time toast for 3 seconds.
        """
        if not self.video_widget.display_pixmap or self.video_widget.display_pixmap.isNull():
            self.video_widget.show_toast("⚠️ Aguarde o vídeo carregar para capturar.", duration_ms=3000)
            return

        pictures_dir = Path.home() / "Pictures"
        if not pictures_dir.exists():
            pictures_dir.mkdir(parents=True, exist_ok=True)

        mode_tag = "LadoALado" if self.config.get("layout_mode") == "side_by_side" else "Normal"
        timestamp = time.strftime('%Y-%m-%d_%H-%M-%S')
        filename = f"Captura_ICSee_{mode_tag}_{timestamp}.png"
        filepath = pictures_dir / filename

        # Camera shutter visual flash effect
        self.video_widget.trigger_flash()

        # Save directly in 1 click
        img_to_save = self.video_widget.display_pixmap.toImage()
        success = img_to_save.save(str(filepath), "PNG")

        if success:
            self.last_saved_path = str(filepath)
            msg = f"📸 Captura salva na pasta Imagens: {filename}"
            self.lbl_status.setText(msg)
            toast_text = f"📸 Captura de tela salva na pasta Imagens!\n{filename}"
            self.video_widget.show_toast(toast_text, duration_ms=3000)
        else:
            self.video_widget.show_toast("❌ Erro ao salvar captura de tela.", duration_ms=3000)

    # Keyboard Controls for PTZ Navigation, Recording and Pause with 8-way diagonal steering
    def _update_keyboard_ptz(self):
        want_up = Qt.Key.Key_Up in self.active_keys
        want_down = Qt.Key.Key_Down in self.active_keys
        want_left = Qt.Key.Key_Left in self.active_keys
        want_right = Qt.Key.Key_Right in self.active_keys

        self.btn_up.setDown(want_up)
        self.btn_down.setDown(want_down)
        self.btn_left.setDown(want_left)
        self.btn_right.setDown(want_right)

        if not self.active_keys:
            self.cam_mgr.ptz_stop()
            return

        speed = self.get_speed()
        if want_up and want_left:
            self.cam_mgr.ptz_move("left_up", speed)
        elif want_up and want_right:
            self.cam_mgr.ptz_move("right_up", speed)
        elif want_down and want_left:
            self.cam_mgr.ptz_move("left_down", speed)
        elif want_down and want_right:
            self.cam_mgr.ptz_move("right_down", speed)
        elif want_up:
            self.cam_mgr.ptz_move("up", speed)
        elif want_down:
            self.cam_mgr.ptz_move("down", speed)
        elif want_left:
            self.cam_mgr.ptz_move("left", speed)
        elif want_right:
            self.cam_mgr.ptz_move("right", speed)

    def toggle_fullscreen(self):
        """Toggles between normal window and full screen mode covering the Windows taskbar."""
        if self.isFullScreen():
            if getattr(self, "_was_maximized_before_fs", False):
                self.showMaximized()
            else:
                self.showNormal()
            self.video_widget.show_toast("🖥️ Modo Janela restaurado", duration_ms=2000)
        else:
            self._was_maximized_before_fs = self.isMaximized()
            # In Windows, clearing maximized state before showFullScreen ensures taskbar is completely covered
            if self.isMaximized():
                self.showNormal()
            self.setWindowState(Qt.WindowState.WindowFullScreen)
            self.showFullScreen()
            self.video_widget.show_toast("🖥️ Tela Cheia (F11 para sair)", duration_ms=2500)
        apply_windows_dark_titlebar(self)

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        if event.isAutoRepeat():
            return super().keyPressEvent(event)

        # F11 Fullscreen always operates globally, covering Windows taskbar
        if key == Qt.Key.Key_F11:
            self.toggle_fullscreen()
            return

        # Do not intercept space bar or hotkeys if settings panel is open
        if hasattr(self, "panel_settings") and self.panel_settings and not self.panel_settings.isHidden():
            return super().keyPressEvent(event)

        # Do not intercept if user has focus on any input widget
        focused = QApplication.focusWidget()
        if focused and isinstance(focused, (QLineEdit, QComboBox, QCheckBox)):
            return super().keyPressEvent(event)

        if key in [Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_Left, Qt.Key.Key_Right]:
            self.active_keys.add(key)
            self._update_keyboard_ptz()
        elif key == Qt.Key.Key_Space:
            self.toggle_camera_pause()
        elif key == Qt.Key.Key_R:
            self.toggle_recording()
        elif key == Qt.Key.Key_S:
            self.take_snapshot()
        elif key == Qt.Key.Key_T:
            self.btn_top.setChecked(not self.btn_top.isChecked())
            self.toggle_always_on_top()
        else:
            super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent):
        key = event.key()
        if event.isAutoRepeat():
            return super().keyReleaseEvent(event)

        if key in [Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_Left, Qt.Key.Key_Right]:
            self.active_keys.discard(key)
            self._update_keyboard_ptz()
        else:
            super().keyReleaseEvent(event)

    def apply_theme(self):
        style = """
        QMainWindow {
            background-color: #0f172a;
        }
        QMenuBar {
            background-color: #1e293b;
            color: #f8fafc;
            border: none;
            height: 0px;
        }
        QWidget {
            color: #f8fafc;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 13px;
        }
        /* Rich Flyout Tooltips */
        QToolTip {
            background-color: #1e293b;
            color: #f8fafc;
            border: 1px solid #38bdf8;
            border-radius: 6px;
            padding: 6px 10px;
            font-size: 12px;
            font-family: 'Segoe UI', sans-serif;
        }
        #topBar {
            background-color: #1e293b;
            border-bottom: 1px solid #334155;
        }
        #appTitle {
            font-size: 14px;
            font-weight: bold;
            color: #38bdf8;
            margin-right: 2px;
        }
        #settingsPanel {
            background-color: #1e293b;
            border-bottom: 1px solid #475569;
        }
        #tipsPanel {
            background-color: #1e293b;
            border-bottom: 1px solid #475569;
        }
        #tipCard {
            background-color: #0f172a;
            border: 1px solid #334155;
            border-radius: 6px;
        }
        #toolCard {
            background-color: #0f172a;
            border: 1px solid #334155;
            border-radius: 6px;
        }
        #ptzScrollArea {
            background-color: #1e293b;
            border: none;
            border-left: 1px solid #334155;
        }
        #ptzScrollArea QScrollBar:vertical {
            background: #0f172a;
            width: 8px;
            margin: 0px;
            border-radius: 4px;
        }
        #ptzScrollArea QScrollBar::handle:vertical {
            background: #334155;
            min-height: 25px;
            border-radius: 4px;
        }
        #ptzScrollArea QScrollBar::handle:vertical:hover {
            background: #475569;
        }
        #ptzScrollArea QScrollBar::add-line:vertical,
        #ptzScrollArea QScrollBar::sub-line:vertical {
            height: 0px;
        }
        #ptzPanel {
            background-color: #1e293b;
            border: none;
        }
        #statusBar {
            background-color: #090d16;
            border-top: 1px solid #1e293b;
        }
        #statusLabel {
            font-weight: bold;
            color: #38bdf8;
        }
        #sectionTitle {
            font-size: 14px;
            font-weight: bold;
            color: #f1f5f9;
        }
        #subTitle {
            font-size: 12px;
            font-weight: bold;
            color: #cbd5e1;
        }
        #hintText {
            font-size: 11px;
            color: #94a3b8;
        }
        QPushButton {
            background-color: #334155;
            color: #f8fafc;
            border: 1px solid #475569;
            border-radius: 6px;
            padding: 5px 10px;
            font-weight: 500;
        }
        QPushButton:hover {
            background-color: #475569;
            border-color: #64748b;
        }
        QPushButton:pressed {
            background-color: #0284c7;
            border-color: #38bdf8;
        }
        #compactBtn {
            padding: 5px 8px;
            min-width: 28px;
        }
        #primaryButton {
            background-color: #0284c7;
            border-color: #0369a1;
            font-weight: bold;
        }
        #primaryButton:hover {
            background-color: #0369a1;
        }
        #btnResetCache {
            background-color: #334155;
            border: 1px solid #475569;
            color: #cbd5e1;
            font-weight: bold;
            padding: 5px 12px;
        }
        #btnResetCache:hover {
            background-color: #dc2626;
            border-color: #ef4444;
            color: #ffffff;
        }
        #btnRecord {
            background-color: #0284c7;
            border-color: #0369a1;
            font-weight: bold;
        }
        #btnRecord:hover {
            background-color: #0369a1;
        }
        #btnToggle:checked {
            background-color: #0284c7;
            border-color: #38bdf8;
            color: white;
        }
        #iconBtn {
            background-color: #1e293b;
            border: 1px solid #334155;
            border-radius: 5px;
            padding: 2px;
            font-size: 13px;
        }
        #iconBtn:hover {
            background-color: #334155;
            border-color: #0284c7;
        }
        /* Segmented Box for Quality & Layout */
        #segmentedBox {
            background-color: #0f172a;
            border: 1px solid #334155;
            border-radius: 6px;
        }
        #segmentBtn {
            background-color: transparent;
            border: none;
            border-radius: 4px;
            padding: 4px 4px;
            font-weight: bold;
            color: #94a3b8;
            font-size: 11px;
        }
        #segmentBtn:hover {
            background-color: #1e293b;
            color: #f8fafc;
        }
        #segmentBtn:checked {
            background-color: #0284c7;
            color: #ffffff;
        }
        #segmentBtn:disabled {
            color: #64748b;
        }
        #linkButton {
            background: transparent;
            border: none;
            color: #38bdf8;
            text-decoration: underline;
            padding: 2px 4px;
        }
        #linkButton:hover {
            color: #7dd3fc;
        }
        /* D-Pad Buttons */
        #dpadBtn {
            background-color: #1e293b;
            border: 2px solid #475569;
            border-radius: 8px;
            font-size: 18px;
            width: 48px;
            height: 48px;
            color: #38bdf8;
        }
        #dpadBtn:hover {
            background-color: #334155;
            border-color: #38bdf8;
        }
        #dpadBtn:pressed {
            background-color: #0284c7;
            color: #ffffff;
            border-color: #bae6fd;
        }
        #pauseBtn {
            background-color: #1e293b;
            border: 2px solid #475569;
            border-radius: 8px;
            font-size: 16px;
            width: 48px;
            height: 48px;
            color: #38bdf8;
        }
        #pauseBtn:hover {
            background-color: #334155;
            border-color: #38bdf8;
        }
        #pauseBtn:pressed {
            background-color: #0284c7;
            color: #ffffff;
            border-color: #bae6fd;
        }
        #stepBtn {
            padding: 4px 4px;
            font-size: 11px;
            font-weight: 500;
        }
        #btnAudioListen {
            background-color: #0f172a;
            border: 1px solid #334155;
            border-radius: 6px;
            padding: 5px 6px;
            font-size: 11px;
            font-weight: 500;
            color: #cbd5e1;
        }
        #btnAudioListen:hover {
            background-color: #1e293b;
            border-color: #0284c7;
            color: #f8fafc;
        }
        #btnAudioListen:checked {
            background-color: #0284c7;
            border-color: #38bdf8;
            color: #ffffff;
            font-weight: bold;
        }
        #btnAudioTalk {
            background-color: #0f172a;
            border: 1px solid #0284c7;
            border-radius: 6px;
            padding: 5px 6px;
            font-size: 12px;
            font-weight: bold;
            color: #38bdf8;
        }
        #btnAudioTalk:hover {
            background-color: #0284c7;
            color: #ffffff;
        }
        #btnAudioTalk:checked {
            background-color: #dc2626;
            border-color: #ef4444;
            color: #ffffff;
            font-weight: bold;
        }
        #btnAudioTalk:pressed {
            background-color: #b91c1c;
            border-color: #f87171;
            color: #ffffff;
        }
        #btnReboot {
            background-color: #1e293b;
            color: #f87171;
            border: 1px solid #7f1d1d;
            border-radius: 6px;
            padding: 6px 10px;
            font-size: 12px;
            font-weight: 500;
        }
        #btnReboot:hover {
            background-color: #7f1d1d;
            color: #ffffff;
            border-color: #ef4444;
        }
        #btnReboot:pressed {
            background-color: #991b1b;
        }
        /* ComboBox with clear Chevron Down Arrow */
        QComboBox {
            background-color: #0f172a;
            border: 1px solid #334155;
            border-radius: 6px;
            padding: 4px 22px 4px 8px;
            color: #f8fafc;
        }
        QComboBox:hover {
            border-color: #0284c7;
        }
        QComboBox::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 22px;
            border: none;
        }
        QComboBox::down-arrow {
            width: 0px;
            height: 0px;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 5px solid #38bdf8;
            margin-right: 6px;
        }
        /* ComboBox Popup List Styling */
        QComboBox QAbstractItemView {
            background-color: #1e293b;
            color: #f8fafc;
            border: 1px solid #475569;
            selection-background-color: #0284c7;
            selection-color: #ffffff;
            padding: 4px;
            outline: none;
        }
        #camSelector QAbstractItemView {
            min-width: 340px;
        }
        #recDurationCombo QAbstractItemView {
            min-width: 270px;
        }
        QComboBox QAbstractItemView::item {
            min-height: 28px;
            padding: 6px 10px;
            border-radius: 4px;
            color: #f8fafc;
            background-color: #1e293b;
        }
        QComboBox QAbstractItemView::item:hover {
            background-color: #334155;
            color: #38bdf8;
        }
        QComboBox QAbstractItemView::item:selected {
            background-color: #0284c7;
            color: #ffffff;
        }
        QLineEdit {
            background-color: #0f172a;
            border: 1px solid #334155;
            border-radius: 6px;
            padding: 4px 6px;
            color: #f8fafc;
        }
        QLineEdit:focus {
            border-color: #0284c7;
        }
        QSlider::groove:horizontal {
            height: 6px;
            background: #334155;
            border-radius: 3px;
        }
        QSlider::sub-page:horizontal {
            background: #0284c7;
            border-radius: 3px;
        }
        QSlider::handle:horizontal {
            background: #38bdf8;
            width: 16px;
            margin-top: -5px;
            margin-bottom: -5px;
            border-radius: 8px;
        }
        QCheckBox {
            color: #e2e8f0;
            spacing: 5px;
        }
        QCheckBox::indicator {
            width: 15px;
            height: 15px;
            border-radius: 4px;
            border: 1px solid #475569;
            background-color: #0f172a;
        }
        QCheckBox::indicator:checked {
            background-color: #0284c7;
            border-color: #38bdf8;
        }
        """
        self.setStyleSheet(style)
