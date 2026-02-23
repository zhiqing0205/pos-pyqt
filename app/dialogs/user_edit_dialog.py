# coding: utf-8
from PyQt5.QtWidgets import QVBoxLayout

from qfluentwidgets import (MessageBoxBase, LineEdit, ComboBox, BodyLabel,
                            SubtitleLabel)


class UserEditDialog(MessageBoxBase):
    """Dialog for adding or editing a user."""

    def __init__(self, user=None, parent=None):
        super().__init__(parent)
        self._user = user
        self._result_data = None
        self._init_ui()

    def _init_ui(self):
        is_edit = self._user is not None
        title = SubtitleLabel('编辑用户' if is_edit else '添加用户')
        self.viewLayout.addWidget(title)
        self.viewLayout.addSpacing(10)

        # Username
        self.viewLayout.addWidget(BodyLabel('用户名'))
        self.usernameEdit = LineEdit()
        self.usernameEdit.setPlaceholderText('用户名')
        if is_edit:
            self.usernameEdit.setText(self._user['username'])
        self.viewLayout.addWidget(self.usernameEdit)

        self.viewLayout.addSpacing(5)

        # Password
        hint = '（留空则不修改密码）' if is_edit else ''
        self.viewLayout.addWidget(BodyLabel('密码' + hint))
        self.passwordEdit = LineEdit()
        self.passwordEdit.setPlaceholderText('密码')
        self.viewLayout.addWidget(self.passwordEdit)

        self.viewLayout.addSpacing(5)

        # Role
        self.viewLayout.addWidget(BodyLabel('角色'))
        self.roleCombo = ComboBox()
        self.roleCombo.addItems(['店员', '管理员'])
        if is_edit and self._user['role'] == 'admin':
            self.roleCombo.setCurrentIndex(1)
        self.viewLayout.addWidget(self.roleCombo)

        self.yesButton.setText('保存')
        self.cancelButton.setText('取消')

        self.widget.setMinimumWidth(360)

    def get_data(self):
        return self._result_data

    def accept(self):
        username = self.usernameEdit.text().strip()
        password = self.passwordEdit.text()
        if not username:
            return
        if not self._user and not password:
            return  # New user must have password

        role = 'admin' if self.roleCombo.currentIndex() == 1 else 'clerk'

        self._result_data = {
            'username': username,
            'role': role,
        }
        if password:
            self._result_data['password'] = password

        super().accept()
