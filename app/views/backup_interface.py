# coding: utf-8
import os

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QHeaderView,
                              QTableWidgetItem, QAbstractItemView,
                              QScrollArea, QFrame, QFileDialog)

from qfluentwidgets import (PushButton, PrimaryPushButton, LineEdit,
                            TableWidget, SimpleCardWidget, BodyLabel,
                            SubtitleLabel, CaptionLabel, SpinBox,
                            CheckBox, InfoBar, InfoBarPosition,
                            FluentIcon as FIF, MessageBox, setFont,
                            setCustomStyleSheet)

from ..common.backup import BackupManager
from ..common.config import BACKUP_DIR, MAX_BACKUPS
from ..models.settings import SettingsModel
from ..common.signal_bus import signal_bus


class BackupInterface(QWidget):
    """Backup management interface for admin users."""

    def __init__(self, backup_manager, parent=None):
        super().__init__(parent)
        self._backup_manager = backup_manager
        self._init_ui()
        self._load_settings()
        self._load_backups()

    def _init_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet('QScrollArea { background: transparent; }')

        container = QWidget()
        container.setStyleSheet('QWidget { background: transparent; }')
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(15)

        # ── Settings Card ──
        settings_card = SimpleCardWidget(self)
        sc_layout = QVBoxLayout(settings_card)
        sc_layout.setContentsMargins(25, 20, 25, 20)
        sc_layout.setSpacing(10)

        sc_title = SubtitleLabel('备份设置')
        sc_layout.addWidget(sc_title)

        sc_hint = CaptionLabel('设置自动备份的文件夹和时间')
        sc_hint.setStyleSheet('color: gray;')
        sc_layout.addWidget(sc_hint)
        sc_layout.addSpacing(5)

        # Backup folder row
        folder_row = QHBoxLayout()
        folder_row.setSpacing(12)
        folder_label = BodyLabel('备份文件夹')
        folder_label.setFixedWidth(100)
        folder_row.addWidget(folder_label)

        self.folderEdit = LineEdit()
        self.folderEdit.setPlaceholderText('选择备份文件夹...')
        self.folderEdit.setReadOnly(True)
        folder_row.addWidget(self.folderEdit, 1)

        self.folderBtn = PushButton(FIF.FOLDER, '浏览')
        self.folderBtn.clicked.connect(self._on_browse_folder)
        folder_row.addWidget(self.folderBtn)

        sc_layout.addLayout(folder_row)

        # Backup time row
        time_row = QHBoxLayout()
        time_row.setSpacing(12)
        time_label = BodyLabel('每日备份时间')
        time_label.setFixedWidth(100)
        time_row.addWidget(time_label)

        self.hourSpin = SpinBox()
        self.hourSpin.setRange(0, 23)
        self.hourSpin.setValue(2)
        self.hourSpin.setFixedWidth(120)
        time_row.addWidget(self.hourSpin)

        time_sep = BodyLabel('时')
        time_row.addWidget(time_sep)

        self.minuteSpin = SpinBox()
        self.minuteSpin.setRange(0, 59)
        self.minuteSpin.setValue(0)
        self.minuteSpin.setFixedWidth(120)
        time_row.addWidget(self.minuteSpin)

        time_suffix = BodyLabel('分')
        time_row.addWidget(time_suffix)
        time_row.addStretch()

        sc_layout.addLayout(time_row)

        # Auto-backup on close
        self.autoBackupCheck = CheckBox('关闭程序前自动备份到备份文件夹')
        self.autoBackupCheck.setChecked(True)
        sc_layout.addLayout(self._wrap_row(self.autoBackupCheck))

        # Max backups row
        max_row = QHBoxLayout()
        max_row.setSpacing(12)
        max_label = BodyLabel('备份保留数量')
        max_label.setFixedWidth(100)
        max_row.addWidget(max_label)

        self.maxBackupsSpin = SpinBox()
        self.maxBackupsSpin.setRange(1, 9999)
        self.maxBackupsSpin.setValue(MAX_BACKUPS)
        self.maxBackupsSpin.setFixedWidth(120)
        max_row.addWidget(self.maxBackupsSpin)

        max_hint = CaptionLabel('超出数量的旧备份将自动删除')
        max_hint.setStyleSheet('color: gray;')
        max_row.addWidget(max_hint)
        max_row.addStretch()

        sc_layout.addLayout(max_row)

        # Save settings button
        save_row = QHBoxLayout()
        save_row.addStretch()
        self.saveSettingsBtn = PrimaryPushButton(FIF.SAVE, '保存设置')
        self.saveSettingsBtn.setFixedHeight(36)
        self.saveSettingsBtn.clicked.connect(self._save_settings)
        save_row.addWidget(self.saveSettingsBtn)
        sc_layout.addLayout(save_row)

        layout.addWidget(settings_card)

        # ── Actions Card ──
        action_card = SimpleCardWidget(self)
        ac_layout = QVBoxLayout(action_card)
        ac_layout.setContentsMargins(25, 20, 25, 20)
        ac_layout.setSpacing(10)

        ac_title = SubtitleLabel('备份操作')
        ac_layout.addWidget(ac_title)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.backupBtn = PrimaryPushButton(FIF.SAVE, '立即备份')
        self.exportBtn = PushButton(FIF.SHARE, '导出数据库')
        self.importBtn = PushButton(FIF.DOWNLOAD, '导入数据库')

        btn_layout.addWidget(self.backupBtn)
        btn_layout.addWidget(self.exportBtn)
        btn_layout.addWidget(self.importBtn)
        btn_layout.addStretch()

        self.resetDemoBtn = PushButton(FIF.DELETE, '清除演示数据')
        setCustomStyleSheet(self.resetDemoBtn,
            'PushButton { color: #d13438; border: 1px solid #d13438; }'
            'PushButton:hover { background: #d13438; color: white; }'
            'PushButton:pressed { background: #a4262c; color: white; border: 1px solid #a4262c; }',
            'PushButton { color: #ff6767; border: 1px solid #ff6767; }'
            'PushButton:hover { background: #ff6767; color: black; }'
            'PushButton:pressed { background: #d13438; color: white; border: 1px solid #d13438; }'
        )
        btn_layout.addWidget(self.resetDemoBtn)

        ac_layout.addLayout(btn_layout)

        layout.addWidget(action_card)

        # ── Backup List Card ──
        list_card = SimpleCardWidget(self)
        lc_layout = QVBoxLayout(list_card)
        lc_layout.setContentsMargins(25, 20, 25, 20)
        lc_layout.setSpacing(10)

        lc_title = SubtitleLabel('备份列表')
        lc_layout.addWidget(lc_title)

        self.table = TableWidget()
        self.table.setBorderVisible(True)
        self.table.setBorderRadius(8)
        self.table.setWordWrap(False)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['文件名', '时间', '大小', '操作'])
        self.table.verticalHeader().hide()
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        self.table.setColumnWidth(3, 80)

        lc_layout.addWidget(self.table)

        layout.addWidget(list_card, 1)

        scroll.setWidget(container)
        outer.addWidget(scroll)

        # Connections
        self.backupBtn.clicked.connect(self._on_backup)
        self.exportBtn.clicked.connect(self._on_export)
        self.importBtn.clicked.connect(self._on_import)
        self.resetDemoBtn.clicked.connect(self._on_reset_demo)

    @staticmethod
    def _wrap_row(widget):
        row = QHBoxLayout()
        row.setSpacing(12)
        spacer = QWidget()
        spacer.setFixedWidth(100)
        row.addWidget(spacer)
        row.addWidget(widget, 1)
        return row

    def _load_settings(self):
        folder = SettingsModel.get('backup_folder', BACKUP_DIR)
        self.folderEdit.setText(folder)

        hour = SettingsModel.get('backup_hour', '2')
        try:
            self.hourSpin.setValue(int(hour))
        except (ValueError, TypeError):
            self.hourSpin.setValue(2)

        minute = SettingsModel.get('backup_minute', '0')
        try:
            self.minuteSpin.setValue(int(minute))
        except (ValueError, TypeError):
            self.minuteSpin.setValue(0)

        auto = SettingsModel.get('backup_on_close', '1')
        self.autoBackupCheck.setChecked(auto == '1')

        max_b = SettingsModel.get('max_backups', str(MAX_BACKUPS))
        try:
            self.maxBackupsSpin.setValue(int(max_b))
        except (ValueError, TypeError):
            self.maxBackupsSpin.setValue(MAX_BACKUPS)

    def _save_settings(self):
        folder = self.folderEdit.text().strip()
        if folder:
            SettingsModel.set('backup_folder', folder)
            # Ensure the folder exists
            os.makedirs(folder, exist_ok=True)

        SettingsModel.set('backup_hour', str(self.hourSpin.value()))
        SettingsModel.set('backup_minute', str(self.minuteSpin.value()))
        SettingsModel.set('backup_on_close',
                          '1' if self.autoBackupCheck.isChecked() else '0')
        SettingsModel.set('max_backups', str(self.maxBackupsSpin.value()))

        # Update backup manager with new settings
        self._backup_manager.update_settings(
            backup_dir=folder,
            backup_hour=self.hourSpin.value(),
            backup_minute=self.minuteSpin.value(),
            max_backups=self.maxBackupsSpin.value()
        )

        InfoBar.success(
            title='保存成功', content='备份设置已保存',
            parent=self, position=InfoBarPosition.TOP, duration=2000)

    def _on_browse_folder(self):
        current = self.folderEdit.text() or BACKUP_DIR
        folder = QFileDialog.getExistingDirectory(
            self, '选择备份文件夹', current)
        if folder:
            self.folderEdit.setText(folder)

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
                parent=self, position=InfoBarPosition.TOP, duration=2000)

    def _on_restore(self, backup_path):
        w = MessageBox('确认恢复', '恢复备份将覆盖当前数据库，确定继续吗？',
                       self.window())
        w.yesButton.setText('确认')
        w.cancelButton.setText('取消')
        if w.exec_():
            if BackupManager.restore_backup(backup_path):
                InfoBar.success(
                    title='恢复成功', content='数据库已恢复，请重启应用',
                    parent=self, position=InfoBarPosition.TOP, duration=5000)

    def _on_export(self):
        path, _ = QFileDialog.getSaveFileName(
            self, '导出数据库', 'pos_export.db',
            '数据库文件 (*.db)')
        if path:
            if BackupManager.export_database(path):
                InfoBar.success(
                    title='导出成功', content='数据库已导出到 {}'.format(path),
                    parent=self, position=InfoBarPosition.TOP, duration=3000)

    def _on_import(self):
        path, _ = QFileDialog.getOpenFileName(
            self, '导入数据库', '',
            '数据库文件 (*.db)')
        if path:
            w = MessageBox('确认导入', '导入将覆盖当前数据库，确定继续吗？',
                           self.window())
            w.yesButton.setText('确认')
            w.cancelButton.setText('取消')
            if w.exec_():
                if BackupManager.import_database(path):
                    InfoBar.success(
                        title='导入成功', content='数据库已导入，请重启应用',
                        parent=self, position=InfoBarPosition.TOP, duration=5000)

    def _on_reset_demo(self):
        w = MessageBox(
            '清除演示数据',
            '此操作将删除所有演示数据（交易记录、进货记录、演示用户），'
            '仅保留管理员账号和商品数据。\n\n确定继续吗？',
            self.window())
        w.yesButton.setText('确认清除')
        w.cancelButton.setText('取消')
        if w.exec_():
            from ..common.database import get_connection
            conn = get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("DELETE FROM transaction_items")
                cursor.execute("DELETE FROM transactions")
                cursor.execute("DELETE FROM stock_in_records")
                cursor.execute("DELETE FROM users WHERE role != 'admin'")
                conn.commit()
                conn.close()
                InfoBar.success(
                    title='清除完成',
                    content='演示数据已清除，系统已恢复为初始状态',
                    parent=self, position=InfoBarPosition.TOP, duration=3000)
                signal_bus.transaction_completed.emit()
                signal_bus.stock_changed.emit()
                signal_bus.user_changed.emit()
            except Exception:
                conn.rollback()
                conn.close()
                InfoBar.error(
                    title='清除失败', content='操作出错，请重试',
                    parent=self, position=InfoBarPosition.TOP, duration=3000)
