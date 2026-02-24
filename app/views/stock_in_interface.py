# coding: utf-8
from PyQt5.QtCore import Qt, QTimer, QEvent
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QHeaderView,
                              QTableWidgetItem, QAbstractItemView, QApplication)

from qfluentwidgets import (TableWidget, SimpleCardWidget, BodyLabel,
                            SubtitleLabel, CaptionLabel, InfoBar, InfoBarPosition,
                            FluentIcon as FIF, setFont)

from ..models.product import ProductModel
from ..models.stock_in import StockInModel
from ..common.auth import AuthManager
from ..common.signal_bus import signal_bus
from ..dialogs.stock_in_dialog import StockInDialog


class StockInInterface(QWidget):
    """Stock-in management interface with barcode scanning."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._barcode_buffer = ''
        self._barcode_timer = QTimer(self)
        self._barcode_timer.setSingleShot(True)
        self._barcode_timer.setInterval(100)
        self._barcode_timer.timeout.connect(self._flush_barcode_buffer)
        self._init_ui()
        self._load_records()

        signal_bus.stock_changed.connect(self._load_records)

        QTimer.singleShot(200, self._install_global_filter)

    def _install_global_filter(self):
        top = self.window()
        if top:
            top.installEventFilter(self)

    def eventFilter(self, obj, event):
        """Capture barcode scans when this interface is visible."""
        if not self.isVisible():
            return False

        if event.type() == QEvent.KeyPress:
            focused = QApplication.focusWidget()
            if (focused and focused is not self
                    and hasattr(focused, 'text')
                    and callable(getattr(focused, 'setText', None))):
                return False

            key = event.key()
            text = event.text()

            if key in (Qt.Key_Return, Qt.Key_Enter):
                if self._barcode_buffer:
                    self._process_barcode(self._barcode_buffer.strip())
                    self._barcode_buffer = ''
                    self._barcode_timer.stop()
                    return True
            elif text and text.isprintable() and key not in (
                Qt.Key_Escape, Qt.Key_Tab, Qt.Key_Backspace,
                Qt.Key_F1, Qt.Key_F2, Qt.Key_F3, Qt.Key_F4,
                Qt.Key_F5, Qt.Key_F6, Qt.Key_F7, Qt.Key_F8,
                Qt.Key_F9, Qt.Key_F10, Qt.Key_F11, Qt.Key_F12,
                Qt.Key_Delete,
            ):
                self._barcode_buffer += text
                self._barcode_timer.start()
                return True

        return False

    def _flush_barcode_buffer(self):
        self._barcode_buffer = ''

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(10)

        # === Hint card ===
        hint_card = SimpleCardWidget(self)
        hint_layout = QVBoxLayout(hint_card)
        hint_layout.setContentsMargins(25, 20, 25, 20)
        hint_layout.setSpacing(8)

        hint_title = SubtitleLabel('商品入库')
        hint_layout.addWidget(hint_title)

        hint_text = BodyLabel('请扫描商品条码，系统将自动弹出入库窗口')
        hint_text.setStyleSheet('color: gray;')
        hint_layout.addWidget(hint_text)

        layout.addWidget(hint_card)

        # === Records table ===
        records_title = SubtitleLabel('进货记录')
        layout.addWidget(records_title)

        self.table = TableWidget(self)
        self.table.setBorderVisible(True)
        self.table.setBorderRadius(8)
        self.table.setWordWrap(False)
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ['时间', '条码', '商品名称', '数量', '进价', '总额', '操作员'])
        self.table.verticalHeader().hide()
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)

        layout.addWidget(self.table, 1)

    def _process_barcode(self, barcode):
        if not barcode:
            return

        product = ProductModel.get_by_barcode(barcode)
        if not product:
            InfoBar.error(
                title='商品未找到',
                content='条码 {} 未在商品库中，请先在商品管理中添加'.format(barcode),
                parent=self, position=InfoBarPosition.TOP, duration=4000)
            return

        dialog = StockInDialog(product, self.window())
        if dialog.exec_():
            user = AuthManager.current_user()
            result = StockInModel.create(
                product_id=product['id'],
                barcode=product['barcode'],
                product_name=product['name'],
                quantity=dialog.get_quantity(),
                purchase_price=dialog.get_price(),
                operator_id=user['id'],
                note=dialog.get_note()
            )
            if result:
                InfoBar.success(
                    title='入库成功',
                    content='{} 入库 {} 件'.format(
                        product['name'], dialog.get_quantity()),
                    parent=self, position=InfoBarPosition.TOP, duration=3000)
                self._load_records()
                signal_bus.stock_changed.emit()
                signal_bus.product_changed.emit()
            else:
                InfoBar.error(
                    title='入库失败', content='操作失败，请重试',
                    parent=self, position=InfoBarPosition.TOP, duration=3000)

    def _load_records(self):
        records = StockInModel.get_recent(100)
        self.table.setRowCount(len(records))
        for i, r in enumerate(records):
            self.table.setItem(i, 0, QTableWidgetItem(r['created_at']))
            self.table.setItem(i, 1, QTableWidgetItem(r['barcode']))
            self.table.setItem(i, 2, QTableWidgetItem(r['product_name']))
            self.table.setItem(i, 3, QTableWidgetItem(str(r['quantity'])))
            self.table.setItem(i, 4, QTableWidgetItem('{:.2f}'.format(r['purchase_price'])))
            self.table.setItem(i, 5, QTableWidgetItem('{:.2f}'.format(r['total_cost'])))
            self.table.setItem(i, 6, QTableWidgetItem(r.get('operator_name', '')))
