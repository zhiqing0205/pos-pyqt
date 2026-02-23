# coding: utf-8
from datetime import datetime

from ..common.database import get_connection
from .product import ProductModel


class TransactionModel:
    """CRUD operations for transactions and transaction items."""

    @staticmethod
    def generate_transaction_no():
        return 'TXN' + datetime.now().strftime('%Y%m%d%H%M%S%f')[:20]

    @staticmethod
    def create(user_id, cart_items, total_amount, discount_amount, final_amount,
               payment_method, payment_ref=''):
        """
        Create a transaction with items and deduct stock.
        cart_items: list of dicts with keys:
            product_id, barcode, name, unit_price, quantity, discount_rate, subtotal
        Returns transaction_id or None.
        """
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        txn_no = TransactionModel.generate_transaction_no()

        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO transactions "
                "(transaction_no, user_id, total_amount, discount_amount, "
                "final_amount, payment_method, payment_ref, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (txn_no, user_id, total_amount, discount_amount,
                 final_amount, payment_method, payment_ref, now)
            )
            txn_id = cursor.lastrowid

            for item in cart_items:
                cursor.execute(
                    "INSERT INTO transaction_items "
                    "(transaction_id, product_id, barcode, product_name, "
                    "unit_price, quantity, discount_rate, subtotal) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (txn_id, item['product_id'], item['barcode'], item['name'],
                     item['unit_price'], item['quantity'], item['discount_rate'],
                     item['subtotal'])
                )
                # Deduct stock
                cursor.execute(
                    "UPDATE products SET stock_quantity = stock_quantity - ?, "
                    "updated_at = ? WHERE id = ?",
                    (item['quantity'], now, item['product_id'])
                )

            conn.commit()
            conn.close()
            return txn_id
        except Exception:
            conn.rollback()
            conn.close()
            return None

    @staticmethod
    def get_recent(limit=50):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT t.*, u.username FROM transactions t "
            "LEFT JOIN users u ON t.user_id = u.id "
            "ORDER BY t.id DESC LIMIT ?",
            (limit,)
        )
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    @staticmethod
    def get_items(transaction_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM transaction_items WHERE transaction_id = ?",
            (transaction_id,)
        )
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows
