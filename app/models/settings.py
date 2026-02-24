# coding: utf-8
from ..common.database import get_connection


class SettingsModel:
    """Key-value settings stored in the database."""

    @staticmethod
    def _ensure_table():
        conn = get_connection()
        conn.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL DEFAULT ''
            )
        ''')
        conn.commit()
        conn.close()

    @staticmethod
    def get(key, default=''):
        SettingsModel._ensure_table()
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        conn.close()
        return row['value'] if row else default

    @staticmethod
    def set(key, value):
        SettingsModel._ensure_table()
        conn = get_connection()
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, str(value))
        )
        conn.commit()
        conn.close()

    @staticmethod
    def get_all_by_prefix(prefix):
        SettingsModel._ensure_table()
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT key, value FROM settings WHERE key LIKE ?",
            (prefix + '%',)
        )
        result = {row['key']: row['value'] for row in cursor.fetchall()}
        conn.close()
        return result

    @staticmethod
    def is_wechat_configured():
        keys = ['wechat_appid', 'wechat_appsecret', 'wechat_mchid', 'wechat_pay_key']
        return all(SettingsModel.get(k) for k in keys)

    @staticmethod
    def is_alipay_configured():
        keys = ['alipay_appid', 'alipay_public_key', 'alipay_private_key']
        return all(SettingsModel.get(k) for k in keys)
