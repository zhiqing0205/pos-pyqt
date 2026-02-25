# coding: utf-8
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout

from qfluentwidgets import (SimpleCardWidget, SubtitleLabel, BodyLabel,
                            CaptionLabel, PasswordLineEdit, PrimaryPushButton,
                            InfoBar, InfoBarPosition, setFont, FluentIcon as FIF)

from ..common.auth import AuthManager
from ..models.user import UserModel


class ProfileInterface(QWidget):
    """Personal profile page for viewing info and changing password."""

    def __init__(self, user_info, parent=None):
        super().__init__(parent)
        self._user_info = user_info
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 20, 40, 20)
        layout.setSpacing(16)

        # ── User info card ──
        info_card = SimpleCardWidget()
        info_layout = QVBoxLayout(info_card)
        info_layout.setContentsMargins(30, 25, 30, 25)
        info_layout.setSpacing(12)

        info_title = SubtitleLabel('个人信息')
        info_layout.addWidget(info_title)
        info_layout.addSpacing(4)

        # Username row
        row1 = QHBoxLayout()
        row1.setSpacing(12)
        label1 = BodyLabel('用户名')
        label1.setFixedWidth(80)
        self.usernameLabel = BodyLabel(self._user_info['username'])
        setFont(self.usernameLabel, 15)
        row1.addWidget(label1)
        row1.addWidget(self.usernameLabel)
        row1.addStretch()
        info_layout.addLayout(row1)

        # Role row
        row2 = QHBoxLayout()
        row2.setSpacing(12)
        label2 = BodyLabel('角色')
        label2.setFixedWidth(80)
        role_text = '管理员' if self._user_info['role'] == 'admin' else '店员'
        self.roleLabel = BodyLabel(role_text)
        setFont(self.roleLabel, 15)
        row2.addWidget(label2)
        row2.addWidget(self.roleLabel)
        row2.addStretch()
        info_layout.addLayout(row2)

        # User ID row
        row3 = QHBoxLayout()
        row3.setSpacing(12)
        label3 = BodyLabel('用户 ID')
        label3.setFixedWidth(80)
        self.idLabel = BodyLabel(str(self._user_info['id']))
        setFont(self.idLabel, 15)
        row3.addWidget(label3)
        row3.addWidget(self.idLabel)
        row3.addStretch()
        info_layout.addLayout(row3)

        layout.addWidget(info_card)

        # ── Change password card ──
        pwd_card = SimpleCardWidget()
        pwd_layout = QVBoxLayout(pwd_card)
        pwd_layout.setContentsMargins(30, 25, 30, 25)
        pwd_layout.setSpacing(12)

        pwd_title = SubtitleLabel('修改密码')
        pwd_layout.addWidget(pwd_title)
        pwd_layout.addSpacing(4)

        # Old password
        pwd_layout.addWidget(BodyLabel('当前密码'))
        self.oldPwdEdit = PasswordLineEdit()
        self.oldPwdEdit.setPlaceholderText('请输入当前密码')
        self.oldPwdEdit.setFixedHeight(38)
        self.oldPwdEdit.setMaximumWidth(400)
        pwd_layout.addWidget(self.oldPwdEdit)

        pwd_layout.addSpacing(4)

        # New password
        pwd_layout.addWidget(BodyLabel('新密码'))
        self.newPwdEdit = PasswordLineEdit()
        self.newPwdEdit.setPlaceholderText('请输入新密码')
        self.newPwdEdit.setFixedHeight(38)
        self.newPwdEdit.setMaximumWidth(400)
        pwd_layout.addWidget(self.newPwdEdit)

        pwd_layout.addSpacing(4)

        # Confirm new password
        pwd_layout.addWidget(BodyLabel('确认新密码'))
        self.confirmPwdEdit = PasswordLineEdit()
        self.confirmPwdEdit.setPlaceholderText('请再次输入新密码')
        self.confirmPwdEdit.setFixedHeight(38)
        self.confirmPwdEdit.setMaximumWidth(400)
        pwd_layout.addWidget(self.confirmPwdEdit)

        pwd_layout.addSpacing(8)

        self.changePwdBtn = PrimaryPushButton(FIF.SYNC, '确认修改')
        self.changePwdBtn.setFixedWidth(140)
        pwd_layout.addWidget(self.changePwdBtn)

        layout.addWidget(pwd_card)

        layout.addStretch()

        # Connections
        self.changePwdBtn.clicked.connect(self._on_change_password)

    def _on_change_password(self):
        old_pwd = self.oldPwdEdit.text()
        new_pwd = self.newPwdEdit.text()
        confirm_pwd = self.confirmPwdEdit.text()

        if not old_pwd or not new_pwd or not confirm_pwd:
            InfoBar.error(
                title='错误', content='请填写所有密码字段',
                parent=self, position=InfoBarPosition.TOP, duration=3000)
            return

        if new_pwd != confirm_pwd:
            InfoBar.error(
                title='错误', content='两次输入的新密码不一致',
                parent=self, position=InfoBarPosition.TOP, duration=3000)
            self.confirmPwdEdit.clear()
            self.confirmPwdEdit.setFocus()
            return

        if len(new_pwd) < 4:
            InfoBar.error(
                title='错误', content='新密码长度不能少于 4 位',
                parent=self, position=InfoBarPosition.TOP, duration=3000)
            return

        # Verify old password
        old_hash = AuthManager.hash_password(old_pwd)
        user_id = self._user_info['id']

        from ..common.database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()

        if not row or row[0] != old_hash:
            InfoBar.error(
                title='错误', content='当前密码不正确',
                parent=self, position=InfoBarPosition.TOP, duration=3000)
            self.oldPwdEdit.clear()
            self.oldPwdEdit.setFocus()
            return

        # Update password
        if UserModel.update(user_id, password=new_pwd):
            InfoBar.success(
                title='成功', content='密码已修改',
                parent=self, position=InfoBarPosition.TOP, duration=2000)
            self.oldPwdEdit.clear()
            self.newPwdEdit.clear()
            self.confirmPwdEdit.clear()
        else:
            InfoBar.error(
                title='失败', content='密码修改失败',
                parent=self, position=InfoBarPosition.TOP, duration=3000)
