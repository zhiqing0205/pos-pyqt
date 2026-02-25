# coding: utf-8
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QHeaderView,
                              QTableWidgetItem, QAbstractItemView)

from qfluentwidgets import (PushButton, PrimaryPushButton, SpinBox,
                            TableWidget, InfoBar, InfoBarPosition,
                            FluentIcon as FIF, MessageBox, MessageBoxBase,
                            SubtitleLabel, BodyLabel, LineEdit, setFont)

from ..models.category import CategoryModel
from ..common.signal_bus import signal_bus


class CategoryEditDialog(MessageBoxBase):
    """Dialog for adding or editing a category."""

    def __init__(self, category=None, default_sort=0, parent=None):
        super().__init__(parent)
        self._category = category
        self._result_data = None

        is_edit = category is not None
        title = SubtitleLabel('编辑分类' if is_edit else '添加分类')
        self.viewLayout.addWidget(title)
        self.viewLayout.addSpacing(10)

        self.viewLayout.addWidget(BodyLabel('分类名称'))
        self.nameEdit = LineEdit()
        self.nameEdit.setPlaceholderText('输入分类名称')
        if is_edit:
            self.nameEdit.setText(category['name'])
        self.viewLayout.addWidget(self.nameEdit)

        self.viewLayout.addSpacing(8)

        self.viewLayout.addWidget(BodyLabel('排序（数字越小越靠前）'))
        self.sortSpin = SpinBox()
        self.sortSpin.setRange(0, 999)
        self.sortSpin.setValue(category['sort_order'] if is_edit else default_sort)
        self.viewLayout.addWidget(self.sortSpin)

        self.yesButton.setText('保存')
        self.cancelButton.setText('取消')
        self.widget.setMinimumWidth(350)

    def get_data(self):
        return self._result_data

    def accept(self):
        name = self.nameEdit.text().strip()
        if not name:
            return
        self._result_data = {
            'name': name,
            'sort_order': self.sortSpin.value(),
        }
        super().accept()


class CategoryInterface(QWidget):
    """Category management interface for admin users."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._load_categories()

        signal_bus.category_changed.connect(self._load_categories)
        signal_bus.product_changed.connect(self._load_categories)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(10)

        # Top bar
        top_layout = QHBoxLayout()
        top_layout.setSpacing(10)
        top_layout.addStretch()

        self.addBtn = PrimaryPushButton(FIF.ADD, '添加分类')
        top_layout.addWidget(self.addBtn)

        layout.addLayout(top_layout)

        # Table
        self.table = TableWidget(self)
        self.table.setBorderVisible(True)
        self.table.setBorderRadius(8)
        self.table.setWordWrap(False)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            ['分类名称', '排序', '商品数', '操作'])
        self.table.verticalHeader().hide()
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        self.table.setColumnWidth(1, 120)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 140)

        layout.addWidget(self.table, 1)

        # Connections
        self.addBtn.clicked.connect(self._on_add)

    def _load_categories(self):
        categories = CategoryModel.get_all()
        self.table.setRowCount(len(categories))
        for i, cat in enumerate(categories):
            self.table.setItem(i, 0, QTableWidgetItem(cat['name']))

            # Sort SpinBox
            spin = SpinBox()
            spin.setRange(0, 999)
            spin.setValue(cat['sort_order'])
            spin.setFixedHeight(30)
            cat_id = cat['id']
            spin.valueChanged.connect(
                lambda val, cid=cat_id: self._on_sort_changed(cid, val))
            self.table.setCellWidget(i, 1, spin)

            # Product count
            count = CategoryModel.product_count(cat['name'])
            count_item = QTableWidgetItem(str(count))
            count_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 2, count_item)

            # Action buttons
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 2, 4, 2)
            btn_layout.setSpacing(4)

            edit_btn = PushButton('编辑')
            edit_btn.setFixedSize(55, 28)
            del_btn = PushButton('删除')
            del_btn.setFixedSize(55, 28)

            edit_btn.clicked.connect(
                lambda checked, cid=cat_id: self._on_edit(cid))
            del_btn.clicked.connect(
                lambda checked, cid=cat_id: self._on_delete(cid))

            btn_layout.addWidget(edit_btn)
            btn_layout.addWidget(del_btn)
            self.table.setCellWidget(i, 3, btn_widget)

    def _on_add(self):
        default_sort = CategoryModel.get_next_sort_order()
        dialog = CategoryEditDialog(
            default_sort=default_sort, parent=self.window())
        if dialog.exec_():
            data = dialog.get_data()
            if CategoryModel.create(data['name'], data['sort_order']):
                InfoBar.success(
                    title='成功', content='分类已添加',
                    parent=self, position=InfoBarPosition.TOP, duration=2000)
                self._load_categories()
                signal_bus.category_changed.emit()
            else:
                InfoBar.error(
                    title='失败', content='添加失败，分类名称可能重复',
                    parent=self, position=InfoBarPosition.TOP, duration=3000)

    def _on_edit(self, cat_id):
        cat = CategoryModel.get_by_id(cat_id)
        if not cat:
            return
        dialog = CategoryEditDialog(category=cat, parent=self.window())
        if dialog.exec_():
            data = dialog.get_data()
            if CategoryModel.update(cat_id, data['name'], data['sort_order']):
                InfoBar.success(
                    title='成功', content='分类已更新',
                    parent=self, position=InfoBarPosition.TOP, duration=2000)
                self._load_categories()
                signal_bus.category_changed.emit()
                signal_bus.product_changed.emit()
            else:
                InfoBar.error(
                    title='失败', content='更新失败，名称可能重复',
                    parent=self, position=InfoBarPosition.TOP, duration=3000)

    def _on_delete(self, cat_id):
        cat = CategoryModel.get_by_id(cat_id)
        if not cat:
            return
        w = MessageBox(
            '确认删除',
            '确定要删除分类「{}」吗？\n\n该分类下的商品将被移至「其他」分类。'.format(
                cat['name']),
            self.window())
        w.yesButton.setText('确认')
        w.cancelButton.setText('取消')
        if w.exec_():
            CategoryModel.delete(cat_id)
            InfoBar.success(
                title='成功', content='分类已删除',
                parent=self, position=InfoBarPosition.TOP, duration=2000)
            self._load_categories()
            signal_bus.category_changed.emit()
            signal_bus.product_changed.emit()

    def _on_sort_changed(self, cat_id, value):
        cat = CategoryModel.get_by_id(cat_id)
        if cat:
            CategoryModel.update(cat_id, cat['name'], value)
            signal_bus.category_changed.emit()
