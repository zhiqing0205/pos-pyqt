# coding: utf-8
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
                              QFrame, QFormLayout)

from qfluentwidgets import (LineEdit, PasswordLineEdit, PrimaryPushButton,
                            SimpleCardWidget, SubtitleLabel, BodyLabel,
                            CaptionLabel, InfoBar, InfoBarPosition,
                            FluentIcon as FIF, setFont)

from ..models.settings import SettingsModel


def _make_form_row(label_text, widget):
    """Create a horizontal row with label and input widget."""
    row = QHBoxLayout()
    row.setSpacing(12)
    label = BodyLabel(label_text)
    label.setFixedWidth(80)
    row.addWidget(label)
    row.addWidget(widget, 1)
    return row


class SettingsInterface(QWidget):
    """Payment settings interface for admin users."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._load_settings()

    def _init_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(15)

        # ── WeChat Pay Card ──
        wechat_card = SimpleCardWidget(self)
        wc_layout = QVBoxLayout(wechat_card)
        wc_layout.setContentsMargins(25, 20, 25, 20)
        wc_layout.setSpacing(10)

        wc_title = SubtitleLabel('微信支付配置')
        wc_layout.addWidget(wc_title)

        wc_hint = CaptionLabel('配置完成后，结账时可选择微信支付')
        wc_hint.setStyleSheet('color: gray;')
        wc_layout.addWidget(wc_hint)
        wc_layout.addSpacing(5)

        self.wechat_appid = LineEdit()
        self.wechat_appid.setPlaceholderText('微信开放平台 APPID')
        wc_layout.addLayout(_make_form_row('APPID', self.wechat_appid))

        self.wechat_appsecret = PasswordLineEdit()
        self.wechat_appsecret.setPlaceholderText('微信开放平台 APPSECRET')
        wc_layout.addLayout(_make_form_row('APPSECRET', self.wechat_appsecret))

        self.wechat_mchid = LineEdit()
        self.wechat_mchid.setPlaceholderText('微信支付商户号')
        wc_layout.addLayout(_make_form_row('商户号', self.wechat_mchid))

        self.wechat_pay_key = PasswordLineEdit()
        self.wechat_pay_key.setPlaceholderText('微信支付 API 密钥')
        wc_layout.addLayout(_make_form_row('支付密钥', self.wechat_pay_key))

        layout.addWidget(wechat_card)

        # ── Alipay Card ──
        alipay_card = SimpleCardWidget(self)
        al_layout = QVBoxLayout(alipay_card)
        al_layout.setContentsMargins(25, 20, 25, 20)
        al_layout.setSpacing(10)

        al_title = SubtitleLabel('支付宝配置')
        al_layout.addWidget(al_title)

        al_hint = CaptionLabel('配置完成后，结账时可选择支付宝')
        al_hint.setStyleSheet('color: gray;')
        al_layout.addWidget(al_hint)
        al_layout.addSpacing(5)

        self.alipay_appid = LineEdit()
        self.alipay_appid.setPlaceholderText('支付宝 APPID')
        al_layout.addLayout(_make_form_row('APPID', self.alipay_appid))

        self.alipay_public_key = PasswordLineEdit()
        self.alipay_public_key.setPlaceholderText('支付宝公钥')
        al_layout.addLayout(_make_form_row('支付宝公钥', self.alipay_public_key))

        self.alipay_private_key = PasswordLineEdit()
        self.alipay_private_key.setPlaceholderText('商户私钥（RSA2）')
        al_layout.addLayout(_make_form_row('商户私钥', self.alipay_private_key))

        layout.addWidget(alipay_card)

        # ── Save Button ──
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.saveBtn = PrimaryPushButton(FIF.SAVE, '保存配置')
        self.saveBtn.setFixedHeight(38)
        self.saveBtn.clicked.connect(self._save_settings)
        btn_layout.addWidget(self.saveBtn)
        layout.addLayout(btn_layout)

        layout.addStretch()

        scroll.setWidget(container)
        outer.addWidget(scroll)

    def _load_settings(self):
        self.wechat_appid.setText(SettingsModel.get('wechat_appid'))
        self.wechat_appsecret.setText(SettingsModel.get('wechat_appsecret'))
        self.wechat_mchid.setText(SettingsModel.get('wechat_mchid'))
        self.wechat_pay_key.setText(SettingsModel.get('wechat_pay_key'))
        self.alipay_appid.setText(SettingsModel.get('alipay_appid'))
        self.alipay_public_key.setText(SettingsModel.get('alipay_public_key'))
        self.alipay_private_key.setText(SettingsModel.get('alipay_private_key'))

    def _save_settings(self):
        SettingsModel.set('wechat_appid', self.wechat_appid.text().strip())
        SettingsModel.set('wechat_appsecret', self.wechat_appsecret.text().strip())
        SettingsModel.set('wechat_mchid', self.wechat_mchid.text().strip())
        SettingsModel.set('wechat_pay_key', self.wechat_pay_key.text().strip())
        SettingsModel.set('alipay_appid', self.alipay_appid.text().strip())
        SettingsModel.set('alipay_public_key', self.alipay_public_key.text().strip())
        SettingsModel.set('alipay_private_key', self.alipay_private_key.text().strip())

        InfoBar.success(
            title='保存成功', content='支付配置已保存',
            parent=self, position=InfoBarPosition.TOP, duration=2000)
