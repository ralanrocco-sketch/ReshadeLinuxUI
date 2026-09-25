"""Small desktop frontend for kevinlekiller/reshade-steam-proton."""
import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow

def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("ReShade Linux GUI")
    app.setOrganizationName("ReShade Linux GUI")
    window = MainWindow()
    window.show()
    return app.exec()

if __name__ == "__main__":
    raise SystemExit(main())
