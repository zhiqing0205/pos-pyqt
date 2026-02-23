# coding: utf-8
from PyQt5.QtCore import Qt, QTimer, QEvent
from PyQt5.QtGui import QFont, QKeySequence, QColor
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QHeaderView,
                              QTableWidgetItem, QShortcut, QAbstractItemView,
                              QGridLayout, QSizePolicy, QScrollArea, QFrame,
                              QGraphicsDropShadowEffect, QApplication)

from qfluentwidgets import (PushButton, PrimaryPushButton, TransparentPushButton,
                            TableWidget, SimpleCardWidget, SubtitleLabel,
                            BodyLabel, TitleLabel, CaptionLabel,
                            InfoBar, InfoBarPosition,
                            setFont, FluentIcon as FIF, PillPushButton)

from ..models.product import ProductModel
from ..dialogs.checkout_dialog import CheckoutDialog
from ..dialogs.discount_dialog import DiscountDialog
from ..common.auth import AuthManager
from ..common.signal_bus import signal_bus


class ProductButton(PushButton):
    """A button representing a product in the quick-select grid."""

    def __init__(self, product, parent=None):
        super().__init__(parent)
        self.product = product
        self.setText('{}\n¥{:.2f}'.format(product['name'], product['selling_price']))
        self.setFixedSize(110, 60)
        self.setStyleSheet('''
            ProductButton {
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                background: white;
                font-size: 12px;
                text-align: center;
                padding: 4px;
            }
            ProductButton:hover {
                background: #e3f2fd;
                border-color: #90caf9;
            }
            ProductButton:pressed {
                background: #bbdefb;
            }
        ''')


class SalesInterface(QWidget):
    """Main cashier interface with cart on the left and product grid on the right."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cart_items = []
        self._discount_rate = 1.0
        self._barcode_buffer = ''
        self._barcode_timer = QTimer(self)
        self._barcode_timer.setSingleShot(True)
        self._barcode_timer.setInterval(100)
        self._barcode_timer.timeout.connect(self._flush_barcode_buffer)
        self._current_category = None
        self._init_ui()
        self._init_shortcuts()
        self._load_categories()

        signal_bus.product_changed.connect(self._load_categories)

        # Install event filter on the top-level window to capture barcode globally
        QTimer.singleShot(200, self._install_global_filter)

    def _install_global_filter(self):
        top = self.window()
        if top:
            top.installEventFilter(self)

    def eventFilter(self, obj, event):
        """Capture keyboard input globally for barcode scanning."""
        if event.type() == QEvent.KeyPress:
            # Only intercept when no dialog / line-edit has focus
            focused = QApplication.focusWidget()
            if focused and focused is not self and hasattr(focused, 'text') and callable(getattr(focused, 'setText', None)):
                # A text input has focus — don't intercept
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
        """Timer expired without Enter — clear partial buffer."""
        self._barcode_buffer = ''

    # ── UI Setup ──

    def _init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 8, 10, 8)
        main_layout.setSpacing(10)

        # ═══ LEFT: cart + summary ═══
        left = QVBoxLayout()
        left.setSpacing(8)

        # Status bar
        status_layout = QHBoxLayout()
        self.statusLabel = CaptionLabel('就绪 — 扫码或点击右侧商品添加到购物车')
        self.statusLabel.setStyleSheet('color: #757575;')
        status_layout.addWidget(self.statusLabel)
        status_layout.addStretch()
        left.addLayout(status_layout)

        # Cart table
        self.cartTable = TableWidget(self)
        self.cartTable.setBorderVisible(True)
        self.cartTable.setBorderRadius(8)
        self.cartTable.setWordWrap(False)
        self.cartTable.setColumnCount(7)
        self.cartTable.setHorizontalHeaderLabels(
            ['#', '商品名称', '单价', '数量', '折扣', '小计', '操作'])
        self.cartTable.verticalHeader().hide()
        self.cartTable.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.cartTable.setSelectionBehavior(QAbstractItemView.SelectRows)

        header = self.cartTable.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.Fixed)
        self.cartTable.setColumnWidth(0, 32)
        self.cartTable.setColumnWidth(3, 120)
        self.cartTable.setColumnWidth(6, 60)

        left.addWidget(self.cartTable, 1)

        # Summary card
        self.summaryCard = SimpleCardWidget(self)
        summary_layout = QHBoxLayout(self.summaryCard)
        summary_layout.setContentsMargins(16, 12, 16, 12)
        summary_layout.setSpacing(20)

        count_vbox = QVBoxLayout()
        count_vbox.setSpacing(2)
        self.countTitleLabel = CaptionLabel('数量')
        self.countValueLabel = SubtitleLabel('0')
        count_vbox.addWidget(self.countTitleLabel)
        count_vbox.addWidget(self.countValueLabel)
        summary_layout.addLayout(count_vbox)

        total_vbox = QVBoxLayout()
        total_vbox.setSpacing(2)
        self.totalTitleLabel = CaptionLabel('总额')
        self.totalValueLabel = SubtitleLabel('¥0.00')
        total_vbox.addWidget(self.totalTitleLabel)
        total_vbox.addWidget(self.totalValueLabel)
        summary_layout.addLayout(total_vbox)

        discount_vbox = QVBoxLayout()
        discount_vbox.setSpacing(2)
        self.discountTitleLabel = CaptionLabel('优惠')
        self.discountValueLabel = SubtitleLabel('¥0.00')
        discount_vbox.addWidget(self.discountTitleLabel)
        discount_vbox.addWidget(self.discountValueLabel)
        summary_layout.addLayout(discount_vbox)

        summary_layout.addStretch()

        final_vbox = QVBoxLayout()
        final_vbox.setSpacing(2)
        self.finalTitleLabel = CaptionLabel('应收')
        self.finalValueLabel = TitleLabel('¥0.00')
        setFont(self.finalValueLabel, 30)
        self.finalValueLabel.setStyleSheet('color: #d32f2f;')
        final_vbox.addWidget(self.finalTitleLabel, 0, Qt.AlignRight)
        final_vbox.addWidget(self.finalValueLabel, 0, Qt.AlignRight)
        summary_layout.addLayout(final_vbox)

        left.addWidget(self.summaryCard)

        # Action buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self.discountBtn = PushButton(FIF.LABEL, '折扣 F4')
        self.clearBtn = PushButton(FIF.DELETE, '清空')
        self.checkoutBtn = PrimaryPushButton(FIF.SHOPPING_CART, '结账 F12')
        self.checkoutBtn.setFixedHeight(42)
        setFont(self.checkoutBtn, 15)

        btn_layout.addWidget(self.discountBtn)
        btn_layout.addWidget(self.clearBtn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.checkoutBtn)

        left.addLayout(btn_layout)

        main_layout.addLayout(left, 5)

        # ═══ RIGHT: category tabs + product grid ═══
        right = QVBoxLayout()
        right.setSpacing(6)

        # Category tabs (horizontal scroll)
        self.categoryScroll = QScrollArea()
        self.categoryScroll.setWidgetResizable(True)
        self.categoryScroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.categoryScroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.categoryScroll.setFixedHeight(38)
        self.categoryScroll.setFrameShape(QFrame.NoFrame)
        self.categoryScroll.setStyleSheet('background: transparent;')

        self.categoryContainer = QWidget()
        self.categoryLayout = QHBoxLayout(self.categoryContainer)
        self.categoryLayout.setContentsMargins(0, 0, 0, 0)
        self.categoryLayout.setSpacing(6)
        self.categoryScroll.setWidget(self.categoryContainer)

        right.addWidget(self.categoryScroll)

        # Product grid (scrollable)
        self.productScroll = QScrollArea()
        self.productScroll.setWidgetResizable(True)
        self.productScroll.setFrameShape(QFrame.NoFrame)
        self.productScroll.setStyleSheet('background: transparent;')

        self.productGridWidget = QWidget()
        self.productGridWidget.setStyleSheet('background: transparent;')
        self.productGrid = QGridLayout(self.productGridWidget)
        self.productGrid.setSpacing(8)
        self.productGrid.setContentsMargins(0, 0, 0, 0)
        self.productScroll.setWidget(self.productGridWidget)

        right.addWidget(self.productScroll, 1)

        main_layout.addLayout(right, 3)

        # ═══ Connections ═══
        self.discountBtn.clicked.connect(self._on_discount)
        self.clearBtn.clicked.connect(self._on_clear_cart)
        self.checkoutBtn.clicked.connect(self._on_checkout)

    def _init_shortcuts(self):
        QShortcut(QKeySequence(Qt.Key_F12), self, self._on_checkout)
        QShortcut(QKeySequence(Qt.Key_F4), self, self._on_discount)
        QShortcut(QKeySequence(Qt.Key_Delete), self, self._on_delete_selected)

    # ── Category & Product Grid ──

    def _load_categories(self):
        categories = ProductModel.get_categories()
        # Clear old buttons
        while self.categoryLayout.count():
            item = self.categoryLayout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        all_btn = PillPushButton('全部')
        all_btn.setFixedHeight(30)
        all_btn.setChecked(True)
        all_btn.clicked.connect(lambda: self._select_category(None))
        self.categoryLayout.addWidget(all_btn)

        for cat in categories:
            btn = PillPushButton(cat)
            btn.setFixedHeight(30)
            btn.clicked.connect(lambda checked, c=cat: self._select_category(c))
            self.categoryLayout.addWidget(btn)

        self.categoryLayout.addStretch()
        self._select_category(None)

    def _select_category(self, category):
        self._current_category = category

        # Update tab highlight
        for i in range(self.categoryLayout.count()):
            item = self.categoryLayout.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), PillPushButton):
                btn = item.widget()
                is_selected = (category is None and btn.text() == '全部') or (btn.text() == category)
                btn.setChecked(is_selected)

        # Load products
        if category is None:
            products = ProductModel.get_all()
        else:
            products = ProductModel.get_by_category(category)
        self._display_product_grid(products)

    def _display_product_grid(self, products):
        # Clear grid
        while self.productGrid.count():
            item = self.productGrid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        cols = 3
        for i, p in enumerate(products):
            btn = ProductButton(p)
            btn.clicked.connect(lambda checked, product=p: self._add_product_to_cart(product))
            self.productGrid.addWidget(btn, i // cols, i % cols)

        # Fill remaining space
        row_count = (len(products) + cols - 1) // cols
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.productGrid.addWidget(spacer, row_count, 0, 1, cols)

    # ── Cart Operations ──

    def _process_barcode(self, barcode):
        """Handle a scanned/entered barcode."""
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
            self.statusLabel.setText('未找到: {}'.format(barcode))
            self.statusLabel.setStyleSheet('color: #d32f2f;')
            return

        self._add_product_to_cart(product)

    def _add_product_to_cart(self, product):
        """Add a product to the cart (or increment if already present)."""
        for item in self._cart_items:
            if item['product_id'] == product['id']:
                item['quantity'] += 1
                item['subtotal'] = round(
                    item['unit_price'] * item['quantity'] * item['discount_rate'], 2)
                self._refresh_cart_table()
                self.statusLabel.setText('{} x{}'.format(product['name'], item['quantity']))
                self.statusLabel.setStyleSheet('color: #2e7d32;')
                return

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
        self.statusLabel.setText('+ {}'.format(product['name']))
        self.statusLabel.setStyleSheet('color: #2e7d32;')

    def _refresh_cart_table(self):
        self.cartTable.setRowCount(len(self._cart_items))
        for i, item in enumerate(self._cart_items):
            self.cartTable.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.cartTable.setItem(i, 1, QTableWidgetItem(item['name']))
            self.cartTable.setItem(i, 2, QTableWidgetItem('{:.2f}'.format(item['unit_price'])))

            # Quantity with +/- buttons
            qty_widget = QWidget()
            qty_layout = QHBoxLayout(qty_widget)
            qty_layout.setContentsMargins(2, 2, 2, 2)
            qty_layout.setSpacing(3)

            minus_btn = PushButton('-')
            minus_btn.setFixedSize(26, 26)
            qty_label = BodyLabel(str(item['quantity']))
            qty_label.setAlignment(Qt.AlignCenter)
            qty_label.setFixedWidth(30)
            plus_btn = PushButton('+')
            plus_btn.setFixedSize(26, 26)

            row = i
            minus_btn.clicked.connect(lambda checked, r=row: self._change_quantity(r, -1))
            plus_btn.clicked.connect(lambda checked, r=row: self._change_quantity(r, 1))

            qty_layout.addWidget(minus_btn)
            qty_layout.addWidget(qty_label)
            qty_layout.addWidget(plus_btn)
            self.cartTable.setCellWidget(i, 3, qty_widget)

            discount_text = '{:.0f}%'.format(item['discount_rate'] * 100)
            self.cartTable.setItem(i, 4, QTableWidgetItem(discount_text))
            self.cartTable.setItem(i, 5, QTableWidgetItem('{:.2f}'.format(item['subtotal'])))

            del_btn = PushButton(FIF.DELETE, '')
            del_btn.setFixedSize(32, 28)
            del_btn.clicked.connect(lambda checked, r=row: self._remove_item(r))
            del_widget = QWidget()
            del_layout = QHBoxLayout(del_widget)
            del_layout.setContentsMargins(2, 2, 2, 2)
            del_layout.addWidget(del_btn)
            self.cartTable.setCellWidget(i, 6, del_widget)

        # Scroll to bottom to show latest item
        if self._cart_items:
            self.cartTable.scrollToBottom()

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
            self.statusLabel.setText('就绪')
            self.statusLabel.setStyleSheet('color: #757575;')

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

        final_amount = round(discounted_total * self._discount_rate, 2)
        discount_amount = round(total_amount - final_amount, 2)

        self.countValueLabel.setText(str(total_qty))
        self.totalValueLabel.setText('¥{:.2f}'.format(total_amount))
        self.discountValueLabel.setText('¥{:.2f}'.format(discount_amount))
        self.finalValueLabel.setText('¥{:.2f}'.format(final_amount))

    # ── Actions ──

    def _on_discount(self):
        if not self._cart_items:
            InfoBar.warning(
                title='提示', content='购物车为空',
                parent=self, position=InfoBarPosition.TOP, duration=2000)
            return
        dialog = DiscountDialog(self._discount_rate, self.window())
        if dialog.exec_():
            self._discount_rate = dialog.get_discount_rate()
            self._update_summary()

    def _on_clear_cart(self):
        self._cart_items.clear()
        self._discount_rate = 1.0
        self._refresh_cart_table()
        self.statusLabel.setText('购物车已清空')
        self.statusLabel.setStyleSheet('color: #757575;')

    def _on_checkout(self):
        if not self._cart_items:
            InfoBar.warning(
                title='提示', content='购物车为空，无法结账',
                parent=self, position=InfoBarPosition.TOP, duration=2000)
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
            self._cart_items.clear()
            self._discount_rate = 1.0
            self._refresh_cart_table()
            InfoBar.success(
                title='交易完成', content='结账成功！',
                parent=self, position=InfoBarPosition.TOP, duration=3000)
            self.statusLabel.setText('交易完成')
            self.statusLabel.setStyleSheet('color: #2e7d32;')
            signal_bus.transaction_completed.emit()
            signal_bus.stock_changed.emit()
