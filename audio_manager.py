"""
Audio Manager for ICSee / Xiongmai Cameras.
Provides:
1. CameraAudioReceiver: Streams RTSP audio (G.711 A-law 8000Hz) from camera to PC speaker via QAudioSink.
2. CameraTalkWorker: Captures PC microphone via QAudioSource at 8000Hz Int16, encodes G.711 A-law,
   and streams in real-time to the camera speaker over Sofia NetSDK port 34567 (TALK_CU_PU_DATA 1432).
"""

import socket
import struct
import hashlib
import re
import json
import time
import math
from typing import Optional

try:
    import audioop
except ImportError:
    audioop = None

from PyQt6.QtCore import QObject, QThread, pyqtSignal, QIODevice
from PyQt6.QtMultimedia import (
    QAudioSource,
    QAudioSink,
    QAudioFormat,
    QMediaDevices
)


def pcm16_to_alaw(pcm_bytes: bytes) -> bytes:
    """Converts 16-bit linear PCM audio to 8-bit G.711 A-law."""
    if audioop is not None:
        return audioop.lin2alaw(pcm_bytes, 2)
    
    # Pure-Python fallback table lookup
    out = bytearray(len(pcm_bytes) // 2)
    for i in range(0, len(pcm_bytes), 2):
        sample = struct.unpack_from("<h", pcm_bytes, i)[0]
        sign = 0x00 if sample >= 0 else 0x80
        if sample < 0:
            sample = -sample
        if sample > 32767:
            sample = 32767
        
        if sample >= 256:
            exponent = int(math.log2(sample)) - 4
            exponent = min(7, max(1, exponent))
            mantissa = (sample >> (exponent + 3)) & 0x0F
            alaw = (exponent << 4) | mantissa
        else:
            alaw = sample >> 4
        out[i // 2] = (sign | alaw) ^ 0xD5
    return bytes(out)


def alaw_to_pcm16(alaw_bytes: bytes) -> bytes:
    """Converts 8-bit G.711 A-law audio to 16-bit linear PCM."""
    if audioop is not None:
        return audioop.alaw2lin(alaw_bytes, 2)
    
    out = bytearray(len(alaw_bytes) * 2)
    for i, b in enumerate(alaw_bytes):
        b ^= 0xD5
        sign = -1 if (b & 0x80) else 1
        exponent = (b >> 4) & 0x07
        mantissa = b & 0x0F
        if exponent == 0:
            sample = (mantissa << 4) + 8
        else:
            sample = ((mantissa << 4) + 0x108) << (exponent - 1)
        sample = sample * sign
        struct.pack_into("<h", out, i * 2, max(-32768, min(32767, sample)))
    return bytes(out)


class CameraAudioReceiver(QThread):
    """
    Background worker thread that receives live RTSP audio (G.711 A-law 8000Hz)
    from camera trackID=4 and streams it directly to PC speakers via QAudioSink.
    """
    status_changed = pyqtSignal(str) # "connecting", "playing", "stopped", "error"

    def __init__(self, ip: str, port: int, user: str, password: str, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.ip = ip
        self.port = port
        self.user = user
        self.password = password
        self._running = False
        self._muted = False
        self.sock: Optional[socket.socket] = None
        self.sink: Optional[QAudioSink] = None
        self.sink_io: Optional[QIODevice] = None

    def set_muted(self, muted: bool):
        self._muted = muted

    def stop(self):
        self._running = False
        if self.sock:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
                self.sock.close()
            except Exception:
                pass
            self.sock = None
        self.wait(2000)

    def run(self):
        self._running = True
        self.status_changed.emit("connecting")

        fmt = QAudioFormat()
        fmt.setSampleRate(8000)
        fmt.setChannelCount(1)
        fmt.setSampleFormat(QAudioFormat.SampleFormat.Int16)

        default_output = QMediaDevices.defaultAudioOutput()
        self.sink = QAudioSink(default_output, fmt)
        self.sink.setBufferSize(8000 * 2 // 5) # 200ms buffer for low latency
        self.sink_io = self.sink.start()

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(3.5)
            self.sock.connect((self.ip, self.port))
            sock = self.sock

            # Xiongmai direct URL
            if self.user:
                base_url = f"rtsp://{self.ip}:{self.port}/user={self.user}_password={self.password}_channel=0_stream=0.sdp"
            else:
                base_url = f"rtsp://{self.ip}:{self.port}/onvif1"

            # 1. DESCRIBE
            req_desc = f"DESCRIBE {base_url} RTSP/1.0\r\nCSeq: 1\r\nUser-Agent: ICSeeViewer\r\nAccept: application/sdp\r\n\r\n"
            sock.sendall(req_desc.encode("utf-8"))
            res_desc = sock.recv(4096).decode("utf-8", errors="ignore")

            # 2. SETUP trackID=4
            track_url = f"{base_url}/trackID=4"
            req_setup = (
                f"SETUP {track_url} RTSP/1.0\r\n"
                f"CSeq: 2\r\n"
                f"Transport: RTP/AVP/TCP;unicast;interleaved=2-3\r\n"
                f"User-Agent: ICSeeViewer\r\n\r\n"
            )
            sock.sendall(req_setup.encode("utf-8"))
            res_setup = sock.recv(4096).decode("utf-8", errors="ignore")

            m_sess = re.search(r'Session:\s*([^\r\n;]+)', res_setup)
            session_val = m_sess.group(1).strip() if m_sess else ""

            m_chan = re.search(r'interleaved=(\d+)-(\d+)', res_setup)
            audio_chan = int(m_chan.group(1)) if m_chan else 2

            # 3. PLAY
            req_play = (
                f"PLAY {base_url} RTSP/1.0\r\n"
                f"CSeq: 3\r\n"
                f"Session: {session_val}\r\n"
                f"Range: npt=0.000-\r\n\r\n"
            )
            sock.sendall(req_play.encode("utf-8"))

            self.status_changed.emit("playing")

            sock.settimeout(2.0)
            while self._running:
                b = sock.recv(1)
                if not b:
                    break
                if b != b"$":
                    continue

                hdr = sock.recv(3)
                if len(hdr) < 3:
                    break
                chan = hdr[0]
                length = (hdr[1] << 8) | hdr[2]

                payload = b""
                while len(payload) < length:
                    chunk = sock.recv(length - len(payload))
                    if not chunk:
                        break
                    payload += chunk

                if chan == audio_chan and len(payload) > 12:
                    if not self._muted and self.sink_io:
                        rtp_payload = payload[12:] # Strip 12-byte RTP header
                        pcm_bytes = alaw_to_pcm16(rtp_payload)
                        self.sink_io.write(pcm_bytes)

        except Exception as e:
            if self._running:
                print(f"[CameraAudioReceiver] Error: {e}")
                self.status_changed.emit("error")
        finally:
            if sock:
                try:
                    sock.close()
                except Exception:
                    pass
            if self.sink:
                try:
                    self.sink.stop()
                except Exception:
                    pass
                self.sink = None
                self.sink_io = None
            self.status_changed.emit("stopped")


class CameraTalkWorker(QThread):
    """
    Continuous Two-Way Intercom Worker (1-Click Toggle).
    Captures PC microphone at 8000Hz 1ch 16-bit PCM, applies digital amplification boost,
    encodes G.711 A-law and streams in real time to camera speaker over Sofia port 34567 (TALK_CU_PU_DATA 1432).
    """
    status_changed = pyqtSignal(str) # "connected", "talking", "stopped", "error"

    def __init__(self, ip: str, port: int, user: str, password: str, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.ip = ip
        self.port = port
        self.user = user
        self.password = password
        self._running = False
        self.sock: Optional[socket.socket] = None
        self.session_id: int = 0
        self.seq: int = 0

    def stop(self):
        self._running = False
        if self.sock:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
                self.sock.close()
            except Exception:
                pass
            self.sock = None
        self.wait(2000)

    def run(self):
        self._running = True
        self.status_changed.emit("connected")

        try:
            # 1. Connect and login to Sofia NetSDK port 34567
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(3.0)
            self.sock.connect((self.ip, self.port))
            s = self.sock

            login_payload = {
                "EncryptType": "NONE",
                "LoginType": "DVRIP-Web",
                "PassWord": self.password,
                "UserName": self.user
            }
            d = (json.dumps(login_payload) + "\n").encode("utf-8")
            h = struct.pack("<4sIIBBHI", b"\xff\x00\x00\x00", 0, 0, 0, 0, 1000, len(d))
            s.sendall(h + d)
            rh = s.recv(20)
            _, _, _, _, _, _, dlen = struct.unpack("<4sIIBBHI", rh)
            rdata = b""
            while len(rdata) < dlen:
                chunk = s.recv(dlen - len(rdata))
                if not chunk:
                    break
                rdata += chunk
            res = json.loads(rdata.decode("utf-8", errors="ignore").strip().split("\n")[0].strip())
            if res.get("Ret") != 100:
                self.status_changed.emit("error")
                s.close()
                return

            self.session_id = int(res["SessionID"], 16)
            self.seq = 1

            # 2. Maximize camera physical speaker volume (100%) so it is loud and clear
            try:
                vol_cfg = {
                    "Name": "fVideo.Volume",
                    "SessionID": hex(self.session_id),
                    "fVideo.Volume": [{"AudioMode": "Single", "LeftVolume": 100, "RightVolume": 100}]
                }
                d_vol = (json.dumps(vol_cfg) + "\n").encode("utf-8")
                self.seq += 1
                s.sendall(struct.pack("<4sIIBBHI", b"\xff\x00\x00\x00", self.session_id, self.seq, 0, 0, 1040, len(d_vol)) + d_vol)
                rh_vol = s.recv(20)
                if len(rh_vol) == 20:
                    dlen_vol = struct.unpack("<4sIIBBHI", rh_vol)[6]
                    s.recv(dlen_vol)
            except Exception:
                pass

            # 3. Claim the audio channel (TALK_CLAIM 1434)
            claim_payload = {
                "Name": "OPTalk",
                "SessionID": hex(self.session_id),
                "OPTalk": {
                    "Action": "Claim",
                    "AudioFormat": {
                        "BitRate": 0,
                        "EncodeType": "G711_ALAW",
                        "SampleBit": 8,
                        "SampleRate": 8000
                    }
                }
            }
            d_claim = (json.dumps(claim_payload) + "\n").encode("utf-8")
            self.seq += 1
            s.sendall(struct.pack("<4sIIBBHI", b"\xff\x00\x00\x00", self.session_id, self.seq, 0, 0, 1434, len(d_claim)) + d_claim)
            rh_claim = s.recv(20)
            if len(rh_claim) == 20:
                dlen_claim = struct.unpack("<4sIIBBHI", rh_claim)[6]
                s.recv(dlen_claim)

            # 4. Activate audio transmission (TALK_REQ 1430 Start)
            talk_payload = {
                "Name": "OPTalk",
                "SessionID": hex(self.session_id),
                "OPTalk": {
                    "Action": "Start",
                    "AudioFormat": {
                        "BitRate": 0,
                        "EncodeType": "G711_ALAW",
                        "SampleBit": 8,
                        "SampleRate": 8000
                    }
                }
            }
            d_talk = (json.dumps(talk_payload) + "\n").encode("utf-8")
            self.seq += 1
            s.sendall(struct.pack("<4sIIBBHI", b"\xff\x00\x00\x00", self.session_id, self.seq, 0, 0, 1430, len(d_talk)) + d_talk)

            # Drain incoming activation reply
            try:
                s.settimeout(0.3)
                rh_talk = s.recv(20)
                if len(rh_talk) == 20:
                    dlen_talk = struct.unpack("<4sIIBBHI", rh_talk)[6]
                    s.recv(dlen_talk)
            except Exception:
                pass

            self.sock = s
            self.status_changed.emit("talking")

            # 5. Setup QAudioSource for PC Microphone Capture (8000Hz 1ch Int16)
            fmt = QAudioFormat()
            fmt.setSampleRate(8000)
            fmt.setChannelCount(1)
            fmt.setSampleFormat(QAudioFormat.SampleFormat.Int16)

            dev = QMediaDevices.defaultAudioInput()
            source = QAudioSource(dev, fmt)
            source.setBufferSize(320 * 4)
            io_dev = source.start()

            buffer = bytearray()
            chunk_samples = 320 # 40ms per packet = 320 samples
            chunk_bytes = chunk_samples * 2

            while self._running:
                available = io_dev.bytesAvailable()
                if available > 0:
                    raw = io_dev.readAll().data()
                    buffer.extend(raw)

                while len(buffer) >= chunk_bytes:
                    pcm_chunk = bytes(buffer[:chunk_bytes])
                    del buffer[:chunk_bytes]

                    # Digital boost: 3.5x amplification with soft limiter for clear outdoor voice
                    samples = struct.unpack(f"<{chunk_samples}h", pcm_chunk)
                    amplified = [max(-32767, min(32767, int(val * 3.5))) for val in samples]
                    boosted_pcm = struct.pack(f"<{chunk_samples}h", *amplified)

                    alaw_chunk = pcm16_to_alaw(boosted_pcm)

                    # Subheader: 00 00 01 FA 0E 02 40 01 (length 320 in little endian)
                    audio_sub = b"\x00\x00\x01\xfa\x0e\x02\x40\x01"
                    payload = audio_sub + alaw_chunk
                    self.seq += 1
                    h_data = struct.pack("<4sIIBBHI", b"\xff\x00\x00\x00", self.session_id, self.seq, 0, 0, 1432, len(payload))
                    s.sendall(h_data + payload)

                time.sleep(0.015)

            source.stop()

        except Exception as e:
            if self._running:
                print(f"[CameraTalkWorker] Error: {e}")
                self.status_changed.emit("error")
        finally:
            if self.sock:
                try:
                    self.sock.close()
                except Exception:
                    pass
                self.sock = None
            self.status_changed.emit("stopped")
            self.status_changed.emit("stopped")
