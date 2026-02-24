# coding: utf-8
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QHBoxLayout, QVBoxLayout, QHeaderView,
                              QTableWidgetItem, QAbstractItemView)

from qfluentwidgets import (MessageBoxBase, BodyLabel, SubtitleLabel,
                            CaptionLabel, TableWidget, setFont)

from ..models.transaction import TransactionModel


_PAYMENT_NAMES = {
    'cash': '现金',
    'wechat': '微信支付',
    'alipay': '支付宝',
}


class TransactionDetailDialog(MessageBoxBase):
    """Dialog showing transaction details."""

    def __init__(self, transaction, parent=None):
        super().__init__(parent)
        self._txn = transaction
        self._init_ui()

    def _init_ui(self):
        title = SubtitleLabel('交易详情')
        self.viewLayout.addWidget(title)

        self.viewLayout.addSpacing(5)

        # Transaction info
        txn = self._txn
        info_lines = [
            ('交易单号', txn['transaction_no']),
            ('交易时间', txn['created_at']),
            ('收银员', txn.get('username', '')),
            ('支付方式', _PAYMENT_NAMES.get(txn['payment_method'], txn['payment_method'])),
        ]
        for label_text, value_text in info_lines:
            row = QHBoxLayout()
            label = CaptionLabel(label_text)
            label.setFixedWidth(70)
            label.setStyleSheet('color: gray;')
            value = BodyLabel(str(value_text))
            row.addWidget(label)
            row.addWidget(value, 1)
            self.viewLayout.addLayout(row)

        self.viewLayout.addSpacing(5)

        # Amount row
        amount_row = QHBoxLayout()
        amount_row.setSpacing(20)

        for label_text, amount in [
            ('商品总额', txn['total_amount']),
            ('折扣优惠', txn['discount_amount']),
            ('实收金额', txn['final_amount']),
        ]:
            col = QVBoxLayout()
            col.setSpacing(2)
            lbl = CaptionLabel(label_text)
            lbl.setStyleSheet('color: gray;')
            val = BodyLabel('¥{:.2f}'.format(amount))
            if label_text == '实收金额':
                val.setStyleSheet('color: #d32f2f;')
                setFont(val, 16)
            col.addWidget(lbl, 0, Qt.AlignCenter)
            col.addWidget(val, 0, Qt.AlignCenter)
            amount_row.addLayout(col)

        self.viewLayout.addLayout(amount_row)

        self.viewLayout.addSpacing(10)

        # Items table
        items = TransactionModel.get_items(txn['id'])

        table = TableWidget()
        table.setBorderVisible(True)
        table.setBorderRadius(6)
        table.setWordWrap(False)
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(['商品', '单价', '数量', '折扣', '小计'])
        table.verticalHeader().hide()
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setFixedHeight(min(38 + len(items) * 38, 300))

        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)

        table.setRowCount(len(items))
        for i, item in enumerate(items):
            table.setItem(i, 0, QTableWidgetItem(item['product_name']))
            table.setItem(i, 1, QTableWidgetItem('¥{:.2f}'.format(item['unit_price'])))
            table.setItem(i, 2, QTableWidgetItem(str(item['quantity'])))
            table.setItem(i, 3, QTableWidgetItem('{:.0f}%'.format(item['discount_rate'] * 100)))
            table.setItem(i, 4, QTableWidgetItem('¥{:.2f}'.format(item['subtotal'])))

        self.viewLayout.addWidget(table)

        self.yesButton.setText('关闭')
        self.cancelButton.hide()

        self.widget.setMinimumWidth(500)
