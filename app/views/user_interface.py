# coding: utf-8
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QHeaderView,
                              QTableWidgetItem, QAbstractItemView)

from qfluentwidgets import (PushButton, PrimaryPushButton, TableWidget,
                            InfoBar, InfoBarPosition, FluentIcon as FIF,
                            MessageBox)

from ..models.user import UserModel
from ..dialogs.user_edit_dialog import UserEditDialog
from ..common.signal_bus import signal_bus


class UserInterface(QWidget):
    """User management interface for admin users."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._load_users()

        signal_bus.user_changed.connect(self._load_users)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(10)

        # Top bar
        top_layout = QHBoxLayout()
        top_layout.setSpacing(10)
        top_layout.addStretch()

        self.addBtn = PrimaryPushButton(FIF.ADD, '添加用户')
        top_layout.addWidget(self.addBtn)

        layout.addLayout(top_layout)

        # Table
        self.table = TableWidget(self)
        self.table.setBorderVisible(True)
        self.table.setBorderRadius(8)
        self.table.setWordWrap(False)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ['用户名', '角色', '状态', '创建时间', '操作'])
        self.table.verticalHeader().hide()
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        self.table.setColumnWidth(4, 190)

        layout.addWidget(self.table, 1)

        # Connections
        self.addBtn.clicked.connect(self._on_add)

    def _load_users(self):
        users = UserModel.get_all()
        self.table.setRowCount(len(users))
        for i, u in enumerate(users):
            self.table.setItem(i, 0, QTableWidgetItem(u['username']))
            role_text = '管理员' if u['role'] == 'admin' else '店员'
            self.table.setItem(i, 1, QTableWidgetItem(role_text))
            status_text = '启用' if u['is_active'] else '禁用'
            self.table.setItem(i, 2, QTableWidgetItem(status_text))
            self.table.setItem(i, 3, QTableWidgetItem(u['created_at']))

            # Action buttons
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 2, 4, 2)
            btn_layout.setSpacing(4)

            edit_btn = PushButton('编辑')
            edit_btn.setFixedSize(55, 28)
            toggle_btn = PushButton('禁用' if u['is_active'] else '启用')
            toggle_btn.setFixedSize(55, 28)
            del_btn = PushButton('删除')
            del_btn.setFixedSize(55, 28)

            user_id = u['id']
            is_active = u['is_active']
            edit_btn.clicked.connect(lambda checked, uid=user_id: self._on_edit(uid))
            toggle_btn.clicked.connect(
                lambda checked, uid=user_id, active=is_active: self._on_toggle(uid, active))
            del_btn.clicked.connect(lambda checked, uid=user_id: self._on_delete(uid))

            btn_layout.addWidget(edit_btn)
            btn_layout.addWidget(toggle_btn)
            btn_layout.addWidget(del_btn)
            self.table.setCellWidget(i, 4, btn_widget)

    def _on_add(self):
        dialog = UserEditDialog(parent=self.window())
        if dialog.exec_():
            data = dialog.get_data()
            password = data.pop('password', '')
            result = UserModel.create(data['username'], password, data['role'])
            if result:
                InfoBar.success(
                    title='成功', content='用户已添加',
                    parent=self, position=InfoBarPosition.TOP, duration=2000)
                self._load_users()
            else:
                InfoBar.error(
                    title='失败', content='添加失败，用户名可能重复',
                    parent=self, position=InfoBarPosition.TOP, duration=3000)

    def _on_edit(self, user_id):
        user = UserModel.get_by_id(user_id)
        if not user:
            return
        dialog = UserEditDialog(user=user, parent=self.window())
        if dialog.exec_():
            data = dialog.get_data()
            result = UserModel.update(
                user_id,
                username=data['username'],
                role=data['role'],
                password=data.get('password')
            )
            if result:
                InfoBar.success(
                    title='成功', content='用户已更新',
                    parent=self, position=InfoBarPosition.TOP, duration=2000)
                self._load_users()
            else:
                InfoBar.error(
                    title='失败', content='更新失败',
                    parent=self, position=InfoBarPosition.TOP, duration=3000)

    def _on_toggle(self, user_id, is_active):
        new_status = 0 if is_active else 1
        UserModel.update(user_id, is_active=new_status)
        self._load_users()

    def _on_delete(self, user_id):
        user = UserModel.get_by_id(user_id)
        if not user:
            return
        w = MessageBox('确认删除', '确定要禁用用户 "{}" 吗？'.format(user['username']),
                       self.window())
        w.yesButton.setText('确认')
        w.cancelButton.setText('取消')
        if w.exec_():
            UserModel.delete(user_id)
            InfoBar.success(
                title='成功', content='用户已禁用',
                parent=self, position=InfoBarPosition.TOP, duration=2000)
            self._load_users()
