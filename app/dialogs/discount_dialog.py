# coding: utf-8
from PyQt5.QtWidgets import QVBoxLayout

from qfluentwidgets import (MessageBoxBase, LineEdit, BodyLabel,
                            SubtitleLabel, setFont)


class DiscountDialog(MessageBoxBase):
    """Dialog for applying an overall discount to the cart."""

    def __init__(self, current_rate, parent=None):
        super().__init__(parent)
        self._discount_rate = current_rate
        self._init_ui()

    def _init_ui(self):
        title = SubtitleLabel('整单折扣')
        self.viewLayout.addWidget(title)

        self.viewLayout.addSpacing(10)

        hint = BodyLabel('请输入折扣率（例如：85 表示 85折，即 85%）')
        self.viewLayout.addWidget(hint)

        self.viewLayout.addSpacing(5)

        self.discountEdit = LineEdit()
        self.discountEdit.setPlaceholderText('输入折扣率 (1-100)')
        current_pct = int(self._discount_rate * 100)
        self.discountEdit.setText(str(current_pct))
        self.discountEdit.setFixedWidth(200)
        self.viewLayout.addWidget(self.discountEdit)

        self.viewLayout.addSpacing(10)

        self.yesButton.setText('确认')
        self.cancelButton.setText('取消')

        self.widget.setMinimumWidth(360)

    def get_discount_rate(self):
        return self._discount_rate

    def accept(self):
        try:
            value = float(self.discountEdit.text().strip())
            if 1 <= value <= 100:
                self._discount_rate = value / 100.0
                super().accept()
        except ValueError:
            pass
