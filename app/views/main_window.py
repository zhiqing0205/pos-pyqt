# coding: utf-8
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

from qfluentwidgets import FluentWindow, NavigationItemPosition
from qfluentwidgets import FluentIcon as FIF

from ..common.config import APP_NAME
from ..common.auth import AuthManager
from ..common.backup import BackupManager
from .sales_interface import SalesInterface
from .product_interface import ProductInterface
from .user_interface import UserInterface
from .stock_in_interface import StockInInterface
from ..dialogs.backup_dialog import BackupDialog


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

    def _init_navigation(self):
        self.addSubInterface(self.salesInterface, FIF.SHOPPING_CART, '收银')

        if AuthManager.is_admin():
            self.addSubInterface(self.productInterface, FIF.TAG, '商品管理')
            self.addSubInterface(self.stockInInterface, FIF.ADD_TO, '进货管理')
            self.addSubInterface(self.userInterface, FIF.PEOPLE, '用户管理')

        # Backup button at bottom
        self.navigationInterface.addItem(
            routeKey='backup',
            icon=FIF.SAVE,
            text='备份管理',
            onClick=self._show_backup_dialog,
            selectable=False,
            position=NavigationItemPosition.BOTTOM,
        )

    def _init_window(self):
        role_text = '管理员' if AuthManager.is_admin() else '店员'
        self.setWindowTitle('{} - {} ({})'.format(
            APP_NAME, self._user_info['username'], role_text))
        self.resize(1200, 800)
        self.setMinimumSize(960, 640)

        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)

    def _show_backup_dialog(self):
        dialog = BackupDialog(self._backup_manager, self)
        dialog.exec_()

    def closeEvent(self, event):
        AuthManager.logout()
        super().closeEvent(event)
