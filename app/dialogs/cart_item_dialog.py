# coding: utf-8
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QHBoxLayout

from qfluentwidgets import (MessageBoxBase, LineEdit, BodyLabel,
                            SubtitleLabel, PushButton, SpinBox,
                            FluentIcon as FIF, setCustomStyleSheet)


class CartItemDialog(MessageBoxBase):
    """Dialog for editing a single cart item's quantity, discount or removing it."""

    RESULT_UPDATE = 1
    RESULT_DELETE = 2

    def __init__(self, item, parent=None):
        super().__init__(parent)
        self._item = item
        self._quantity = item['quantity']
        self._discount_rate = item['discount_rate']
        self._action = None
        self._init_ui()

    def _init_ui(self):
        title = SubtitleLabel(self._item['name'])
        self.viewLayout.addWidget(title)

        self.viewLayout.addSpacing(5)

        info = BodyLabel('单价: ¥{:.2f}'.format(self._item['unit_price']))
        self.viewLayout.addWidget(info)

        self.viewLayout.addSpacing(10)

        # Quantity
        qty_row = QHBoxLayout()
        qty_row.setSpacing(12)
        qty_label = BodyLabel('数量')
        qty_label.setFixedWidth(50)
        qty_row.addWidget(qty_label)

        self.quantitySpin = SpinBox()
        self.quantitySpin.setRange(1, 99999)
        self.quantitySpin.setValue(self._item['quantity'])
        self.quantitySpin.setFixedWidth(150)
        qty_row.addWidget(self.quantitySpin)
        qty_row.addStretch()
        self.viewLayout.addLayout(qty_row)

        self.viewLayout.addSpacing(5)

        # Discount
        discount_row = QHBoxLayout()
        discount_row.setSpacing(12)
        discount_label = BodyLabel('折扣率')
        discount_label.setFixedWidth(50)
        discount_row.addWidget(discount_label)

        self.discountEdit = LineEdit()
        self.discountEdit.setPlaceholderText('1-100，如 85 表示 85折')
        current_pct = int(self._discount_rate * 100)
        self.discountEdit.setText(str(current_pct))
        self.discountEdit.setFixedWidth(150)
        discount_row.addWidget(self.discountEdit)
        discount_row.addStretch()
        self.viewLayout.addLayout(discount_row)

        self.viewLayout.addSpacing(10)

        self.deleteBtn = PushButton(FIF.DELETE, '删除此商品')
        self.deleteBtn.setIcon(FIF.DELETE.icon(color=QColor('#d32f2f')))
        qss = 'PushButton { color: #d32f2f; border: 1px solid #d32f2f; }'
        qss_dark = 'PushButton { color: #ef5350; border: 1px solid #ef5350; }'
        setCustomStyleSheet(self.deleteBtn, qss, qss_dark)
        self.deleteBtn.clicked.connect(self._on_delete)
        self.viewLayout.addWidget(self.deleteBtn)

        self.yesButton.setText('确认')
        self.cancelButton.setText('取消')

        self.widget.setMinimumWidth(400)

    def _on_delete(self):
        self._action = self.RESULT_DELETE
        self.accept()

    def get_action(self):
        return self._action

    def get_quantity(self):
        return self._quantity

    def get_discount_rate(self):
        return self._discount_rate

    def accept(self):
        if self._action == self.RESULT_DELETE:
            super().accept()
            return

        try:
            value = float(self.discountEdit.text().strip())
            if not (1 <= value <= 100):
                return
        except ValueError:
            return

        qty = self.quantitySpin.value()
        if qty <= 0:
            return

        self._quantity = qty
        self._discount_rate = value / 100.0
        self._action = self.RESULT_UPDATE
        super().accept()
