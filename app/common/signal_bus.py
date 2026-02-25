# coding: utf-8
from PyQt5.QtCore import pyqtSignal, QObject


class SignalBus(QObject):
    """Global signal bus for inter-component communication."""

    # Emitted when cart changes (for updating summary)
    cart_changed = pyqtSignal()

    # Emitted when a product is updated (for refreshing product lists)
    product_changed = pyqtSignal()

    # Emitted when a user is updated
    user_changed = pyqtSignal()

    # Emitted when stock changes
    stock_changed = pyqtSignal()

    # Emitted when a transaction is completed
    transaction_completed = pyqtSignal()

    # Emitted when categories are updated
    category_changed = pyqtSignal()


signal_bus = SignalBus()
