# coding: utf-8
from datetime import datetime

from ..common.database import get_connection
from ..common.auth import AuthManager


class UserModel:
    """CRUD operations for users."""

    @staticmethod
    def get_all():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, role, is_active, created_at, updated_at "
            "FROM users ORDER BY id"
        )
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    @staticmethod
    def get_by_id(user_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, role, is_active, created_at, updated_at "
            "FROM users WHERE id = ?", (user_id,)
        )
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def create(username, password, role='clerk'):
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        password_hash = AuthManager.hash_password(password)
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, password, role, is_active, created_at, updated_at) "
                "VALUES (?, ?, ?, 1, ?, ?)",
                (username, password_hash, role, now, now)
            )
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            return user_id
        except Exception:
            conn.close()
            return None

    @staticmethod
    def update(user_id, username=None, password=None, role=None, is_active=None):
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn = get_connection()
        cursor = conn.cursor()

        fields = []
        values = []
        if username is not None:
            fields.append("username = ?")
            values.append(username)
        if password is not None:
            fields.append("password = ?")
            values.append(AuthManager.hash_password(password))
        if role is not None:
            fields.append("role = ?")
            values.append(role)
        if is_active is not None:
            fields.append("is_active = ?")
            values.append(is_active)

        if not fields:
            conn.close()
            return False

        fields.append("updated_at = ?")
        values.append(now)
        values.append(user_id)

        try:
            cursor.execute(
                "UPDATE users SET {} WHERE id = ?".format(", ".join(fields)),
                values
            )
            conn.commit()
            conn.close()
            return True
        except Exception:
            conn.close()
            return False

    @staticmethod
    def delete(user_id):
        """Hard-delete a user and cascade delete related records."""
        conn = get_connection()
        cursor = conn.cursor()
        try:
            # Delete transaction items for this user's transactions
            cursor.execute(
                "SELECT id FROM transactions WHERE user_id = ?", (user_id,))
            txn_ids = [r[0] for r in cursor.fetchall()]
            for txn_id in txn_ids:
                cursor.execute(
                    "DELETE FROM transaction_items WHERE transaction_id = ?",
                    (txn_id,))
            cursor.execute(
                "DELETE FROM transactions WHERE user_id = ?", (user_id,))
            cursor.execute(
                "DELETE FROM stock_in_records WHERE operator_id = ?",
                (user_id,))
            cursor.execute(
                "DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            conn.close()
            return True
        except Exception:
            conn.rollback()
            conn.close()
            return False
