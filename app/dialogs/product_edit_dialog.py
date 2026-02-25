# coding: utf-8
from PyQt5.QtWidgets import QVBoxLayout

from qfluentwidgets import (MessageBoxBase, LineEdit, ComboBox, BodyLabel,
                            SubtitleLabel)

from ..models.category import CategoryModel


class ProductEditDialog(MessageBoxBase):
    """Dialog for adding or editing a product."""

    def __init__(self, product=None, barcode=None, parent=None):
        super().__init__(parent)
        self._product = product
        self._barcode = barcode
        self._result_data = None
        self._init_ui()

    def _init_ui(self):
        is_edit = self._product is not None
        title = SubtitleLabel('编辑商品' if is_edit else '添加商品')
        self.viewLayout.addWidget(title)
        self.viewLayout.addSpacing(10)

        # Barcode
        self.viewLayout.addWidget(BodyLabel('条码'))
        self.barcodeEdit = LineEdit()
        self.barcodeEdit.setPlaceholderText('商品条码')
        if is_edit:
            self.barcodeEdit.setText(self._product['barcode'])
        elif self._barcode:
            self.barcodeEdit.setText(self._barcode)
            self.barcodeEdit.setReadOnly(True)
        self.viewLayout.addWidget(self.barcodeEdit)

        self.viewLayout.addSpacing(5)

        # Name
        self.viewLayout.addWidget(BodyLabel('名称'))
        self.nameEdit = LineEdit()
        self.nameEdit.setPlaceholderText('商品名称')
        if is_edit:
            self.nameEdit.setText(self._product['name'])
        self.viewLayout.addWidget(self.nameEdit)

        self.viewLayout.addSpacing(5)

        # Category
        self.viewLayout.addWidget(BodyLabel('分类'))
        self.categoryCombo = ComboBox()
        cat_names = CategoryModel.get_names()
        self.categoryCombo.addItems(cat_names)
        if is_edit:
            current = self._product.get('category', '其他')
            idx = self.categoryCombo.findText(current)
            if idx >= 0:
                self.categoryCombo.setCurrentIndex(idx)
            else:
                self.categoryCombo.addItem(current)
                self.categoryCombo.setCurrentIndex(self.categoryCombo.count() - 1)
        else:
            idx = self.categoryCombo.findText('其他')
            if idx >= 0:
                self.categoryCombo.setCurrentIndex(idx)
        self.viewLayout.addWidget(self.categoryCombo)

        self.viewLayout.addSpacing(5)

        # Purchase price
        self.viewLayout.addWidget(BodyLabel('进价'))
        self.purchasePriceEdit = LineEdit()
        self.purchasePriceEdit.setPlaceholderText('0.00')
        if is_edit:
            self.purchasePriceEdit.setText(str(self._product['purchase_price']))
        self.viewLayout.addWidget(self.purchasePriceEdit)

        self.viewLayout.addSpacing(5)

        # Selling price
        self.viewLayout.addWidget(BodyLabel('售价'))
        self.sellingPriceEdit = LineEdit()
        self.sellingPriceEdit.setPlaceholderText('0.00')
        if is_edit:
            self.sellingPriceEdit.setText(str(self._product['selling_price']))
        self.viewLayout.addWidget(self.sellingPriceEdit)

        self.viewLayout.addSpacing(5)

        # Stock quantity
        self.viewLayout.addWidget(BodyLabel('库存数量'))
        self.stockEdit = LineEdit()
        self.stockEdit.setPlaceholderText('0')
        if is_edit:
            self.stockEdit.setText(str(self._product['stock_quantity']))
        self.viewLayout.addWidget(self.stockEdit)

        self.viewLayout.addSpacing(5)

        # Unit
        self.viewLayout.addWidget(BodyLabel('单位'))
        self.unitEdit = LineEdit()
        self.unitEdit.setPlaceholderText('个')
        if is_edit:
            self.unitEdit.setText(self._product.get('unit', '个'))
        else:
            self.unitEdit.setText('个')
        self.viewLayout.addWidget(self.unitEdit)

        self.yesButton.setText('保存')
        self.cancelButton.setText('取消')

        self.widget.setMinimumWidth(380)

    def get_data(self):
        return self._result_data

    def accept(self):
        barcode = self.barcodeEdit.text().strip()
        name = self.nameEdit.text().strip()
        if not barcode or not name:
            return

        try:
            purchase_price = float(self.purchasePriceEdit.text() or '0')
            selling_price = float(self.sellingPriceEdit.text() or '0')
            stock = int(self.stockEdit.text() or '0')
        except ValueError:
            return

        self._result_data = {
            'barcode': barcode,
            'name': name,
            'category': self.categoryCombo.currentText(),
            'purchase_price': purchase_price,
            'selling_price': selling_price,
            'stock_quantity': stock,
            'unit': self.unitEdit.text().strip() or '个',
        }
        super().accept()
