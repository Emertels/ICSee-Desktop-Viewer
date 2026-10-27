"""
Gamepad Controller Worker using pygame-ce.
Supports Sony PlayStation DualSense (PS5), DualShock 4 (PS4),
and Microsoft Xbox (One, Series, 360) controllers.
Provides 8-way analog steering, instant motor halt on stick release,
and dedicated Pause/Resume toggle via Circle (○) / B button.
"""

import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import time
from PyQt6.QtCore import QThread, pyqtSignal


class GamepadWorker(QThread):
    connected = pyqtSignal(str) # controller name
    disconnected = pyqtSignal()
    move = pyqtSignal(str, float) # direction ("left", "right", "up", "down", "left_up", etc.), speed
    ptz_stop = pyqtSignal() # emitted when analog stick or D-pad returns to center
    action_pause = pyqtSignal() # emitted when Circle (○) / B button is pressed
    action_snapshot = pyqtSignal() # Triangle (△) / Y
    action_quality = pyqtSignal(str) # "sub" or "main"
    action_layout = pyqtSignal() # Square (□) / X
    action_zoom_lens = pyqtSignal(str) # "top" (L2/LT) or "bottom" (R2/RT)

    def __init__(self):
        super().__init__()
        self._running = False
        self.active_direction = None
        self.btn_states = {}

    def stop_worker(self):
        self._running = False
        self.wait(1000)

    def run(self):
        self._running = True
        try:
            import pygame
            pygame.init()
            pygame.joystick.init()
        except Exception as e:
            print(f"[Gamepad] Initialization error: {e}")
            return

        joystick = None
        current_name = ""
        DEADZONE = 0.28

        while self._running:
            try:
                import pygame
                pygame.event.pump()
                count = pygame.joystick.get_count()

                if count == 0:
                    if joystick is not None:
                        joystick = None
                        current_name = ""
                        self.disconnected.emit()
                    time.sleep(0.5)
                    continue

                if joystick is None:
                    joystick = pygame.joystick.Joystick(0)
                    current_name = joystick.get_name()
                    self.connected.emit(current_name)

                # 1. Analog Sticks (Left Stick: axes 0 & 1, Right Stick: axes 2 & 3)
                num_axes = joystick.get_numaxes()
                ax_x = joystick.get_axis(0) if num_axes > 0 else 0.0
                ax_y = joystick.get_axis(1) if num_axes > 1 else 0.0

                # Also allow right stick if left stick is idle
                if abs(ax_x) < DEADZONE and abs(ax_y) < DEADZONE and num_axes >= 4:
                    rx = joystick.get_axis(2)
                    ry = joystick.get_axis(3)
                    if abs(rx) >= DEADZONE or abs(ry) >= DEADZONE:
                        ax_x = rx
                        ax_y = ry

                # 2. D-Pad Inputs (Buttons 11-14 on DualSense, or Hat 0 on Xbox)
                dpad_x, dpad_y = 0.0, 0.0
                num_buttons = joystick.get_numbuttons()
                num_hats = joystick.get_numhats()

                if num_hats > 0:
                    hat = joystick.get_hat(0)
                    dpad_x = float(hat[0])
                    dpad_y = float(-hat[1]) # invert Y so 1 is down, -1 is up

                # DualSense D-Pad buttons: 11=Up, 12=Down, 13=Left, 14=Right
                if num_buttons > 14:
                    if joystick.get_button(11):
                        dpad_y = -1.0
                    elif joystick.get_button(12):
                        dpad_y = 1.0
                    if joystick.get_button(13):
                        dpad_x = -1.0
                    elif joystick.get_button(14):
                        dpad_x = 1.0

                # Combine stick and D-pad
                eff_x = dpad_x if abs(dpad_x) > 0.1 else (ax_x if abs(ax_x) >= DEADZONE else 0.0)
                eff_y = dpad_y if abs(dpad_y) > 0.1 else (ax_y if abs(ax_y) >= DEADZONE else 0.0)

                target_dir = None
                speed = 0.6

                is_x = abs(eff_x) >= DEADZONE
                is_y = abs(eff_y) >= DEADZONE

                if is_x and is_y:
                    h_dir = "left" if eff_x < 0 else "right"
                    v_dir = "up" if eff_y < 0 else "down"
                    target_dir = f"{h_dir}_{v_dir}"
                    speed = min(1.0, max(0.3, max(abs(eff_x), abs(eff_y))))
                elif is_x:
                    target_dir = "left" if eff_x < 0 else "right"
                    speed = min(1.0, max(0.3, abs(eff_x)))
                elif is_y:
                    target_dir = "up" if eff_y < 0 else "down"
                    speed = min(1.0, max(0.3, abs(eff_y)))

                # Motion state change: emit move on direction or ptz_stop on stick center
                if target_dir != self.active_direction:
                    self.active_direction = target_dir
                    if target_dir:
                        self.move.emit(target_dir, speed)
                    else:
                        self.ptz_stop.emit()

                # 3. Action Buttons (edge-triggered on press)
                def was_just_pressed(btn_id):
                    if btn_id >= num_buttons:
                        return False
                    cur = joystick.get_button(btn_id)
                    prev = self.btn_states.get(btn_id, False)
                    self.btn_states[btn_id] = cur
                    return cur and not prev

                # Triangle (DualSense 3, Xbox Y 3) -> Snapshot!
                if was_just_pressed(3):
                    self.action_snapshot.emit()

                # Square (DualSense 2, Xbox X 2) -> Toggle Layout (Normal / Side-by-Side)!
                if was_just_pressed(2):
                    self.action_layout.emit()

                # L1 / LB (DualSense 9/4, Xbox LB 4) -> SD Fluido
                if was_just_pressed(4) or (num_buttons > 9 and was_just_pressed(9)):
                    self.action_quality.emit("sub")

                # R1 / RB (DualSense 10/5, Xbox RB 5) -> HD Ultra
                if was_just_pressed(5) or (num_buttons > 10 and was_just_pressed(10)):
                    self.action_quality.emit("main")

                # Circle / B (DualSense 1, Xbox B 1) -> Pause / Resume Camera
                if was_just_pressed(1):
                    self.action_pause.emit()

                # L2 / LT (DualSense 6/Axis 4, Xbox LT/Axis 4) -> Expand Upper/Left Camera
                l2_hit = False
                if num_buttons > 6 and was_just_pressed(6):
                    l2_hit = True
                elif num_axes > 4:
                    trig_l = joystick.get_axis(4)
                    prev_l = self.btn_states.get("trig_l", False)
                    cur_l = trig_l > 0.4
                    self.btn_states["trig_l"] = cur_l
                    if cur_l and not prev_l:
                        l2_hit = True

                if l2_hit:
                    self.action_zoom_lens.emit("top")

                # R2 / RT (DualSense 7/Axis 5, Xbox RT/Axis 5) -> Expand Lower/Right Camera
                r2_hit = False
                if num_buttons > 7 and was_just_pressed(7):
                    r2_hit = True
                elif num_axes > 5:
                    trig_r = joystick.get_axis(5)
                    prev_r = self.btn_states.get("trig_r", False)
                    cur_r = trig_r > 0.4
                    self.btn_states["trig_r"] = cur_r
                    if cur_r and not prev_r:
                        r2_hit = True

                if r2_hit:
                    self.action_zoom_lens.emit("bottom")

            except Exception:
                pass

            time.sleep(0.04) # ~25 Hz polling rate
