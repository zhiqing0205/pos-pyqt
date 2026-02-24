# coding: utf-8
from PyQt5.QtWidgets import QHBoxLayout

from qfluentwidgets import (MessageBoxBase, LineEdit, BodyLabel,
                            SubtitleLabel, CaptionLabel, SpinBox, setFont)


class StockInDialog(MessageBoxBase):
    """Dialog for entering stock-in details for a scanned product."""

    def __init__(self, product, parent=None):
        super().__init__(parent)
        self._product = product
        self._result = None
        self._init_ui()

    def _init_ui(self):
        title = SubtitleLabel('商品入库')
        self.viewLayout.addWidget(title)

        self.viewLayout.addSpacing(5)

        # Product info
        name_label = BodyLabel(self._product['name'])
        setFont(name_label, 16)
        self.viewLayout.addWidget(name_label)

        info = CaptionLabel('条码: {}  |  当前库存: {}  |  售价: ¥{:.2f}'.format(
            self._product['barcode'],
            self._product['stock_quantity'],
            self._product['selling_price']))
        info.setStyleSheet('color: gray;')
        self.viewLayout.addWidget(info)

        self.viewLayout.addSpacing(15)

        # Quantity row
        qty_row = QHBoxLayout()
        qty_row.setSpacing(12)
        qty_label = BodyLabel('进货数量')
        qty_label.setFixedWidth(70)
        qty_row.addWidget(qty_label)

        self.quantitySpin = SpinBox()
        self.quantitySpin.setRange(1, 99999)
        self.quantitySpin.setValue(1)
        self.quantitySpin.setFixedWidth(150)
        qty_row.addWidget(self.quantitySpin)
        qty_row.addStretch()
        self.viewLayout.addLayout(qty_row)

        self.viewLayout.addSpacing(5)

        # Price row (optional)
        price_row = QHBoxLayout()
        price_row.setSpacing(12)
        price_label = BodyLabel('进货单价')
        price_label.setFixedWidth(70)
        price_row.addWidget(price_label)

        self.priceEdit = LineEdit()
        self.priceEdit.setPlaceholderText('可选，默认使用上次进价')
        if self._product['purchase_price'] > 0:
            self.priceEdit.setText('{:.2f}'.format(self._product['purchase_price']))
        self.priceEdit.setFixedWidth(150)
        price_row.addWidget(self.priceEdit)
        price_row.addStretch()
        self.viewLayout.addLayout(price_row)

        self.viewLayout.addSpacing(5)

        # Note row (optional)
        note_row = QHBoxLayout()
        note_row.setSpacing(12)
        note_label = BodyLabel('备注')
        note_label.setFixedWidth(70)
        note_row.addWidget(note_label)

        self.noteEdit = LineEdit()
        self.noteEdit.setPlaceholderText('可选')
        note_row.addWidget(self.noteEdit, 1)
        self.viewLayout.addLayout(note_row)

        self.viewLayout.addSpacing(10)

        self.yesButton.setText('确认入库')
        self.cancelButton.setText('取消')

        self.widget.setMinimumWidth(420)

    def get_quantity(self):
        return self.quantitySpin.value()

    def get_price(self):
        text = self.priceEdit.text().strip()
        if not text:
            return self._product['purchase_price']
        try:
            return float(text)
        except ValueError:
            return self._product['purchase_price']

    def get_note(self):
        return self.noteEdit.text().strip()

    def accept(self):
        if self.quantitySpin.value() <= 0:
            return
        price_text = self.priceEdit.text().strip()
        if price_text:
            try:
                p = float(price_text)
                if p < 0:
                    return
            except ValueError:
                return
        super().accept()
