# coding: utf-8
from PyQt5.QtCore import Qt, QTimer, QEvent
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QHeaderView,
                              QTableWidgetItem, QAbstractItemView, QApplication)

from qfluentwidgets import (SearchLineEdit, PushButton, PrimaryPushButton,
                            TableWidget, InfoBar, InfoBarPosition,
                            FluentIcon as FIF, MessageBox)

from ..models.product import ProductModel
from ..dialogs.product_edit_dialog import ProductEditDialog
from ..common.signal_bus import signal_bus


class ProductInterface(QWidget):
    """Product management interface for admin users."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._barcode_buffer = ''
        self._barcode_timer = QTimer(self)
        self._barcode_timer.setSingleShot(True)
        self._barcode_timer.setInterval(100)
        self._barcode_timer.timeout.connect(self._flush_barcode_buffer)
        self._init_ui()
        self._load_products()

        signal_bus.product_changed.connect(self._load_products)
        signal_bus.stock_changed.connect(self._load_products)

        QTimer.singleShot(200, self._install_global_filter)

    def _install_global_filter(self):
        top = self.window()
        if top:
            top.installEventFilter(self)

    def eventFilter(self, obj, event):
        """Capture barcode scans when this interface is visible."""
        if not self.isVisible():
            return False

        if event.type() == QEvent.KeyPress:
            focused = QApplication.focusWidget()
            if (focused and focused is not self
                    and hasattr(focused, 'text')
                    and callable(getattr(focused, 'setText', None))):
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

    def _process_barcode(self, barcode):
        """Handle scanned barcode: edit existing product or create new."""
        if not barcode:
            return
        product = ProductModel.get_by_barcode(barcode)
        if product:
            self._on_edit(product['id'])
        else:
            dialog = ProductEditDialog(barcode=barcode, parent=self.window())
            if dialog.exec_():
                data = dialog.get_data()
                result = ProductModel.create(**data)
                if result:
                    InfoBar.success(
                        title='成功', content='商品已添加',
                        parent=self, position=InfoBarPosition.TOP, duration=2000)
                    self._load_products()
                    signal_bus.product_changed.emit()
                else:
                    InfoBar.error(
                        title='失败', content='添加失败，条码可能重复',
                        parent=self, position=InfoBarPosition.TOP, duration=3000)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(10)

        # Top bar
        top_layout = QHBoxLayout()
        top_layout.setSpacing(10)

        self.searchEdit = SearchLineEdit()
        self.searchEdit.setPlaceholderText('搜索商品（条码、名称、分类）或扫码快速添加/编辑...')
        self.searchEdit.setFixedHeight(36)
        top_layout.addWidget(self.searchEdit, 1)

        self.addBtn = PrimaryPushButton(FIF.ADD, '添加商品')
        top_layout.addWidget(self.addBtn)

        layout.addLayout(top_layout)

        # Table
        self.table = TableWidget(self)
        self.table.setBorderVisible(True)
        self.table.setBorderRadius(8)
        self.table.setWordWrap(False)
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            ['条码', '名称', '分类', '进价', '售价', '库存', '单位', '操作'])
        self.table.verticalHeader().hide()
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.Fixed)
        self.table.setColumnWidth(7, 140)

        layout.addWidget(self.table, 1)

        # Connections
        self.searchEdit.returnPressed.connect(self._on_search)
        self.searchEdit.textChanged.connect(self._on_search_changed)
        self.addBtn.clicked.connect(self._on_add)

    def _on_search_changed(self, text):
        if not text:
            self._load_products()

    def _on_search(self):
        keyword = self.searchEdit.text().strip()
        if keyword:
            products = ProductModel.search(keyword)
        else:
            products = ProductModel.get_all()
        self._display_products(products)

    def _load_products(self):
        products = ProductModel.get_all()
        self._display_products(products)

    def _display_products(self, products):
        self.table.setRowCount(len(products))
        for i, p in enumerate(products):
            self.table.setItem(i, 0, QTableWidgetItem(p['barcode']))
            self.table.setItem(i, 1, QTableWidgetItem(p['name']))
            self.table.setItem(i, 2, QTableWidgetItem(p.get('category', '')))
            self.table.setItem(i, 3, QTableWidgetItem('{:.2f}'.format(p['purchase_price'])))
            self.table.setItem(i, 4, QTableWidgetItem('{:.2f}'.format(p['selling_price'])))
            self.table.setItem(i, 5, QTableWidgetItem(str(p['stock_quantity'])))
            self.table.setItem(i, 6, QTableWidgetItem(p.get('unit', '个')))

            # Action buttons
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 2, 4, 2)
            btn_layout.setSpacing(4)

            edit_btn = PushButton('编辑')
            edit_btn.setFixedSize(55, 28)
            del_btn = PushButton('删除')
            del_btn.setFixedSize(55, 28)

            product_id = p['id']
            edit_btn.clicked.connect(lambda checked, pid=product_id: self._on_edit(pid))
            del_btn.clicked.connect(lambda checked, pid=product_id: self._on_delete(pid))

            btn_layout.addWidget(edit_btn)
            btn_layout.addWidget(del_btn)
            self.table.setCellWidget(i, 7, btn_widget)

    def _on_add(self):
        dialog = ProductEditDialog(parent=self.window())
        if dialog.exec_():
            data = dialog.get_data()
            result = ProductModel.create(**data)
            if result:
                InfoBar.success(
                    title='成功', content='商品已添加',
                    parent=self, position=InfoBarPosition.TOP, duration=2000)
                self._load_products()
                signal_bus.product_changed.emit()
            else:
                InfoBar.error(
                    title='失败', content='添加失败，条码可能重复',
                    parent=self, position=InfoBarPosition.TOP, duration=3000)

    def _on_edit(self, product_id):
        product = ProductModel.get_by_id(product_id)
        if not product:
            return
        dialog = ProductEditDialog(product=product, parent=self.window())
        if dialog.exec_():
            data = dialog.get_data()
            result = ProductModel.update(product_id, **data)
            if result:
                InfoBar.success(
                    title='成功', content='商品已更新',
                    parent=self, position=InfoBarPosition.TOP, duration=2000)
                self._load_products()
                signal_bus.product_changed.emit()
            else:
                InfoBar.error(
                    title='失败', content='更新失败',
                    parent=self, position=InfoBarPosition.TOP, duration=3000)

    def _on_delete(self, product_id):
        product = ProductModel.get_by_id(product_id)
        if not product:
            return
        w = MessageBox(
            '确认删除',
            '确定要删除商品 "{}" 吗？\n\n相关的销售记录和进货记录也将被一并删除。'.format(
                product['name']),
            self.window())
        w.yesButton.setText('确认')
        w.cancelButton.setText('取消')
        if w.exec_():
            ProductModel.delete(product_id)
            InfoBar.success(
                title='成功', content='商品已删除',
                parent=self, position=InfoBarPosition.TOP, duration=2000)
            self._load_products()
            signal_bus.product_changed.emit()
            signal_bus.transaction_completed.emit()
