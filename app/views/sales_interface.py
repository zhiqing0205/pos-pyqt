# coding: utf-8
from PyQt5.QtCore import Qt, QTimer, QEvent
from PyQt5.QtGui import QFont, QKeySequence, QColor, QFontMetrics
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QHeaderView,
                              QTableWidgetItem, QShortcut, QAbstractItemView,
                              QGridLayout, QSizePolicy, QScrollArea, QFrame,
                              QGraphicsDropShadowEffect, QApplication, QLabel)

from qfluentwidgets import (PushButton, PrimaryPushButton, TransparentPushButton,
                            TableWidget, SimpleCardWidget, SubtitleLabel,
                            BodyLabel, TitleLabel, CaptionLabel,
                            InfoBar, InfoBarPosition,
                            setFont, FluentIcon as FIF, PillPushButton,
                            ToolButton, SmoothScrollArea)

from ..models.product import ProductModel
from ..dialogs.checkout_dialog import CheckoutDialog
from ..dialogs.discount_dialog import DiscountDialog
from ..dialogs.cart_item_dialog import CartItemDialog
from ..common.auth import AuthManager
from ..common.signal_bus import signal_bus

# Preferred category display order (listed ones come first, rest alphabetical)
_CATEGORY_ORDER = ['饮料', '水', '奶品', '酒', '方便面', '零食', '日用品']


class ProductButton(PushButton):
    """A button representing a product in the quick-select grid."""

    def __init__(self, product, parent=None):
        super().__init__(parent)
        self.product = product
        self.setFixedSize(130, 58)
        self.setToolTip('{}\n¥{:.2f}'.format(product['name'], product['selling_price']))

        # Elide the name if too long
        fm = QFontMetrics(QFont(self.font().family(), 13))
        max_w = 112  # button width minus padding
        elided = fm.elidedText(product['name'], Qt.ElideRight, max_w)
        self.setText('{}\n¥{:.2f}'.format(elided, product['selling_price']))

        self.setStyleSheet('''
            ProductButton {
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                background: white;
                font-size: 13px;
                text-align: center;
                padding: 2px 8px;
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

        QTimer.singleShot(200, self._install_global_filter)

    def _install_global_filter(self):
        top = self.window()
        if top:
            top.installEventFilter(self)

    def eventFilter(self, obj, event):
        """Capture keyboard input globally for barcode scanning."""
        if event.type() == QEvent.KeyPress:
            focused = QApplication.focusWidget()
            if focused and focused is not self and hasattr(focused, 'text') and callable(getattr(focused, 'setText', None)):
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
        self.cartTable.setStyleSheet(
            'QTableView::item { padding-left: 8px; padding-right: 8px; }')

        header = self.cartTable.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.Fixed)
        self.cartTable.setColumnWidth(0, 45)
        self.cartTable.setColumnWidth(3, 120)
        self.cartTable.setColumnWidth(6, 60)

        left.addWidget(self.cartTable, 1)

        # ── Summary card (larger) ──
        self.summaryCard = SimpleCardWidget(self)
        self.summaryCard.setFixedHeight(100)
        summary_layout = QHBoxLayout(self.summaryCard)
        summary_layout.setContentsMargins(24, 14, 24, 14)
        summary_layout.setSpacing(0)

        # Helper to create each summary column
        def make_summary_col(title_text, default_value, font_size=20):
            vbox = QVBoxLayout()
            vbox.setSpacing(4)
            title = CaptionLabel(title_text)
            setFont(title, 13)
            value = SubtitleLabel(default_value)
            setFont(value, font_size)
            vbox.addWidget(title, 0, Qt.AlignCenter)
            vbox.addWidget(value, 0, Qt.AlignCenter)
            return vbox, value

        col1, self.countValueLabel = make_summary_col('商品数量', '0')
        summary_layout.addLayout(col1, 1)

        col2, self.totalValueLabel = make_summary_col('商品总额', '¥0.00')
        summary_layout.addLayout(col2, 1)

        col3, self.discountValueLabel = make_summary_col('折扣优惠', '¥0.00')
        summary_layout.addLayout(col3, 1)

        # Final amount — bigger and red
        final_vbox = QVBoxLayout()
        final_vbox.setSpacing(4)
        final_title = CaptionLabel('应收金额')
        setFont(final_title, 13)
        self.finalValueLabel = TitleLabel('¥0.00')
        setFont(self.finalValueLabel, 32)
        self.finalValueLabel.setStyleSheet('color: #d32f2f;')
        final_vbox.addWidget(final_title, 0, Qt.AlignCenter)
        final_vbox.addWidget(self.finalValueLabel, 0, Qt.AlignCenter)
        summary_layout.addLayout(final_vbox, 2)

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

        # Category tabs
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

        # Product grid
        self.productScroll = SmoothScrollArea()
        self.productScroll.setWidgetResizable(True)
        self.productScroll.setFrameShape(QFrame.NoFrame)
        self.productScroll.setStyleSheet('QScrollArea { background: transparent; }')

        self.productGridWidget = QWidget()
        self.productGridWidget.setStyleSheet('background: transparent;')
        self.productGrid = QGridLayout(self.productGridWidget)
        self.productGrid.setSpacing(5)
        self.productGrid.setContentsMargins(0, 0, 0, 0)
        self.productScroll.setWidget(self.productGridWidget)

        right.addWidget(self.productScroll, 1)

        main_layout.addLayout(right, 3)

        # ═══ Connections ═══
        self.discountBtn.clicked.connect(self._on_discount)
        self.clearBtn.clicked.connect(self._on_clear_cart)
        self.checkoutBtn.clicked.connect(self._on_checkout)
        self.cartTable.doubleClicked.connect(self._on_cart_double_click)

    def _init_shortcuts(self):
        QShortcut(QKeySequence(Qt.Key_F12), self, self._on_checkout)
        QShortcut(QKeySequence(Qt.Key_F4), self, self._on_discount)
        QShortcut(QKeySequence(Qt.Key_Delete), self, self._on_delete_selected)

    # ── Category & Product Grid ──

    def _sorted_categories(self, categories):
        """Sort categories: preferred order first, then alphabetical for the rest."""
        ordered = []
        remaining = []
        for cat in _CATEGORY_ORDER:
            if cat in categories:
                ordered.append(cat)
        for cat in categories:
            if cat not in ordered:
                remaining.append(cat)
        remaining.sort()
        return ordered + remaining

    def _load_categories(self):
        raw = ProductModel.get_categories()
        categories = self._sorted_categories(raw)

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

        for i in range(self.categoryLayout.count()):
            item = self.categoryLayout.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), PillPushButton):
                btn = item.widget()
                is_selected = (category is None and btn.text() == '全部') or (btn.text() == category)
                btn.setChecked(is_selected)

        if category is None:
            products = ProductModel.get_all()
        else:
            products = ProductModel.get_by_category(category)
        self._display_product_grid(products)

    def _display_product_grid(self, products):
        while self.productGrid.count():
            item = self.productGrid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        cols = 3
        for i, p in enumerate(products):
            btn = ProductButton(p)
            btn.clicked.connect(lambda checked, product=p: self._add_product_to_cart(product))
            self.productGrid.addWidget(btn, i // cols, i % cols)

        row_count = (len(products) + cols - 1) // cols
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.productGrid.addWidget(spacer, row_count, 0, 1, cols)

    # ── Cart Operations ──

    def _process_barcode(self, barcode):
        if not barcode:
            return
        product = ProductModel.get_by_barcode(barcode)
        if not product:
            InfoBar.error(
                title='商品未找到',
                content='条码 {} 未找到对应商品'.format(barcode),
                parent=self, position=InfoBarPosition.TOP, duration=3000)
            self.statusLabel.setText('未找到: {}'.format(barcode))
            self.statusLabel.setStyleSheet('color: #d32f2f;')
            return
        self._add_product_to_cart(product)

    def _add_product_to_cart(self, product):
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
            num_item = QTableWidgetItem(str(i + 1))
            num_item.setTextAlignment(Qt.AlignCenter)
            self.cartTable.setItem(i, 0, num_item)
            self.cartTable.setItem(i, 1, QTableWidgetItem(item['name']))
            self.cartTable.setItem(i, 2, QTableWidgetItem('{:.2f}'.format(item['unit_price'])))

            # Quantity with styled +/- buttons
            qty_widget = QWidget()
            qty_layout = QHBoxLayout(qty_widget)
            qty_layout.setContentsMargins(2, 2, 2, 2)
            qty_layout.setSpacing(3)

            minus_btn = ToolButton(FIF.REMOVE, self)
            minus_btn.setFixedSize(26, 26)
            qty_label = BodyLabel(str(item['quantity']))
            qty_label.setAlignment(Qt.AlignCenter)
            qty_label.setFixedWidth(30)
            setFont(qty_label, 14)
            plus_btn = ToolButton(FIF.ADD, self)
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

            # Red delete button
            del_btn = ToolButton(FIF.DELETE, self)
            del_btn.setFixedSize(32, 28)
            del_btn.setStyleSheet('''
                ToolButton {
                    background: transparent;
                    border: none;
                    border-radius: 4px;
                    qproperty-iconSize: 16px 16px;
                }
                ToolButton:hover {
                    background: #ffebee;
                }
                ToolButton:pressed {
                    background: #ffcdd2;
                }
            ''')
            del_btn.setIcon(FIF.DELETE.icon(color=QColor('#d32f2f')))
            del_btn.clicked.connect(lambda checked, r=row: self._remove_item(r))
            del_widget = QWidget()
            del_layout = QHBoxLayout(del_widget)
            del_layout.setContentsMargins(2, 2, 2, 2)
            del_layout.addWidget(del_btn)
            self.cartTable.setCellWidget(i, 6, del_widget)

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

    def _on_cart_double_click(self, index):
        row = index.row()
        if row < 0 or row >= len(self._cart_items):
            return
        item = self._cart_items[row]
        dialog = CartItemDialog(item, self.window())
        if dialog.exec_():
            action = dialog.get_action()
            if action == CartItemDialog.RESULT_DELETE:
                self._remove_item(row)
            elif action == CartItemDialog.RESULT_DISCOUNT:
                item['discount_rate'] = dialog.get_discount_rate()
                item['subtotal'] = round(
                    item['unit_price'] * item['quantity'] * item['discount_rate'], 2)
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
