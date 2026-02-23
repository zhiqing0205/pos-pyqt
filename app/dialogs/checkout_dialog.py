# coding: utf-8
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel

from qfluentwidgets import (MessageBoxBase, ComboBox, LineEdit, BodyLabel,
                            TitleLabel, SubtitleLabel, setFont)

from ..models.transaction import TransactionModel
from ..common.auth import AuthManager


class CheckoutDialog(MessageBoxBase):
    """Checkout dialog for completing a transaction."""

    def __init__(self, final_amount, total_amount, discount_amount,
                 cart_items, parent=None):
        super().__init__(parent)
        self._final_amount = final_amount
        self._total_amount = total_amount
        self._discount_amount = discount_amount
        self._cart_items = cart_items

        self._init_ui()

    def _init_ui(self):
        # Title
        title = TitleLabel('结账')
        self.viewLayout.addWidget(title)

        # Amount display
        amount_label = BodyLabel('应收金额')
        self.viewLayout.addWidget(amount_label)

        self.amountDisplay = TitleLabel('¥{:.2f}'.format(self._final_amount))
        setFont(self.amountDisplay, 36)
        self.amountDisplay.setStyleSheet('color: #d32f2f;')
        self.viewLayout.addWidget(self.amountDisplay)

        self.viewLayout.addSpacing(15)

        # Payment method
        method_label = BodyLabel('付款方式')
        self.viewLayout.addWidget(method_label)

        self.methodCombo = ComboBox()
        self.methodCombo.addItems(['现金', '支付宝', '微信'])
        self.methodCombo.setFixedWidth(200)
        self.viewLayout.addWidget(self.methodCombo)

        self.viewLayout.addSpacing(10)

        # Payment amount / reference
        self.payLabel = BodyLabel('收款金额')
        self.viewLayout.addWidget(self.payLabel)

        self.payEdit = LineEdit()
        self.payEdit.setPlaceholderText('输入收款金额')
        self.payEdit.setText('{:.2f}'.format(self._final_amount))
        self.payEdit.setFixedWidth(200)
        self.viewLayout.addWidget(self.payEdit)

        # Change display
        self.changeLabel = BodyLabel('')
        self.viewLayout.addWidget(self.changeLabel)

        self.viewLayout.addSpacing(10)

        # Set button texts
        self.yesButton.setText('确认结账')
        self.cancelButton.setText('取消')

        # Connections
        self.methodCombo.currentIndexChanged.connect(self._on_method_changed)
        self.payEdit.textChanged.connect(self._update_change)

        # Set dialog width
        self.widget.setMinimumWidth(360)

        self._update_change()

    def _on_method_changed(self, index):
        if index == 0:  # Cash
            self.payLabel.setText('收款金额')
            self.payEdit.setPlaceholderText('输入收款金额')
            self.payEdit.setText('{:.2f}'.format(self._final_amount))
            self.changeLabel.show()
        else:  # Alipay / WeChat
            self.payLabel.setText('支付凭证号')
            self.payEdit.setPlaceholderText('输入凭证号（可选）')
            self.payEdit.clear()
            self.changeLabel.hide()

    def _update_change(self):
        if self.methodCombo.currentIndex() != 0:
            return
        try:
            paid = float(self.payEdit.text())
            change = paid - self._final_amount
            if change >= 0:
                self.changeLabel.setText('找零: ¥{:.2f}'.format(change))
                self.changeLabel.setStyleSheet('color: #2e7d32;')
            else:
                self.changeLabel.setText('金额不足: ¥{:.2f}'.format(abs(change)))
                self.changeLabel.setStyleSheet('color: #d32f2f;')
        except ValueError:
            self.changeLabel.setText('')

    def _validate(self):
        if self.methodCombo.currentIndex() == 0:  # Cash
            try:
                paid = float(self.payEdit.text())
                if paid < self._final_amount:
                    return False
            except ValueError:
                return False
        return True

    def accept(self):
        """Override accept to process the transaction."""
        if not self._validate():
            return

        methods = ['cash', 'alipay', 'wechat']
        method = methods[self.methodCombo.currentIndex()]
        payment_ref = ''
        if method != 'cash':
            payment_ref = self.payEdit.text().strip()

        user = AuthManager.current_user()
        result = TransactionModel.create(
            user_id=user['id'],
            cart_items=self._cart_items,
            total_amount=self._total_amount,
            discount_amount=self._discount_amount,
            final_amount=self._final_amount,
            payment_method=method,
            payment_ref=payment_ref,
        )

        if result:
            super().accept()
