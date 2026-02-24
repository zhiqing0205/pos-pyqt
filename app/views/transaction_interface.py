# coding: utf-8
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QHeaderView,
                              QTableWidgetItem, QAbstractItemView)

from qfluentwidgets import (SearchLineEdit, TableWidget, InfoBar, InfoBarPosition,
                            FluentIcon as FIF, CaptionLabel)

from ..models.transaction import TransactionModel
from ..dialogs.transaction_detail_dialog import TransactionDetailDialog
from ..common.signal_bus import signal_bus


_PAYMENT_NAMES = {
    'cash': '现金',
    'wechat': '微信支付',
    'alipay': '支付宝',
}


class TransactionInterface(QWidget):
    """Transaction history interface, visible to all users."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._transactions = []
        self._init_ui()
        self._load_transactions()

        signal_bus.transaction_completed.connect(self._load_transactions)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(10)

        # Top bar
        top_layout = QHBoxLayout()
        top_layout.setSpacing(10)

        self.searchEdit = SearchLineEdit()
        self.searchEdit.setPlaceholderText('搜索交易（单号、收银员）...')
        self.searchEdit.setFixedHeight(36)
        top_layout.addWidget(self.searchEdit, 1)

        self.hintLabel = CaptionLabel('双击查看交易详情')
        self.hintLabel.setStyleSheet('color: gray;')
        top_layout.addWidget(self.hintLabel)

        layout.addLayout(top_layout)

        # Table
        self.table = TableWidget(self)
        self.table.setBorderVisible(True)
        self.table.setBorderRadius(8)
        self.table.setWordWrap(False)
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ['交易单号', '时间', '收银员', '商品总额', '优惠', '实收金额', '支付方式'])
        self.table.verticalHeader().hide()
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)

        layout.addWidget(self.table, 1)

        # Connections
        self.searchEdit.returnPressed.connect(self._on_search)
        self.searchEdit.textChanged.connect(self._on_search_changed)
        self.table.doubleClicked.connect(self._on_double_click)

    def _on_search_changed(self, text):
        if not text:
            self._load_transactions()

    def _on_search(self):
        keyword = self.searchEdit.text().strip()
        if keyword:
            filtered = [t for t in self._transactions
                        if keyword.lower() in t.get('transaction_no', '').lower()
                        or keyword.lower() in t.get('username', '').lower()]
            self._display_transactions(filtered)
        else:
            self._load_transactions()

    def _load_transactions(self):
        self._transactions = TransactionModel.get_recent(200)
        self._display_transactions(self._transactions)

    def _display_transactions(self, transactions):
        self.table.setRowCount(len(transactions))
        for i, t in enumerate(transactions):
            self.table.setItem(i, 0, QTableWidgetItem(t['transaction_no']))
            self.table.setItem(i, 1, QTableWidgetItem(t['created_at']))
            self.table.setItem(i, 2, QTableWidgetItem(t.get('username', '')))
            self.table.setItem(i, 3, QTableWidgetItem('¥{:.2f}'.format(t['total_amount'])))
            self.table.setItem(i, 4, QTableWidgetItem('¥{:.2f}'.format(t['discount_amount'])))

            final_item = QTableWidgetItem('¥{:.2f}'.format(t['final_amount']))
            self.table.setItem(i, 5, final_item)

            method = _PAYMENT_NAMES.get(t['payment_method'], t['payment_method'])
            self.table.setItem(i, 6, QTableWidgetItem(method))

    def _on_double_click(self, index):
        row = index.row()
        # Get from displayed rows
        keyword = self.searchEdit.text().strip()
        if keyword:
            displayed = [t for t in self._transactions
                         if keyword.lower() in t.get('transaction_no', '').lower()
                         or keyword.lower() in t.get('username', '').lower()]
        else:
            displayed = self._transactions

        if 0 <= row < len(displayed):
            txn = displayed[row]
            dialog = TransactionDetailDialog(txn, self.window())
            dialog.exec_()
