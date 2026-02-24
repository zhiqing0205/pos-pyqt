# coding: utf-8
import sys
import os

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

from app.common.config import APP_NAME, BASE_DIR
from app.common.database import init_database
from app.common.backup import BackupManager
from app.views.login_window import LoginWindow
from app.views.main_window import MainWindow

ICON_PATH = os.path.join(BASE_DIR, 'resources', 'icon.ico')
ICON_PNG = os.path.join(BASE_DIR, 'resources', 'icon.png')


def main():
    # High DPI support
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)

    # Set application-wide icon (taskbar, title bar, etc.)
    icon_file = ICON_PATH if os.path.exists(ICON_PATH) else ICON_PNG
    if os.path.exists(icon_file):
        app.setWindowIcon(QIcon(icon_file))

    # Initialize database
    init_database()

    # Start backup manager
    backup_manager = BackupManager()
    backup_manager.start()

    # Show login window
    login_window = LoginWindow()
    main_window = None

    def on_login_success(user_info):
        nonlocal main_window
        main_window = MainWindow(user_info, backup_manager)
        main_window.show()

    login_window.login_success.connect(on_login_success)
    login_window.show()

    exit_code = app.exec_()
    backup_manager.stop()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
