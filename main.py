# coding: utf-8
import sys
import os

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

from app.common.config import APP_NAME
from app.common.database import init_database
from app.common.backup import BackupManager
from app.views.login_window import LoginWindow
from app.views.main_window import MainWindow


def main():
    # High DPI support
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)

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
