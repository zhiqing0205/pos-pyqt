# coding: utf-8
from PyQt5.QtWidgets import QHBoxLayout

from qfluentwidgets import (MessageBoxBase, LineEdit, BodyLabel,
                            SubtitleLabel, PushButton, FluentIcon as FIF)


class CartItemDialog(MessageBoxBase):
    """Dialog for editing a single cart item's discount or removing it."""

    RESULT_DISCOUNT = 1
    RESULT_DELETE = 2

    def __init__(self, item, parent=None):
        super().__init__(parent)
        self._item = item
        self._discount_rate = item['discount_rate']
        self._action = None
        self._init_ui()

    def _init_ui(self):
        title = SubtitleLabel(self._item['name'])
        self.viewLayout.addWidget(title)

        self.viewLayout.addSpacing(5)

        info = BodyLabel('单价: ¥{:.2f}  数量: {}'.format(
            self._item['unit_price'], self._item['quantity']))
        self.viewLayout.addWidget(info)

        self.viewLayout.addSpacing(10)

        hint = BodyLabel('折扣率（例如：85 表示 85折）')
        self.viewLayout.addWidget(hint)

        self.discountEdit = LineEdit()
        self.discountEdit.setPlaceholderText('输入折扣率 (1-100)')
        current_pct = int(self._discount_rate * 100)
        self.discountEdit.setText(str(current_pct))
        self.discountEdit.setFixedWidth(200)
        self.viewLayout.addWidget(self.discountEdit)

        self.viewLayout.addSpacing(10)

        self.deleteBtn = PushButton(FIF.DELETE, '删除此商品')
        self.deleteBtn.setStyleSheet(
            'PushButton { color: #d32f2f; border-color: #d32f2f; }'
            'PushButton:hover { background: #ffebee; }'
        )
        self.deleteBtn.clicked.connect(self._on_delete)
        self.viewLayout.addWidget(self.deleteBtn)

        self.yesButton.setText('确认折扣')
        self.cancelButton.setText('取消')

        self.widget.setMinimumWidth(380)

    def _on_delete(self):
        self._action = self.RESULT_DELETE
        self.accept()

    def get_action(self):
        return self._action

    def get_discount_rate(self):
        return self._discount_rate

    def accept(self):
        if self._action == self.RESULT_DELETE:
            super().accept()
            return

        try:
            value = float(self.discountEdit.text().strip())
            if 1 <= value <= 100:
                self._discount_rate = value / 100.0
                self._action = self.RESULT_DISCOUNT
                super().accept()
        except ValueError:
            pass
