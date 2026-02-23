# coding: utf-8
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QKeySequence
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QHeaderView,
                              QTableWidgetItem, QShortcut, QAbstractItemView)

from qfluentwidgets import (SearchLineEdit, PushButton, PrimaryPushButton,
                            TableWidget, SimpleCardWidget, SubtitleLabel,
                            BodyLabel, TitleLabel, InfoBar, InfoBarPosition,
                            setFont, FluentIcon as FIF)

from ..models.product import ProductModel
from ..dialogs.checkout_dialog import CheckoutDialog
from ..dialogs.discount_dialog import DiscountDialog
from ..common.auth import AuthManager
from ..common.signal_bus import signal_bus


class SalesInterface(QWidget):
    """Main cashier interface with barcode scanning and cart management."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cart_items = []
        self._discount_rate = 1.0  # overall discount rate
        self._init_ui()
        self._init_shortcuts()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(10)

        # === Barcode input area ===
        barcode_layout = QHBoxLayout()
        barcode_layout.setSpacing(10)

        self.barcodeEdit = SearchLineEdit()
        self.barcodeEdit.setPlaceholderText('扫描条码或输入条码后回车...')
        self.barcodeEdit.setFixedHeight(40)
        setFont(self.barcodeEdit, 16)
        barcode_layout.addWidget(self.barcodeEdit, 1)

        layout.addLayout(barcode_layout)

        # === Cart table ===
        self.cartTable = TableWidget(self)
        self.cartTable.setBorderVisible(True)
        self.cartTable.setBorderRadius(8)
        self.cartTable.setWordWrap(False)
        self.cartTable.setColumnCount(8)
        self.cartTable.setHorizontalHeaderLabels(
            ['#', '商品名称', '条码', '单价', '数量', '折扣', '小计', '操作'])
        self.cartTable.verticalHeader().hide()
        self.cartTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.cartTable.setSelectionBehavior(QAbstractItemView.SelectRows)

        header = self.cartTable.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.Fixed)
        self.cartTable.setColumnWidth(0, 40)
        self.cartTable.setColumnWidth(4, 130)
        self.cartTable.setColumnWidth(7, 70)

        layout.addWidget(self.cartTable, 1)

        # === Summary card ===
        self.summaryCard = SimpleCardWidget(self)
        summary_layout = QHBoxLayout(self.summaryCard)
        summary_layout.setContentsMargins(20, 15, 20, 15)
        summary_layout.setSpacing(30)

        # Item count
        count_vbox = QVBoxLayout()
        count_vbox.setSpacing(4)
        self.countTitleLabel = BodyLabel('商品数量')
        self.countValueLabel = SubtitleLabel('0')
        count_vbox.addWidget(self.countTitleLabel)
        count_vbox.addWidget(self.countValueLabel)
        summary_layout.addLayout(count_vbox)

        # Total
        total_vbox = QVBoxLayout()
        total_vbox.setSpacing(4)
        self.totalTitleLabel = BodyLabel('商品总额')
        self.totalValueLabel = SubtitleLabel('¥0.00')
        total_vbox.addWidget(self.totalTitleLabel)
        total_vbox.addWidget(self.totalValueLabel)
        summary_layout.addLayout(total_vbox)

        # Discount
        discount_vbox = QVBoxLayout()
        discount_vbox.setSpacing(4)
        self.discountTitleLabel = BodyLabel('折扣优惠')
        self.discountValueLabel = SubtitleLabel('¥0.00')
        discount_vbox.addWidget(self.discountTitleLabel)
        discount_vbox.addWidget(self.discountValueLabel)
        summary_layout.addLayout(discount_vbox)

        summary_layout.addStretch()

        # Final amount (large)
        final_vbox = QVBoxLayout()
        final_vbox.setSpacing(4)
        self.finalTitleLabel = BodyLabel('应收金额')
        self.finalValueLabel = TitleLabel('¥0.00')
        setFont(self.finalValueLabel, 32)
        self.finalValueLabel.setStyleSheet('color: #d32f2f;')
        final_vbox.addWidget(self.finalTitleLabel, 0, Qt.AlignRight)
        final_vbox.addWidget(self.finalValueLabel, 0, Qt.AlignRight)
        summary_layout.addLayout(final_vbox)

        layout.addWidget(self.summaryCard)

        # === Action buttons ===
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.discountBtn = PushButton(FIF.LABEL, '整单折扣 (F4)')
        self.clearBtn = PushButton(FIF.DELETE, '清空购物车')
        self.checkoutBtn = PrimaryPushButton(FIF.SHOPPING_CART, '结账 (F12)')
        self.checkoutBtn.setFixedHeight(45)
        setFont(self.checkoutBtn, 16)

        btn_layout.addWidget(self.discountBtn)
        btn_layout.addWidget(self.clearBtn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.checkoutBtn)

        layout.addLayout(btn_layout)

        # === Connections ===
        self.barcodeEdit.returnPressed.connect(self._on_barcode_enter)
        self.discountBtn.clicked.connect(self._on_discount)
        self.clearBtn.clicked.connect(self._on_clear_cart)
        self.checkoutBtn.clicked.connect(self._on_checkout)

    def _init_shortcuts(self):
        QShortcut(QKeySequence(Qt.Key_F12), self, self._on_checkout)
        QShortcut(QKeySequence(Qt.Key_F2), self, self._focus_barcode)
        QShortcut(QKeySequence(Qt.Key_F4), self, self._on_discount)
        QShortcut(QKeySequence(Qt.Key_Delete), self, self._on_delete_selected)

    def _focus_barcode(self):
        self.barcodeEdit.clear()
        self.barcodeEdit.setFocus()

    def _on_barcode_enter(self):
        barcode = self.barcodeEdit.text().strip()
        if not barcode:
            return

        product = ProductModel.get_by_barcode(barcode)
        if not product:
            InfoBar.error(
                title='商品未找到',
                content='条码 {} 未找到对应商品'.format(barcode),
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )
            self.barcodeEdit.clear()
            self.barcodeEdit.setFocus()
            return

        # Check if already in cart
        for item in self._cart_items:
            if item['product_id'] == product['id']:
                item['quantity'] += 1
                item['subtotal'] = round(
                    item['unit_price'] * item['quantity'] * item['discount_rate'], 2)
                self._refresh_cart_table()
                self.barcodeEdit.clear()
                self.barcodeEdit.setFocus()
                return

        # Add new item
        self._cart_items.append({
            'product_id': product['id'],
            'barcode': product['barcode'],
            'name': product['name'],
            'unit_price': product['selling_price'],
            'quantity': 1,
            'discount_rate': 1.0,
            'subtotal': product['selling_price'],
        })
        self._refresh_cart_table()
        self.barcodeEdit.clear()
        self.barcodeEdit.setFocus()

    def _refresh_cart_table(self):
        self.cartTable.setRowCount(len(self._cart_items))
        for i, item in enumerate(self._cart_items):
            # #
            self.cartTable.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            # Name
            self.cartTable.setItem(i, 1, QTableWidgetItem(item['name']))
            # Barcode
            self.cartTable.setItem(i, 2, QTableWidgetItem(item['barcode']))
            # Unit price
            self.cartTable.setItem(i, 3, QTableWidgetItem(
                '{:.2f}'.format(item['unit_price'])))

            # Quantity with +/- buttons
            qty_widget = QWidget()
            qty_layout = QHBoxLayout(qty_widget)
            qty_layout.setContentsMargins(2, 2, 2, 2)
            qty_layout.setSpacing(4)

            minus_btn = PushButton('-')
            minus_btn.setFixedSize(28, 28)
            qty_label = BodyLabel(str(item['quantity']))
            qty_label.setAlignment(Qt.AlignCenter)
            qty_label.setFixedWidth(35)
            plus_btn = PushButton('+')
            plus_btn.setFixedSize(28, 28)

            row = i
            minus_btn.clicked.connect(lambda checked, r=row: self._change_quantity(r, -1))
            plus_btn.clicked.connect(lambda checked, r=row: self._change_quantity(r, 1))

            qty_layout.addWidget(minus_btn)
            qty_layout.addWidget(qty_label)
            qty_layout.addWidget(plus_btn)
            self.cartTable.setCellWidget(i, 4, qty_widget)

            # Discount
            discount_text = '{:.0f}%'.format(item['discount_rate'] * 100)
            self.cartTable.setItem(i, 5, QTableWidgetItem(discount_text))

            # Subtotal
            self.cartTable.setItem(i, 6, QTableWidgetItem(
                '{:.2f}'.format(item['subtotal'])))

            # Delete button
            del_btn = PushButton(FIF.DELETE, '')
            del_btn.setFixedSize(36, 30)
            del_btn.clicked.connect(lambda checked, r=row: self._remove_item(r))
            del_widget = QWidget()
            del_layout = QHBoxLayout(del_widget)
            del_layout.setContentsMargins(4, 2, 4, 2)
            del_layout.addWidget(del_btn)
            self.cartTable.setCellWidget(i, 7, del_widget)

        self._update_summary()

    def _change_quantity(self, row, delta):
        if 0 <= row < len(self._cart_items):
            item = self._cart_items[row]
            new_qty = item['quantity'] + delta
            if new_qty <= 0:
                self._remove_item(row)
                return
            item['quantity'] = new_qty
            item['subtotal'] = round(
                item['unit_price'] * item['quantity'] * item['discount_rate'], 2)
            self._refresh_cart_table()

    def _remove_item(self, row):
        if 0 <= row < len(self._cart_items):
            self._cart_items.pop(row)
            self._refresh_cart_table()

    def _on_delete_selected(self):
        rows = set()
        for item in self.cartTable.selectedItems():
            rows.add(item.row())
        for row in sorted(rows, reverse=True):
            if 0 <= row < len(self._cart_items):
                self._cart_items.pop(row)
        self._refresh_cart_table()

    def _update_summary(self):
        total_qty = sum(item['quantity'] for item in self._cart_items)
        total_amount = sum(
            item['unit_price'] * item['quantity'] for item in self._cart_items)
        discounted_total = sum(item['subtotal'] for item in self._cart_items)

        # Apply overall discount
        final_amount = round(discounted_total * self._discount_rate, 2)
        discount_amount = round(total_amount - final_amount, 2)

        self.countValueLabel.setText(str(total_qty))
        self.totalValueLabel.setText('¥{:.2f}'.format(total_amount))
        self.discountValueLabel.setText('¥{:.2f}'.format(discount_amount))
        self.finalValueLabel.setText('¥{:.2f}'.format(final_amount))

    def _on_discount(self):
        if not self._cart_items:
            InfoBar.warning(
                title='提示',
                content='购物车为空',
                parent=self,
                position=InfoBarPosition.TOP,
                duration=2000
            )
            return
        dialog = DiscountDialog(self._discount_rate, self.window())
        if dialog.exec_():
            self._discount_rate = dialog.get_discount_rate()
            self._update_summary()
        QTimer.singleShot(100, self._focus_barcode)

    def _on_clear_cart(self):
        self._cart_items.clear()
        self._discount_rate = 1.0
        self._refresh_cart_table()
        self._focus_barcode()

    def _on_checkout(self):
        if not self._cart_items:
            InfoBar.warning(
                title='提示',
                content='购物车为空，无法结账',
                parent=self,
                position=InfoBarPosition.TOP,
                duration=2000
            )
            return

        total_amount = sum(
            item['unit_price'] * item['quantity'] for item in self._cart_items)
        discounted_total = sum(item['subtotal'] for item in self._cart_items)
        final_amount = round(discounted_total * self._discount_rate, 2)
        discount_amount = round(total_amount - final_amount, 2)

        dialog = CheckoutDialog(
            final_amount=final_amount,
            total_amount=total_amount,
            discount_amount=discount_amount,
            cart_items=self._cart_items,
            parent=self.window()
        )
        if dialog.exec_():
            # Checkout succeeded, clear cart
            self._cart_items.clear()
            self._discount_rate = 1.0
            self._refresh_cart_table()
            InfoBar.success(
                title='交易完成',
                content='结账成功！',
                parent=self,
                position=InfoBarPosition.TOP,
                duration=3000
            )
            signal_bus.transaction_completed.emit()
            signal_bus.stock_changed.emit()
        QTimer.singleShot(100, self._focus_barcode)

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(200, self._focus_barcode)
