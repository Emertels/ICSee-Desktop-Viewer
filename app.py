"""
Main entry point for ICSee Desktop Viewer.
"""

import sys
import os
import traceback

# Ensure project directory is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def show_critical_error(msg: str):
    import ctypes
    ctypes.windll.user32.MessageBoxW(0, msg, "Erro - ICSee Desktop Viewer", 0x10)

try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QIcon
    from main_window import MainWindow

    def main():
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )

        app = QApplication(sys.argv)
        app.setApplicationName("ICSee Desktop Viewer")
        app.setOrganizationName("ICSeeViewer")

        base_dir = getattr(sys, '_MEIPASS', current_dir)
        icon_path = os.path.join(base_dir, "app_icon.ico")
        if not os.path.exists(icon_path):
            icon_path = os.path.join(current_dir, "app_icon.ico")
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))

        window = MainWindow()
        if "--minimized" in sys.argv or window.config.get("start_minimized", False):
            window.showMinimized()
        else:
            window.show()

        sys.exit(app.exec())

    if __name__ == "__main__":
        main()

except Exception as e:
    err_text = traceback.format_exc()
    log_file = os.path.join(current_dir, "crash_log.txt")
    try:
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(err_text)
    except Exception:
        pass
    show_critical_error(f"Erro ao iniciar o visualizador:\n\n{e}\n\nDetalhes gravados em:\n{log_file}")
