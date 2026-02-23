# coding: utf-8
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QApplication

from qfluentwidgets import (LineEdit, PasswordLineEdit, PrimaryPushButton,
                            InfoBar, InfoBarPosition, setFont, SubtitleLabel,
                            TitleLabel)

from ..common.auth import AuthManager
from ..common.config import APP_NAME


class LoginWindow(QWidget):
    """Login window for the POS system."""

    login_success = pyqtSignal(dict)  # emits user info dict

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(APP_NAME)
        self.setFixedSize(420, 380)
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint)
        self._init_ui()
        self._center_on_screen()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(50, 40, 50, 40)
        layout.setSpacing(0)

        # Title
        self.titleLabel = TitleLabel(APP_NAME)
        self.titleLabel.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.titleLabel)

        layout.addSpacing(8)

        self.subtitleLabel = SubtitleLabel('请登录以继续')
        self.subtitleLabel.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.subtitleLabel)

        layout.addSpacing(30)

        # Username
        self.usernameEdit = LineEdit()
        self.usernameEdit.setPlaceholderText('用户名')
        self.usernameEdit.setClearButtonEnabled(True)
        layout.addWidget(self.usernameEdit)

        layout.addSpacing(15)

        # Password
        self.passwordEdit = PasswordLineEdit()
        self.passwordEdit.setPlaceholderText('密码')
        layout.addWidget(self.passwordEdit)

        layout.addSpacing(25)

        # Login button
        self.loginBtn = PrimaryPushButton('登 录')
        self.loginBtn.setFixedHeight(38)
        layout.addWidget(self.loginBtn)

        layout.addStretch()

        # Connections
        self.loginBtn.clicked.connect(self._on_login)
        self.passwordEdit.returnPressed.connect(self._on_login)
        self.usernameEdit.returnPressed.connect(lambda: self.passwordEdit.setFocus())

    def _center_on_screen(self):
        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)

    def _on_login(self):
        username = self.usernameEdit.text().strip()
        password = self.passwordEdit.text()

        if not username or not password:
            InfoBar.error(
                title='登录失败',
                content='请输入用户名和密码',
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )
            return

        user = AuthManager.login(username, password)
        if user:
            self.login_success.emit(user)
            self.close()
        else:
            InfoBar.error(
                title='登录失败',
                content='用户名或密码错误，或账号已被禁用',
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )
            self.passwordEdit.clear()
            self.passwordEdit.setFocus()

    def showEvent(self, event):
        super().showEvent(event)
        self.usernameEdit.setFocus()
