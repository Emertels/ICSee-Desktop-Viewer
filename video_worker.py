"""
Video Worker Thread for smooth, low-latency RTSP playback using OpenCV & PyQt6.
Optimized for high-speed switching between SD and HD streams without stutter or session lock.
"""

import os
import cv2
import time
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QImage

class VideoWorker(QThread):
    frame_ready = pyqtSignal(QImage, int, int, np.ndarray) # QImage, width, height, raw_bgr_frame
    fps_updated = pyqtSignal(float)
    status_changed = pyqtSignal(str) # "connecting", "connected", "switching", "disconnected", "error"

    def __init__(self, rtsp_url: str):
        super().__init__()
        self.rtsp_url = rtsp_url
        self.next_url = None
        self._switch_requested = False
        self._running = False
        self.last_raw_frame = None

    def switch_url(self, new_url: str):
        """Requests hot-switch to a new RTSP URL."""
        if new_url != self.rtsp_url:
            self.next_url = new_url
            self._switch_requested = True

    def get_last_raw_frame(self):
        return self.last_raw_frame

    def stop(self):
        self._running = False
        self.wait(1500)

    def run(self):
        self._running = True
        
        # Fast RTSP flags for FFmpeg: low probe size, zero buffering, quick recovery, 3s socket timeout
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = (
            "rtsp_transport;tcp|fflags;nobuffer|flags;low_delay|analyzeduration;500000|probesize;500000|max_delay;500000|reorder_queue_size;0|stimeout;3000000"
        )

        while self._running:
            self.status_changed.emit("connecting")
            
            cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 4000)
            cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 4000)

            if not cap.isOpened():
                self.status_changed.emit("error")
                for _ in range(10):
                    if not self._running or self._switch_requested:
                        break
                    time.sleep(0.1)
                if self._switch_requested and self.next_url:
                    self.rtsp_url = self.next_url
                    self.next_url = None
                    self._switch_requested = False
                continue

            self.status_changed.emit("connected")
            
            frame_count = 0
            start_time = time.time()
            consecutive_failures = 0

            while self._running:
                # Check for instant quality switch request
                if self._switch_requested:
                    self._switch_requested = False
                    if self.next_url:
                        self.status_changed.emit("switching")
                        self.rtsp_url = self.next_url
                        self.next_url = None
                        cap.release()
                        # Short pause to let camera close RTSP session cleanly
                        time.sleep(0.15)
                        break

                ret, frame = cap.read()
                
                if not ret or frame is None:
                    consecutive_failures += 1
                    if consecutive_failures > 25:
                        break
                    time.sleep(0.02)
                    continue

                consecutive_failures = 0
                frame_count += 1
                self.last_raw_frame = frame

                # FPS calculation
                elapsed = time.time() - start_time
                if elapsed >= 1.0:
                    fps = frame_count / elapsed
                    self.fps_updated.emit(fps)
                    frame_count = 0
                    start_time = time.time()

                # Convert to Qt QImage
                h, w, ch = frame.shape
                bytes_per_line = ch * w
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                q_img = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888).copy()
                
                self.frame_ready.emit(q_img, w, h, frame)

            cap.release()
            
            if self._running and not self._switch_requested and not self.next_url:
                self.status_changed.emit("disconnected")
                time.sleep(0.5)
