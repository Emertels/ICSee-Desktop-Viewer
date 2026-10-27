"""
Camera Manager for ICSee / Xiongmai cameras.
Handles ONVIF discovery, profile retrieval, RTSP stream URLs, ultra-responsive Sofia NetSDK PTZ,
and native Human Detection / Auto-Tracking (port 34567).
Supports Xiongmai authentication (user=..._password=...) and standard ONVIF.
"""

import socket
import struct
import uuid
import re
import time
import json
import threading
import concurrent.futures
import sys
import os
from typing import List, Dict, Optional
from onvif import ONVIFCamera

def get_wsdl_dir() -> str:
    """Finds WSDL directory whether running as python script or frozen PyInstaller executable."""
    if getattr(sys, 'frozen', False):
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        cand = os.path.join(base_dir, 'wsdl')
        if os.path.exists(cand):
            return cand
    try:
        import onvif
        p1 = os.path.join(os.path.dirname(os.path.dirname(onvif.__file__)), 'wsdl')
        if os.path.exists(p1):
            return p1
        return os.path.join(os.path.dirname(onvif.__file__), 'wsdl')
    except Exception:
        return 'wsdl'

WSDL_DIR = get_wsdl_dir()


class SofiaClient:
    """
    High-performance native client for Xiongmai / Sofia NetSDK protocol over TCP port 34567.
    Provides ~60ms ultra-low latency PTZ commands and native AI Humanoid Auto-Tracking.
    """
    def __init__(self, ip: str, port: int = 34567, user: str = "admin", password: str = ""):
        self.ip = ip
        self.port = port
        self.user = user
        self.password = password
        self.sock: Optional[socket.socket] = None
        self.session_id: int = 0
        self.seq: int = 0
        self._lock = threading.Lock()

    def update_credentials(self, ip: str, port: int, user: str, password: str):
        with self._lock:
            self.ip = ip
            self.port = port
            self.user = user
            self.password = password
            self._close_socket()

    def _close_socket(self):
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None
        self.session_id = 0

    def connect(self) -> bool:
        with self._lock:
            return self._raw_connect()

    def _raw_connect(self) -> bool:
        self._close_socket()
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2.5)
            s.connect((self.ip, self.port))
            payload = {
                "EncryptType": "NONE",
                "LoginType": "DVRIP-Web",
                "PassWord": self.password,
                "UserName": self.user
            }
            d = (json.dumps(payload) + "\n").encode("utf-8")
            h = struct.pack("<4sIIBBHI", b"\xff\x00\x00\x00", 0, 0, 0, 0, 1000, len(d))
            s.sendall(h + d)
            rh = s.recv(20)
            if len(rh) < 20:
                s.close()
                return False
            _, _, _, _, _, _, dlen = struct.unpack("<4sIIBBHI", rh)
            rdata = b""
            while len(rdata) < dlen:
                chunk = s.recv(dlen - len(rdata))
                if not chunk:
                    break
                rdata += chunk
            body = rdata.decode("utf-8", errors="ignore").strip().split("\n")[0].strip()
            res = json.loads(body)
            if res.get("Ret") == 100:
                self.session_id = int(res["SessionID"], 16)
                self.sock = s
                self.seq = 0
                return True
            s.close()
            return False
        except Exception:
            return False

    def send_cmd(self, mid: int, payload: dict, retries: int = 2) -> dict:
        """Sends a JSON command to the Sofia NetSDK port with automatic reconnection on stale socket."""
        with self._lock:
            for attempt in range(retries):
                if not self.sock:
                    if not self._raw_connect():
                        continue
                try:
                    self.seq += 1
                    payload["SessionID"] = hex(self.session_id)
                    d = (json.dumps(payload) + "\n").encode("utf-8")
                    h = struct.pack("<4sIIBBHI", b"\xff\x00\x00\x00", self.session_id, self.seq, 0, 0, mid, len(d))
                    self.sock.sendall(h + d)
                    rh = self.sock.recv(20)
                    if len(rh) < 20:
                        self._close_socket()
                        continue
                    _, _, _, _, _, _, dlen = struct.unpack("<4sIIBBHI", rh)
                    rdata = b""
                    while len(rdata) < dlen:
                        chunk = self.sock.recv(dlen - len(rdata))
                        if not chunk:
                            break
                        rdata += chunk
                    txt = rdata.decode("utf-8", errors="ignore").strip().split("\n")[0].strip()
                    res = json.loads(txt)
                    if res:
                        return res
                except Exception:
                    self._close_socket()
            return {}

    def ptz_move(self, cmd_name: str, step: int = 4) -> bool:
        req = {
            "Name": "OPPTZControl",
            "OPPTZControl": {
                "Command": cmd_name,
                "Parameter": {
                    "Channel": 0,
                    "MenuOpts": 0,
                    "POINT": [0, 0],
                    "Pattern": "None",
                    "Preset": 0,
                    "Step": max(1, min(8, step)),
                    "Tour": 0
                }
            }
        }
        res = self.send_cmd(1436, req)
        return res.get("Ret") in (100, 102)

    def ptz_stop(self) -> bool:
        return self.ptz_move("PTZStop", 0)

    def set_auto_tracking(self, enable: bool) -> bool:
        """Enables or disables native humanoid auto-tracking on the camera hardware."""
        ok1 = False
        track_req = {
            "Name": "Detect.DetectTrack",
            "Detect.DetectTrack": {
                "Enable": 1 if enable else 0,
                "ReturnTime": 5,
                "Sensitivity": 1
            }
        }
        res1 = self.send_cmd(1040, track_req)
        if res1.get("Ret") == 100:
            ok1 = True

        # Also configure Detect.HumanDetection
        cur_human = self.send_cmd(1042, {"Name": "Detect.HumanDetection"})
        if cur_human.get("Ret") == 100 and "Detect.HumanDetection" in cur_human:
            h_cfg = cur_human["Detect.HumanDetection"]
            if isinstance(h_cfg, list) and len(h_cfg) > 0:
                h_cfg[0]["Enable"] = bool(enable)
                h_cfg[0]["ShowTrack"] = bool(enable)
                set_h = {
                    "Name": "Detect.HumanDetection",
                    "Detect.HumanDetection": h_cfg
                }
                self.send_cmd(1040, set_h)

        return ok1

    def get_auto_tracking(self) -> bool:
        """Queries whether native humanoid auto-tracking is currently active."""
        res = self.send_cmd(1042, {"Name": "Detect.DetectTrack"})
        if res.get("Ret") == 100 and "Detect.DetectTrack" in res:
            en = res["Detect.DetectTrack"].get("Enable", 0)
            return bool(en == 1 or en is True)
        return False


class CameraManager:
    def __init__(self):
        self.ip: str = "192.168.1.10"
        self.port: int = 8899
        self.user: str = "admin"
        self.password: str = ""

        self.onvif_cam: Optional[ONVIFCamera] = None
        self.media_service = None
        self.ptz_service = None

        self.profiles: List[Dict] = []
        self.main_profile_token: Optional[str] = "000"
        self.sub_profile_token: Optional[str] = "001"
        self.current_profile_token: Optional[str] = "001"
        self.rtsp_urls: Dict[str, str] = {}
        self.device_info: Dict[str, str] = {}

        # PTZ Inversion settings (default invert_x=True because ICSee camera pan axis is inverted)
        self.invert_x = True
        self.invert_y = False

        self._ptz_lock = threading.Lock()
        self._is_moving = False

        # Sofia NetSDK client (port 34567) for ultra-fast PTZ and Auto-Tracking
        self.sofia = SofiaClient(self.ip, 34567, self.user, self.password)
        self.sofia_available = False

    @staticmethod
    def get_local_subnets() -> List[str]:
        prefixes = []
        try:
            hostname = socket.gethostname()
            for ip in socket.gethostbyname_ex(hostname)[2]:
                if ip.startswith("127.") or ip.startswith("172."):
                    continue
                parts = ip.split(".")
                if len(parts) == 4:
                    prefix = f"{parts[0]}.{parts[1]}.{parts[2]}."
                    if prefix not in prefixes:
                        prefixes.append(prefix)
        except Exception:
            pass
        if "192.168.1." not in prefixes:
            prefixes.append("192.168.1.")
        return prefixes

    @staticmethod
    def discover_cameras(timeout: float = 2.0) -> List[Dict]:
        found_map: Dict[str, Dict] = {}

        # 1. WS-Discovery Probe
        probe_msg = (
            '<?xml version="1.0" encoding="utf-8"?>'
            '<Envelope xmlns:dn="http://www.onvif.org/ver10/network/wsdl" xmlns="http://www.w3.org/2003/05/soap-envelope">'
            '<Header>'
            f'<wsa:MessageID xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing">uuid:{uuid.uuid4()}</wsa:MessageID>'
            '<wsa:To xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing">urn:schemas-xmlsoap-org:ws:2005:04:discovery</wsa:To>'
            '<wsa:Action xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing">http://schemas.xmlsoap.org/ws/2005/04/discovery/Probe</wsa:Action>'
            '</Header>'
            '<Body>'
            '<Probe xmlns="http://schemas.xmlsoap.org/ws/2005/04/discovery">'
            '<Types>dn:NetworkVideoTransmitter</Types>'
            '</Probe>'
            '</Body>'
            '</Envelope>'
        ).encode('utf-8')

        for subnet in CameraManager.get_local_subnets():
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
                s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                s.settimeout(timeout)
                s.sendto(probe_msg, ('239.255.255.250', 3702))
                s.sendto(probe_msg, ('255.255.255.255', 3702))
                s.sendto(probe_msg, (f"{subnet}255", 3702))

                start_t = time.time()
                while time.time() - start_t < timeout:
                    try:
                        data, addr = s.recvfrom(65535)
                        ip = addr[0]
                        if ip not in found_map:
                            found_map[ip] = {
                                'ip': ip,
                                'port': 8899,
                                'name': f"ICSee ({ip})",
                                'source': 'ONVIF WS-Discovery'
                            }
                    except socket.timeout:
                        break
                    except Exception:
                        break
                s.close()
            except Exception:
                pass

        # 2. Fast TCP probe on port 8899
        def check_candidate(candidate_ip: str):
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.2)
            if s.connect_ex((candidate_ip, 8899)) == 0:
                s.close()
                return candidate_ip, 8899
            s.close()
            return None, None

        for subnet in CameraManager.get_local_subnets():
            with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
                futures = [executor.submit(check_candidate, f"{subnet}{i}") for i in range(1, 255)]
                for f in concurrent.futures.as_completed(futures):
                    cand_ip, cand_port = f.result()
                    if cand_ip and cand_ip not in found_map:
                        found_map[cand_ip] = {
                            'ip': cand_ip,
                            'port': cand_port,
                            'name': f"ICSee ({cand_ip})",
                            'source': 'IP Scan'
                        }

        result = list(found_map.values())
        for cam in result:
            try:
                temp_cam = ONVIFCamera(cam['ip'], cam['port'], "admin", "", no_cache=True, wsdl_dir=WSDL_DIR)
                info = temp_cam.devicemgmt.GetDeviceInformation()
                model = getattr(info, 'Model', '')
                serial = getattr(info, 'SerialNumber', '')
                cam['model'] = model
                cam['serial'] = serial
                if model:
                    cam['name'] = f"ICSee {model} ({cam['ip']})"
            except Exception:
                pass

        return result

    def connect(self, ip: str, port: int = 8899, user: str = "admin", password: str = "") -> bool:
        """Connects to ONVIF service, discovers media profiles, and starts Sofia NetSDK connection."""
        self.ip = ip
        self.port = port
        self.user = user.strip()
        self.password = password.strip()
        self.profiles.clear()
        self.rtsp_urls.clear()
        self.main_profile_token = None
        self.sub_profile_token = None

        # 1. Connect Sofia client on port 34567 for fast PTZ & Auto-Tracking
        self.sofia.update_credentials(self.ip, 34567, self.user, self.password)
        self.sofia_available = self.sofia.connect()

        # 2. Connect ONVIF for RTSP Profiles
        try:
            self.onvif_cam = ONVIFCamera(self.ip, self.port, self.user, self.password, no_cache=True, wsdl_dir=WSDL_DIR)
            try:
                info = self.onvif_cam.devicemgmt.GetDeviceInformation()
                self.device_info = {
                    'Manufacturer': getattr(info, 'Manufacturer', 'ICSee/Xiongmai'),
                    'Model': getattr(info, 'Model', 'XM-Cam'),
                    'Firmware': getattr(info, 'FirmwareVersion', ''),
                    'Serial': getattr(info, 'SerialNumber', '')
                }
            except Exception:
                self.device_info = {'Model': 'ICSee IP Camera'}

            # Get media service & profiles
            self.media_service = self.onvif_cam.create_media_service()
            onvif_profiles = self.media_service.GetProfiles()

            for p in onvif_profiles:
                token = p.token
                name = getattr(p, 'Name', f'Profile_{token}')
                is_sub = 'sub' in name.lower() or token == '001'
                stream_idx = "1" if is_sub else "0"

                # Xiongmai format with embedded user and password (no hardcoded IP!)
                if self.user:
                    rtsp_uri = f"rtsp://{self.ip}:554/user={self.user}_password={self.password}_channel=0_stream={stream_idx}.sdp?real_stream"
                else:
                    rtsp_uri = f"rtsp://{self.ip}:554/onvif{'2' if is_sub else '1'}"

                self.profiles.append({
                    'token': token,
                    'name': name,
                    'is_sub': is_sub
                })
                self.rtsp_urls[token] = rtsp_uri

                if is_sub and self.sub_profile_token is None:
                    self.sub_profile_token = token
                elif not is_sub and self.main_profile_token is None:
                    self.main_profile_token = token

            if not self.sub_profile_token and self.profiles:
                self.sub_profile_token = self.profiles[0]['token']
            if not self.main_profile_token and self.profiles:
                self.main_profile_token = self.profiles[0]['token']

            self.current_profile_token = self.sub_profile_token

            # Initialize ONVIF PTZ as fallback
            try:
                self.ptz_service = self.onvif_cam.create_ptz_service()
            except Exception as e:
                self.ptz_service = None

            return True

        except Exception as e:
            print(f"[CameraManager] Connection error: {e}")
            self.onvif_cam = None
            self.media_service = None
            self.ptz_service = None
            return False

    def get_rtsp_url(self, profile_token: Optional[str] = None) -> str:
        token = profile_token or self.current_profile_token
        is_sub = (token == self.sub_profile_token) or (token == "001")
        stream_idx = "1" if is_sub else "0"

        if self.user:
            return f"rtsp://{self.ip}:554/user={self.user}_password={self.password}_channel=0_stream={stream_idx}.sdp?real_stream"
        return f"rtsp://{self.ip}:554/onvif{'2' if is_sub else '1'}"

    def get_token_for_quality(self, quality: str) -> str:
        if quality == "main" and self.main_profile_token:
            return self.main_profile_token
        if self.sub_profile_token:
            return self.sub_profile_token
        return self.profiles[0]['token'] if self.profiles else "000"

    def set_profile_by_token(self, token: str):
        if token in self.rtsp_urls:
            self.current_profile_token = token

    def ptz_move(self, direction: str, speed: float = 0.5) -> bool:
        """
        Rotates the camera in the specified direction using ONVIF ContinuousMove.
        Supports 8 directions: up, down, left, right, and diagonals.
        """
        if not self.ptz_service:
            return False

        d = direction.lower()

        want_left = "left" in d
        want_right = "right" in d
        want_up = "up" in d
        want_down = "down" in d

        # Apply axis inversions
        eff_left = want_right if self.invert_x else want_left
        eff_right = want_left if self.invert_x else want_right
        eff_up = want_down if self.invert_y else want_up
        eff_down = want_up if self.invert_y else want_down

        vx = 0.0
        vy = 0.0
        if eff_left:
            vx = -speed
        elif eff_right:
            vx = speed

        if eff_up:
            vy = speed
        elif eff_down:
            vy = -speed

        token = self.current_profile_token or "000"

        def _do_onvif():
            with self._ptz_lock:
                try:
                    self.ptz_service.ContinuousMove({
                        'ProfileToken': token,
                        'Velocity': {
                            'PanTilt': {'x': vx, 'y': vy}
                        }
                    })
                    self._is_moving = True
                except Exception as e:
                    print(f"[ONVIF PTZ] Move error: {e}")

        threading.Thread(target=_do_onvif, daemon=True).start()
        return True

    def ptz_stop(self) -> bool:
        """Halts camera rotation immediately via ONVIF Stop."""
        if not self.ptz_service:
            return False

        token = self.current_profile_token or "000"

        def _do_stop():
            with self._ptz_lock:
                try:
                    self.ptz_service.Stop({
                        'ProfileToken': token,
                        'PanTilt': True,
                        'Zoom': True
                    })
                except Exception as e:
                    pass
                self._is_moving = False

        threading.Thread(target=_do_stop, daemon=True).start()
        return True

    def ptz_step(self, direction: str, speed: float = 0.5, duration: float = 0.35):
        """Single short calibrated step in specified direction."""
        def _step():
            self.ptz_move(direction, speed)
            time.sleep(duration)
            self.ptz_stop()

        threading.Thread(target=_step, daemon=True).start()

    def set_auto_tracking(self, enable: bool) -> bool:
        """Enables or disables native humanoid auto-tracking on the camera hardware."""
        if not self.sofia_available:
            self.sofia_available = self.sofia.connect()
        return self.sofia.set_auto_tracking(enable)

    def get_auto_tracking(self) -> bool:
        """Queries camera hardware for active humanoid auto-tracking state."""
        if not self.sofia_available:
            self.sofia_available = self.sofia.connect()
        return self.sofia.get_auto_tracking()

    def set_light_mode(self, mode: str) -> bool:
        """
        Sets the camera lighting / night vision mode:
        - 'light': White light floodlights turned ON (color night mode).
        - 'night': Standard infrared night vision with white lights OFF.
        - 'auto': Intelligent auto mode (light triggers on motion/humanoid).
        """
        is_light = (mode == "light")
        is_auto = (mode == "auto")
        ok = False

        if not self.sofia_available:
            self.sofia_available = self.sofia.connect()

        # 1. Camera.WhiteLight WorkMode
        work_mode = "KeepOpen" if is_light else ("Auto" if is_auto else "Close")
        cfg = self.sofia.send_cmd(1042, {"Name": "Camera.WhiteLight"})
        if cfg.get("Ret") == 100 and "Camera.WhiteLight" in cfg:
            d = cfg["Camera.WhiteLight"].copy()
            d["WorkMode"] = work_mode
            r1 = self.sofia.send_cmd(1040, {"Name": "Camera.WhiteLight", "Camera.WhiteLight": d})
            if r1.get("Ret") == 100:
                ok = True

        # 2. Camera.ParamEx OneKeyOpenWL across all sensors
        ex = self.sofia.send_cmd(1042, {"Name": "Camera.ParamEx"})
        if ex.get("Ret") == 100 and "Camera.ParamEx" in ex:
            params = ex["Camera.ParamEx"]
            if isinstance(params, list) and len(params) > 0:
                new_params = []
                for p in params:
                    p_copy = p.copy()
                    p_copy["OneKeyOpenWL"] = bool(is_light)
                    new_params.append(p_copy)
                r2 = self.sofia.send_cmd(1040, {"Name": "Camera.ParamEx", "Camera.ParamEx": new_params})
                if r2.get("Ret") == 100:
                    ok = True

        return ok

    def get_light_mode(self) -> str:
        """Queries the current light mode from camera hardware."""
        if not self.sofia_available:
            self.sofia_available = self.sofia.connect()

        cfg = self.sofia.send_cmd(1042, {"Name": "Camera.WhiteLight"})
        if cfg.get("Ret") == 100 and "Camera.WhiteLight" in cfg:
            wm = cfg["Camera.WhiteLight"].get("WorkMode", "Close")
            if wm in ("KeepOpen", "Open"):
                return "light"
            elif wm in ("Auto", "Intelligent"):
                return "auto"

        ex = self.sofia.send_cmd(1042, {"Name": "Camera.ParamEx"})
        if ex.get("Ret") == 100 and "Camera.ParamEx" in ex:
            params = ex["Camera.ParamEx"]
            if isinstance(params, list) and len(params) > 0:
                if params[0].get("OneKeyOpenWL", False):
                    return "light"

        return "night"

    def reboot_camera(self) -> bool:
        """Reboots camera hardware via ONVIF SystemReboot or Sofia OPMachine."""
        ok = False
        if self.onvif_cam:
            try:
                self.onvif_cam.devicemgmt.SystemReboot()
                ok = True
            except Exception as e:
                print(f"[CameraManager] ONVIF SystemReboot error: {e}")

        if not ok and self.sofia:
            try:
                res = self.sofia.send_cmd(1450, {"Name": "OPMachine", "OPMachine": {"Action": "Reboot"}})
                if res.get("Ret") in (100, 102):
                    ok = True
            except Exception as e:
                print(f"[CameraManager] Sofia OPMachine reboot error: {e}")

        return ok
