# coding: utf-8
from datetime import datetime

from ..common.database import get_connection


class ProductModel:
    """CRUD operations for products."""

    @staticmethod
    def get_all(include_inactive=False):
        conn = get_connection()
        cursor = conn.cursor()
        if include_inactive:
            cursor.execute("SELECT * FROM products ORDER BY id DESC")
        else:
            cursor.execute("SELECT * FROM products WHERE is_active = 1 ORDER BY id DESC")
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    @staticmethod
    def get_by_id(product_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def get_by_barcode(barcode):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM products WHERE barcode = ? AND is_active = 1",
            (barcode,)
        )
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def search(keyword):
        conn = get_connection()
        cursor = conn.cursor()
        like = '%{}%'.format(keyword)
        cursor.execute(
            "SELECT * FROM products WHERE is_active = 1 AND "
            "(barcode LIKE ? OR name LIKE ? OR category LIKE ?) "
            "ORDER BY id DESC",
            (like, like, like)
        )
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    @staticmethod
    def get_categories():
        """Get all distinct categories."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT DISTINCT category FROM products WHERE is_active = 1 AND category != '' ORDER BY category"
        )
        rows = [r['category'] for r in cursor.fetchall()]
        conn.close()
        return rows

    @staticmethod
    def get_by_category(category):
        """Get all active products in a category."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM products WHERE is_active = 1 AND category = ? ORDER BY name",
            (category,)
        )
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    @staticmethod
    def create(barcode, name, category='', purchase_price=0, selling_price=0,
               stock_quantity=0, unit='个'):
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO products (barcode, name, category, purchase_price, "
                "selling_price, stock_quantity, unit, is_active, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)",
                (barcode, name, category, purchase_price, selling_price,
                 stock_quantity, unit, now, now)
            )
            conn.commit()
            pid = cursor.lastrowid
            conn.close()
            return pid
        except Exception:
            conn.close()
            return None

    @staticmethod
    def update(product_id, **kwargs):
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        allowed = ['barcode', 'name', 'category', 'purchase_price',
                    'selling_price', 'stock_quantity', 'unit', 'is_active']
        fields = []
        values = []
        for key in allowed:
            if key in kwargs:
                fields.append("{} = ?".format(key))
                values.append(kwargs[key])

        if not fields:
            return False

        fields.append("updated_at = ?")
        values.append(now)
        values.append(product_id)

        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE products SET {} WHERE id = ?".format(", ".join(fields)),
                values
            )
            conn.commit()
            conn.close()
            return True
        except Exception:
            conn.close()
            return False

    @staticmethod
    def update_stock(product_id, quantity_change):
        """Increment or decrement stock. quantity_change can be negative."""
        conn = get_connection()
        cursor = conn.cursor()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute(
            "UPDATE products SET stock_quantity = stock_quantity + ?, updated_at = ? "
            "WHERE id = ?",
            (quantity_change, now, product_id)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def delete(product_id):
        """Soft-delete."""
        return ProductModel.update(product_id, is_active=0)
