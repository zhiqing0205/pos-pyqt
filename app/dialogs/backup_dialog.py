# coding: utf-8
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QFileDialog

from qfluentwidgets import (MessageBoxBase, PushButton, PrimaryPushButton,
                            TableWidget, BodyLabel, SubtitleLabel,
                            InfoBar, InfoBarPosition, FluentIcon as FIF,
                            MessageBox)

from PyQt5.QtWidgets import QHeaderView, QTableWidgetItem, QAbstractItemView


class BackupDialog(MessageBoxBase):
    """Dialog for managing database backups."""

    def __init__(self, backup_manager, parent=None):
        super().__init__(parent)
        self._backup_manager = backup_manager
        self._init_ui()
        self._load_backups()

    def _init_ui(self):
        title = SubtitleLabel('备份管理')
        self.viewLayout.addWidget(title)

        self.viewLayout.addSpacing(10)

        # Action buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.backupBtn = PrimaryPushButton(FIF.SAVE, '立即备份')
        self.exportBtn = PushButton(FIF.SHARE, '导出数据库')
        self.importBtn = PushButton(FIF.DOWNLOAD, '导入数据库')

        btn_layout.addWidget(self.backupBtn)
        btn_layout.addWidget(self.exportBtn)
        btn_layout.addWidget(self.importBtn)
        btn_layout.addStretch()

        self.viewLayout.addLayout(btn_layout)

        self.viewLayout.addSpacing(10)

        # Backup list
        self.viewLayout.addWidget(BodyLabel('备份列表:'))

        self.table = TableWidget()
        self.table.setBorderVisible(True)
        self.table.setBorderRadius(8)
        self.table.setWordWrap(False)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['文件名', '时间', '大小', '操作'])
        self.table.verticalHeader().hide()
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setFixedHeight(250)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        self.table.setColumnWidth(3, 80)

        self.viewLayout.addWidget(self.table)

        # Hide default yes button, only show cancel as "close"
        self.yesButton.hide()
        self.cancelButton.setText('关闭')

        self.widget.setMinimumWidth(600)

        # Connections
        self.backupBtn.clicked.connect(self._on_backup)
        self.exportBtn.clicked.connect(self._on_export)
        self.importBtn.clicked.connect(self._on_import)

    def _load_backups(self):
        backups = self._backup_manager.list_backups()
        self.table.setRowCount(len(backups))
        for i, b in enumerate(backups):
            self.table.setItem(i, 0, QTableWidgetItem(b['name']))
            self.table.setItem(i, 1, QTableWidgetItem(b['time']))
            size_kb = b['size'] / 1024
            self.table.setItem(i, 2, QTableWidgetItem('{:.1f} KB'.format(size_kb)))

            restore_btn = PushButton('恢复')
            restore_btn.setFixedSize(65, 28)
            backup_path = b['path']
            restore_btn.clicked.connect(
                lambda checked, p=backup_path: self._on_restore(p))
            self.table.setCellWidget(i, 3, restore_btn)

    def _on_backup(self):
        path = self._backup_manager.create_backup(prefix='manual')
        if path:
            self._load_backups()
            InfoBar.success(
                title='备份成功', content='备份已创建',
                parent=self.parent(), position=InfoBarPosition.TOP, duration=2000)

    def _on_restore(self, backup_path):
        w = MessageBox('确认恢复', '恢复备份将覆盖当前数据库，确定继续吗？',
                       self.parent())
        w.yesButton.setText('确认')
        w.cancelButton.setText('取消')
        if w.exec_():
            if self._backup_manager.restore_backup(backup_path):
                InfoBar.success(
                    title='恢复成功', content='数据库已恢复，请重启应用',
                    parent=self.parent(), position=InfoBarPosition.TOP, duration=5000)

    def _on_export(self):
        path, _ = QFileDialog.getSaveFileName(
            self.parent(), '导出数据库', 'pos_export.db',
            '数据库文件 (*.db)')
        if path:
            if self._backup_manager.export_database(path):
                InfoBar.success(
                    title='导出成功', content='数据库已导出到 {}'.format(path),
                    parent=self.parent(), position=InfoBarPosition.TOP, duration=3000)

    def _on_import(self):
        path, _ = QFileDialog.getOpenFileName(
            self.parent(), '导入数据库', '',
            '数据库文件 (*.db)')
        if path:
            w = MessageBox('确认导入', '导入将覆盖当前数据库，确定继续吗？',
                           self.parent())
            w.yesButton.setText('确认')
            w.cancelButton.setText('取消')
            if w.exec_():
                if self._backup_manager.import_database(path):
                    InfoBar.success(
                        title='导入成功', content='数据库已导入，请重启应用',
                        parent=self.parent(), position=InfoBarPosition.TOP, duration=5000)
