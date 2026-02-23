# coding: utf-8
import hashlib

from .database import get_connection


class AuthManager:
    """Manages user authentication and session state."""

    _current_user = None

    @classmethod
    def hash_password(cls, password):
        return hashlib.sha256(password.encode()).hexdigest()

    @classmethod
    def login(cls, username, password):
        """Attempt login. Returns user dict on success, None on failure."""
        conn = get_connection()
        cursor = conn.cursor()
        password_hash = cls.hash_password(password)
        cursor.execute(
            "SELECT id, username, role, is_active FROM users "
            "WHERE username = ? AND password = ?",
            (username, password_hash)
        )
        row = cursor.fetchone()
        conn.close()

        if row is None:
            return None
        if not row['is_active']:
            return None

        cls._current_user = {
            'id': row['id'],
            'username': row['username'],
            'role': row['role'],
        }
        return cls._current_user

    @classmethod
    def logout(cls):
        cls._current_user = None

    @classmethod
    def current_user(cls):
        return cls._current_user

    @classmethod
    def is_admin(cls):
        return cls._current_user and cls._current_user['role'] == 'admin'
