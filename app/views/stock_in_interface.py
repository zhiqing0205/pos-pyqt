# coding: utf-8
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QHeaderView,
                              QTableWidgetItem, QAbstractItemView)

from qfluentwidgets import (SearchLineEdit, LineEdit, PushButton, PrimaryPushButton,
                            TableWidget, SimpleCardWidget, BodyLabel,
                            SubtitleLabel, InfoBar, InfoBarPosition,
                            FluentIcon as FIF, setFont)

from ..models.product import ProductModel
from ..models.stock_in import StockInModel
from ..common.auth import AuthManager
from ..common.signal_bus import signal_bus


class StockInInterface(QWidget):
    """Stock-in management interface."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_product = None
        self._init_ui()
        self._load_records()

        signal_bus.stock_changed.connect(self._load_records)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(10)

        # === Input card ===
        input_card = SimpleCardWidget(self)
        card_layout = QVBoxLayout(input_card)
        card_layout.setContentsMargins(20, 15, 20, 15)
        card_layout.setSpacing(10)

        card_title = SubtitleLabel('商品入库')
        card_layout.addWidget(card_title)

        # Barcode scan row
        scan_layout = QHBoxLayout()
        scan_layout.setSpacing(10)

        self.barcodeEdit = SearchLineEdit()
        self.barcodeEdit.setPlaceholderText('扫描或输入商品条码...')
        self.barcodeEdit.setFixedHeight(36)
        scan_layout.addWidget(self.barcodeEdit, 1)

        card_layout.addLayout(scan_layout)

        # Product info display
        self.productInfoLabel = BodyLabel('请先扫描商品条码')
        self.productInfoLabel.setStyleSheet('color: gray;')
        card_layout.addWidget(self.productInfoLabel)

        # Quantity and price row
        qty_price_layout = QHBoxLayout()
        qty_price_layout.setSpacing(15)

        qty_price_layout.addWidget(BodyLabel('进货数量:'))
        self.quantityEdit = LineEdit()
        self.quantityEdit.setPlaceholderText('数量')
        self.quantityEdit.setFixedWidth(100)
        qty_price_layout.addWidget(self.quantityEdit)

        qty_price_layout.addWidget(BodyLabel('进价:'))
        self.priceEdit = LineEdit()
        self.priceEdit.setPlaceholderText('单价')
        self.priceEdit.setFixedWidth(100)
        qty_price_layout.addWidget(self.priceEdit)

        qty_price_layout.addWidget(BodyLabel('备注:'))
        self.noteEdit = LineEdit()
        self.noteEdit.setPlaceholderText('备注（可选）')
        qty_price_layout.addWidget(self.noteEdit, 1)

        self.confirmBtn = PrimaryPushButton(FIF.ADD, '确认入库')
        qty_price_layout.addWidget(self.confirmBtn)

        card_layout.addLayout(qty_price_layout)

        layout.addWidget(input_card)

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

        # === Connections ===
        self.barcodeEdit.returnPressed.connect(self._on_barcode_enter)
        self.confirmBtn.clicked.connect(self._on_confirm)

    def _on_barcode_enter(self):
        barcode = self.barcodeEdit.text().strip()
        if not barcode:
            return

        product = ProductModel.get_by_barcode(barcode)
        if product:
            self._current_product = product
            self.productInfoLabel.setText(
                '商品: {} | 当前库存: {} | 售价: ¥{:.2f}'.format(
                    product['name'], product['stock_quantity'],
                    product['selling_price']))
            self.productInfoLabel.setStyleSheet('color: #2e7d32;')
            self.priceEdit.setText('{:.2f}'.format(product['purchase_price']))
            self.quantityEdit.setFocus()
        else:
            self._current_product = None
            self.productInfoLabel.setText('未找到条码 {} 对应的商品'.format(barcode))
            self.productInfoLabel.setStyleSheet('color: #d32f2f;')

    def _on_confirm(self):
        if not self._current_product:
            InfoBar.warning(
                title='提示', content='请先扫描有效的商品条码',
                parent=self, position=InfoBarPosition.TOP, duration=2000)
            return

        try:
            quantity = int(self.quantityEdit.text())
            price = float(self.priceEdit.text())
            if quantity <= 0 or price < 0:
                raise ValueError
        except (ValueError, TypeError):
            InfoBar.error(
                title='输入错误', content='请输入有效的数量和价格',
                parent=self, position=InfoBarPosition.TOP, duration=2000)
            return

        user = AuthManager.current_user()
        result = StockInModel.create(
            product_id=self._current_product['id'],
            barcode=self._current_product['barcode'],
            product_name=self._current_product['name'],
            quantity=quantity,
            purchase_price=price,
            operator_id=user['id'],
            note=self.noteEdit.text().strip()
        )

        if result:
            InfoBar.success(
                title='入库成功',
                content='{} 入库 {} 件'.format(
                    self._current_product['name'], quantity),
                parent=self, position=InfoBarPosition.TOP, duration=3000)
            self._current_product = None
            self.barcodeEdit.clear()
            self.quantityEdit.clear()
            self.priceEdit.clear()
            self.noteEdit.clear()
            self.productInfoLabel.setText('请先扫描商品条码')
            self.productInfoLabel.setStyleSheet('color: gray;')
            self._load_records()
            signal_bus.stock_changed.emit()
            signal_bus.product_changed.emit()
            self.barcodeEdit.setFocus()
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
