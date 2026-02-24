# coding: utf-8
import os

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QIcon
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                              QApplication, QGraphicsDropShadowEffect)

from qfluentwidgets import (LineEdit, PasswordLineEdit, PrimaryPushButton,
                            InfoBar, InfoBarPosition, setFont, SubtitleLabel,
                            TitleLabel, CaptionLabel, SimpleCardWidget,
                            FluentIcon as FIF)

from ..common.auth import AuthManager
from ..common.config import APP_NAME, BASE_DIR

ICON_PATH = os.path.join(BASE_DIR, 'resources', 'icon.png')


class LoginWindow(QWidget):
    """Login window for the POS system."""

    login_success = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(APP_NAME)
        if os.path.exists(ICON_PATH):
            self.setWindowIcon(QIcon(ICON_PATH))
        self.setFixedSize(860, 520)
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint)
        self._init_ui()
        self._center_on_screen()

    def _init_ui(self):
        # Background styling
        self.setStyleSheet('''
            LoginWindow {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:1 #764ba2
                );
            }
        ''')

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        # ── Left branding panel ──
        left = QWidget()
        left.setFixedWidth(360)
        left.setStyleSheet('background: transparent;')
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(50, 0, 30, 0)
        left_layout.setAlignment(Qt.AlignCenter)

        icon_label = QLabel()
        icon_label.setText(FIF.SHOPPING_CART.icon().name() if False else '')
        icon_label.hide()

        brand_title = TitleLabel(APP_NAME)
        setFont(brand_title, 30)
        brand_title.setStyleSheet('color: white;')
        left_layout.addWidget(brand_title)

        left_layout.addSpacing(12)

        brand_sub = SubtitleLabel('高效便捷的收银管理')
        brand_sub.setStyleSheet('color: rgba(255,255,255,0.85);')
        left_layout.addWidget(brand_sub)

        left_layout.addSpacing(30)

        features = [
            ('扫码收银，快速结账', FIF.SHOPPING_CART),
            ('商品库存，实时管理', FIF.TAG),
            ('数据备份，安全可靠', FIF.SAVE),
        ]
        for text, _ in features:
            row = QHBoxLayout()
            row.setSpacing(8)
            dot = CaptionLabel('●')
            dot.setStyleSheet('color: rgba(255,255,255,0.7);')
            desc = CaptionLabel(text)
            setFont(desc, 14)
            desc.setStyleSheet('color: rgba(255,255,255,0.9);')
            row.addWidget(dot)
            row.addWidget(desc)
            row.addStretch()
            left_layout.addLayout(row)
            left_layout.addSpacing(6)

        outer.addWidget(left)

        # ── Right login card ──
        right = QWidget()
        right.setStyleSheet('background: transparent;')
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(30, 0, 50, 0)
        right_layout.setAlignment(Qt.AlignCenter)

        card = SimpleCardWidget()
        card.setFixedSize(340, 360)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 60))
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(35, 35, 35, 30)
        card_layout.setSpacing(0)

        login_title = SubtitleLabel('登录')
        setFont(login_title, 22)
        card_layout.addWidget(login_title)

        card_layout.addSpacing(6)

        login_hint = CaptionLabel('请输入账号和密码')
        login_hint.setStyleSheet('color: gray;')
        card_layout.addWidget(login_hint)

        card_layout.addSpacing(25)

        self.usernameEdit = LineEdit()
        self.usernameEdit.setPlaceholderText('用户名')
        self.usernameEdit.setClearButtonEnabled(True)
        self.usernameEdit.setFixedHeight(38)
        card_layout.addWidget(self.usernameEdit)

        card_layout.addSpacing(15)

        self.passwordEdit = PasswordLineEdit()
        self.passwordEdit.setPlaceholderText('密码')
        self.passwordEdit.setFixedHeight(38)
        card_layout.addWidget(self.passwordEdit)

        card_layout.addSpacing(25)

        self.loginBtn = PrimaryPushButton('登 录')
        self.loginBtn.setFixedHeight(40)
        setFont(self.loginBtn, 15)
        card_layout.addWidget(self.loginBtn)

        card_layout.addStretch()

        right_layout.addWidget(card)

        outer.addWidget(right)

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
