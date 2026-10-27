import os
import sys
import subprocess
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON_EXE = sys.executable

# Dynamically locate onvif wsdl directory
import importlib.util
spec = importlib.util.find_spec("onvif")
if spec and spec.origin:
    WSDL_SRC = os.path.join(os.path.dirname(spec.origin), "wsdl")
    if not os.path.isdir(WSDL_SRC):
        WSDL_SRC = os.path.join(sys.prefix, "Lib", "site-packages", "wsdl")
else:
    WSDL_SRC = os.path.join(sys.prefix, "Lib", "site-packages", "wsdl")

ICON_SRC = os.path.join(BASE_DIR, "app_icon.ico")

cmd = [
    PYTHON_EXE,
    "-m", "PyInstaller",
    "--noconfirm",
    "--clean",
    "--windowed",
    "--name=ICSee_Viewer",
    f"--icon={ICON_SRC}",
    f"--add-data={WSDL_SRC};wsdl",
    f"--add-data={ICON_SRC};.",
    "--hidden-import=PyQt6.QtMultimedia",
    "--hidden-import=PyQt6.QtCore",
    "--hidden-import=PyQt6.QtGui",
    "--hidden-import=PyQt6.QtWidgets",
    "--hidden-import=cv2",
    "--hidden-import=numpy",
    "--hidden-import=onvif",
    "--hidden-import=zeep",
    "--hidden-import=zeep.transports",
    "--hidden-import=zeep.plugins",
    "--hidden-import=defusedxml",
    "--hidden-import=lxml",
    "--hidden-import=audio_manager",
    "--hidden-import=camera_manager",
    "--hidden-import=video_worker",
    "--hidden-import=gamepad_worker",
    "--hidden-import=main_window",
    "--hidden-import=i18n",
    "--collect-data=zeep",
    "--collect-submodules=zeep",
    "--onedir",
    os.path.join(BASE_DIR, "app.py")
]

print("Running PyInstaller build...")
res = subprocess.run(cmd, cwd=BASE_DIR)
print(f"Build exited with code: {res.returncode}")
