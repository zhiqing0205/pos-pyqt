# coding: utf-8
from datetime import datetime

from ..common.database import get_connection
from .product import ProductModel


class StockInModel:
    """CRUD operations for stock-in records."""

    @staticmethod
    def create(product_id, barcode, product_name, quantity, purchase_price, operator_id, note=''):
        """Create a stock-in record and update product stock + purchase price."""
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        total_cost = quantity * purchase_price

        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO stock_in_records "
                "(product_id, barcode, product_name, quantity, purchase_price, "
                "total_cost, operator_id, note, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (product_id, barcode, product_name, quantity, purchase_price,
                 total_cost, operator_id, note, now)
            )
            # Update product stock and purchase price
            cursor.execute(
                "UPDATE products SET stock_quantity = stock_quantity + ?, "
                "purchase_price = ?, updated_at = ? WHERE id = ?",
                (quantity, purchase_price, now, product_id)
            )
            conn.commit()
            record_id = cursor.lastrowid
            conn.close()
            return record_id
        except Exception:
            conn.rollback()
            conn.close()
            return None

    @staticmethod
    def get_recent(limit=100):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT s.*, u.username as operator_name FROM stock_in_records s "
            "LEFT JOIN users u ON s.operator_id = u.id "
            "ORDER BY s.id DESC LIMIT ?",
            (limit,)
        )
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows
