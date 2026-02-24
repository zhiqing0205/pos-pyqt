# coding: utf-8
"""Statistics queries for dashboard."""
from datetime import datetime, timedelta

from ..common.database import get_connection


class StatsModel:

    @staticmethod
    def today_sales():
        """Return today's transaction count and total revenue."""
        today = datetime.now().strftime('%Y-%m-%d')
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) as cnt, COALESCE(SUM(final_amount), 0) as total "
            "FROM transactions WHERE created_at LIKE ?",
            (today + '%',)
        )
        row = cur.fetchone()
        conn.close()
        return {'count': row['cnt'], 'revenue': row['total']}

    @staticmethod
    def today_items_sold():
        """Return total items sold today."""
        today = datetime.now().strftime('%Y-%m-%d')
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT COALESCE(SUM(ti.quantity), 0) as total "
            "FROM transaction_items ti "
            "JOIN transactions t ON ti.transaction_id = t.id "
            "WHERE t.created_at LIKE ?",
            (today + '%',)
        )
        row = cur.fetchone()
        conn.close()
        return row['total']

    @staticmethod
    def product_summary():
        """Return total products and low stock count (< 10)."""
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) as total, "
            "SUM(CASE WHEN stock_quantity < 10 THEN 1 ELSE 0 END) as low_stock "
            "FROM products WHERE is_active = 1"
        )
        row = cur.fetchone()
        conn.close()
        return {'total': row['total'], 'low_stock': row['low_stock']}

    @staticmethod
    def sales_last_7_days():
        """Return daily revenue for the last 7 days."""
        results = []
        for i in range(6, -1, -1):
            day = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                "SELECT COALESCE(SUM(final_amount), 0) as total "
                "FROM transactions WHERE created_at LIKE ?",
                (day + '%',)
            )
            row = cur.fetchone()
            conn.close()
            label = (datetime.now() - timedelta(days=i)).strftime('%m/%d')
            results.append({'date': label, 'revenue': row['total']})
        return results

    @staticmethod
    def category_sales():
        """Return sales by category for the last 30 days."""
        since = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT p.category, COALESCE(SUM(ti.subtotal), 0) as total "
            "FROM transaction_items ti "
            "JOIN transactions t ON ti.transaction_id = t.id "
            "JOIN products p ON ti.product_id = p.id "
            "WHERE t.created_at >= ? AND p.category != '' "
            "GROUP BY p.category ORDER BY total DESC LIMIT 8",
            (since,)
        )
        rows = [{'category': r['category'], 'total': r['total']}
                for r in cur.fetchall()]
        conn.close()
        return rows

    @staticmethod
    def top_products(limit=10):
        """Return top selling products by quantity in last 30 days."""
        since = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT ti.product_name, SUM(ti.quantity) as qty, "
            "SUM(ti.subtotal) as revenue "
            "FROM transaction_items ti "
            "JOIN transactions t ON ti.transaction_id = t.id "
            "WHERE t.created_at >= ? "
            "GROUP BY ti.product_name ORDER BY qty DESC LIMIT ?",
            (since, limit)
        )
        rows = [{'name': r['product_name'], 'quantity': r['qty'],
                 'revenue': r['revenue']} for r in cur.fetchall()]
        conn.close()
        return rows

    @staticmethod
    def low_stock_products(threshold=10, limit=10):
        """Return products with stock below threshold."""
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT name, stock_quantity, category FROM products "
            "WHERE is_active = 1 AND stock_quantity < ? "
            "ORDER BY stock_quantity ASC LIMIT ?",
            (threshold, limit)
        )
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    @staticmethod
    def payment_method_stats():
        """Return payment method breakdown for last 30 days."""
        since = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT payment_method, COUNT(*) as cnt, "
            "COALESCE(SUM(final_amount), 0) as total "
            "FROM transactions WHERE created_at >= ? "
            "GROUP BY payment_method",
            (since,)
        )
        rows = [{'method': r['payment_method'], 'count': r['cnt'],
                 'total': r['total']} for r in cur.fetchall()]
        conn.close()
        return rows

    @staticmethod
    def monthly_sales():
        """Return current month's transaction count and revenue."""
        month = datetime.now().strftime('%Y-%m')
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) as cnt, COALESCE(SUM(final_amount), 0) as total "
            "FROM transactions WHERE created_at LIKE ?",
            (month + '%',)
        )
        row = cur.fetchone()
        conn.close()
        return {'count': row['cnt'], 'revenue': row['total']}

    @staticmethod
    def avg_order_value():
        """Return today's average order value."""
        today = datetime.now().strftime('%Y-%m-%d')
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT COALESCE(AVG(final_amount), 0) as avg_val "
            "FROM transactions WHERE created_at LIKE ?",
            (today + '%',)
        )
        row = cur.fetchone()
        conn.close()
        return row['avg_val']

    @staticmethod
    def inventory_value():
        """Return total inventory value (stock * selling_price)."""
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT COALESCE(SUM(stock_quantity * selling_price), 0) as total "
            "FROM products WHERE is_active = 1"
        )
        row = cur.fetchone()
        conn.close()
        return row['total']

    @staticmethod
    def recent_transactions(limit=10):
        """Return the most recent transactions with basic info."""
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT t.transaction_no, t.final_amount, t.payment_method, "
            "t.created_at, u.username "
            "FROM transactions t "
            "LEFT JOIN users u ON t.user_id = u.id "
            "ORDER BY t.id DESC LIMIT ?",
            (limit,)
        )
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    @staticmethod
    def sales_last_7_days_count():
        """Return daily transaction count for the last 7 days."""
        results = []
        for i in range(6, -1, -1):
            day = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                "SELECT COUNT(*) as cnt FROM transactions "
                "WHERE created_at LIKE ?",
                (day + '%',)
            )
            row = cur.fetchone()
            conn.close()
            label = (datetime.now() - timedelta(days=i)).strftime('%m/%d')
            results.append({'date': label, 'count': row['cnt']})
        return results
