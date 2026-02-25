# coding: utf-8
from ..common.database import get_connection


class CategoryModel:
    """CRUD operations for product categories."""

    @staticmethod
    def get_all():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM categories ORDER BY sort_order, id")
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    @staticmethod
    def get_names():
        """Return category names sorted by sort_order."""
        return [c['name'] for c in CategoryModel.get_all()]

    @staticmethod
    def get_by_id(cat_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM categories WHERE id = ?", (cat_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def get_next_sort_order():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COALESCE(MAX(sort_order), 0) + 1 FROM categories")
        val = cursor.fetchone()[0]
        conn.close()
        return val

    @staticmethod
    def create(name, sort_order=0):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO categories (name, sort_order) VALUES (?, ?)",
                (name, sort_order)
            )
            conn.commit()
            conn.close()
            return True
        except Exception:
            conn.rollback()
            conn.close()
            return False

    @staticmethod
    def update(cat_id, name, sort_order):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            # If name changed, cascade to products
            cursor.execute("SELECT name FROM categories WHERE id = ?", (cat_id,))
            row = cursor.fetchone()
            if row and row[0] != name:
                cursor.execute(
                    "UPDATE products SET category = ? WHERE category = ?",
                    (name, row[0])
                )
            cursor.execute(
                "UPDATE categories SET name = ?, sort_order = ? WHERE id = ?",
                (name, sort_order, cat_id)
            )
            conn.commit()
            conn.close()
            return True
        except Exception:
            conn.rollback()
            conn.close()
            return False

    @staticmethod
    def delete(cat_id):
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT name FROM categories WHERE id = ?", (cat_id,))
            row = cursor.fetchone()
            if row:
                cursor.execute(
                    "UPDATE products SET category = '其他' WHERE category = ?",
                    (row[0],)
                )
            cursor.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
            conn.commit()
            conn.close()
            return True
        except Exception:
            conn.rollback()
            conn.close()
            return False

    @staticmethod
    def product_count(name):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM products WHERE category = ? AND is_active = 1",
            (name,)
        )
        val = cursor.fetchone()[0]
        conn.close()
        return val
