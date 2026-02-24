# coding: utf-8
import os

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

from qfluentwidgets import FluentWindow, NavigationItemPosition
from qfluentwidgets import FluentIcon as FIF

from ..common.config import APP_NAME, BASE_DIR
from ..common.auth import AuthManager
from ..common.backup import BackupManager
from .sales_interface import SalesInterface
from .product_interface import ProductInterface
from .user_interface import UserInterface
from .stock_in_interface import StockInInterface
from .settings_interface import SettingsInterface
from .backup_interface import BackupInterface

ICON_PATH = os.path.join(BASE_DIR, 'resources', 'icon.png')


class MainWindow(FluentWindow):
    """Main application window with role-based navigation."""

    def __init__(self, user_info, backup_manager, parent=None):
        super().__init__()
        self._user_info = user_info
        self._backup_manager = backup_manager

        self._init_interfaces()
        self._init_navigation()
        self._init_window()

    def _init_interfaces(self):
        self.salesInterface = SalesInterface(self)
        self.salesInterface.setObjectName('sales-interface')

        if AuthManager.is_admin():
            self.productInterface = ProductInterface(self)
            self.productInterface.setObjectName('product-interface')

            self.stockInInterface = StockInInterface(self)
            self.stockInInterface.setObjectName('stock-in-interface')

            self.userInterface = UserInterface(self)
            self.userInterface.setObjectName('user-interface')

            self.settingsInterface = SettingsInterface(self)
            self.settingsInterface.setObjectName('settings-interface')

            self.backupInterface = BackupInterface(self._backup_manager, self)
            self.backupInterface.setObjectName('backup-interface')

    def _init_navigation(self):
        self.addSubInterface(self.salesInterface, FIF.SHOPPING_CART, '收银')

        if AuthManager.is_admin():
            self.addSubInterface(self.productInterface, FIF.TAG, '商品管理')
            self.addSubInterface(self.stockInInterface, FIF.ADD_TO, '进货管理')
            self.addSubInterface(self.userInterface, FIF.PEOPLE, '用户管理')

            self.addSubInterface(
                self.settingsInterface, FIF.SETTING, '支付设置',
                NavigationItemPosition.BOTTOM)

            self.addSubInterface(
                self.backupInterface, FIF.SAVE, '备份管理',
                NavigationItemPosition.BOTTOM)

    def _init_window(self):
        role_text = '管理员' if AuthManager.is_admin() else '店员'
        self.setWindowTitle('{} - {} ({})'.format(
            APP_NAME, self._user_info['username'], role_text))

        if os.path.exists(ICON_PATH):
            self.setWindowIcon(QIcon(ICON_PATH))

        self.resize(1200, 800)
        self.setMinimumSize(960, 640)

        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)

    def closeEvent(self, event):
        if self._backup_manager.should_backup_on_close():
            self._backup_manager.create_backup(prefix='close')
        AuthManager.logout()
        super().closeEvent(event)
