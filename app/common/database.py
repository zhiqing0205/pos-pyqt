# coding: utf-8
import sqlite3
import hashlib
from datetime import datetime

from .config import DB_PATH


def get_connection():
    """Get a new SQLite connection with WAL mode and foreign keys enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Create all tables and seed default data."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'clerk',
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barcode TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT '',
            purchase_price REAL NOT NULL DEFAULT 0,
            selling_price REAL NOT NULL DEFAULT 0,
            stock_quantity INTEGER NOT NULL DEFAULT 0,
            unit TEXT NOT NULL DEFAULT '个',
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_no TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            total_amount REAL NOT NULL DEFAULT 0,
            discount_amount REAL NOT NULL DEFAULT 0,
            final_amount REAL NOT NULL DEFAULT 0,
            payment_method TEXT NOT NULL DEFAULT 'cash',
            payment_ref TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transaction_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            barcode TEXT NOT NULL,
            product_name TEXT NOT NULL,
            unit_price REAL NOT NULL,
            quantity INTEGER NOT NULL,
            discount_rate REAL NOT NULL DEFAULT 1.0,
            subtotal REAL NOT NULL,
            FOREIGN KEY (transaction_id) REFERENCES transactions(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_in_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            barcode TEXT NOT NULL,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            purchase_price REAL NOT NULL,
            total_cost REAL NOT NULL,
            operator_id INTEGER NOT NULL,
            note TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products(id),
            FOREIGN KEY (operator_id) REFERENCES users(id)
        )
    ''')

    # Seed default admin user if no users exist
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        password_hash = hashlib.sha256('admin123'.encode()).hexdigest()
        cursor.execute(
            "INSERT INTO users (username, password, role, is_active, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ('admin', password_hash, 'admin', 1, now, now)
        )

    # Seed common products if products table is empty
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        seed_products = [
            # (barcode, name, category, purchase_price, selling_price, stock, unit)
            ('6901028075862', '可口可乐 330ml', '饮料', 1.80, 3.00, 100, '瓶'),
            ('6901028071048', '雪碧 330ml', '饮料', 1.80, 3.00, 100, '瓶'),
            ('6902827110013', '百事可乐 330ml', '饮料', 1.80, 3.00, 100, '瓶'),
            ('6920584430048', '王老吉 310ml', '饮料', 3.50, 5.00, 80, '罐'),
            ('6921168550012', '冰红茶 500ml', '饮料', 2.00, 3.50, 100, '瓶'),
            ('4890008100118', '维他柠檬茶 250ml', '饮料', 2.50, 4.00, 80, '盒'),
            ('6922266446368', '怡宝纯净水 555ml', '水', 0.80, 2.00, 200, '瓶'),
            ('6902538004045', '农夫山泉 550ml', '水', 0.80, 2.00, 200, '瓶'),
            ('6921168500109', '百岁山 570ml', '水', 1.00, 3.00, 150, '瓶'),
            ('6907992513485', '伊利纯牛奶 250ml', '奶品', 2.50, 4.00, 80, '盒'),
            ('6902693004813', '蒙牛纯牛奶 250ml', '奶品', 2.50, 4.00, 80, '盒'),
            ('6907992500812', '伊利酸奶 200g', '奶品', 3.00, 5.00, 60, '杯'),
            ('6902083890117', '青岛啤酒 330ml', '酒', 2.50, 5.00, 100, '瓶'),
            ('6903252710168', '雪花啤酒 330ml', '酒', 2.00, 4.00, 100, '瓶'),
            ('6920108400014', '红牛 250ml', '饮料', 4.00, 6.00, 80, '罐'),
            ('6920152400012', '康师傅红烧牛肉面', '方便面', 2.50, 4.50, 100, '包'),
            ('6920152400029', '康师傅酸菜牛肉面', '方便面', 2.50, 4.50, 100, '包'),
            ('6921581500106', '统一老坛酸菜面', '方便面', 2.50, 4.50, 80, '包'),
            ('6924743915480', '乐事薯片 75g', '零食', 3.50, 6.00, 60, '包'),
            ('6916804200052', '旺旺雪饼 84g', '零食', 2.50, 5.00, 60, '包'),
            ('6902827111317', '奥利奥饼干 97g', '零食', 3.00, 5.50, 60, '包'),
            ('6901668004154', '卫龙辣条 78g', '零食', 1.50, 3.00, 80, '包'),
            ('6923450600047', '德芙巧克力 43g', '零食', 5.00, 8.00, 50, '块'),
            ('6921734900852', '蒙牛冰淇淋', '零食', 2.00, 4.00, 50, '支'),
            ('6901236341708', '海飞丝洗发水 200ml', '日用品', 15.00, 25.00, 40, '瓶'),
            ('6920174730364', '心相印纸巾', '日用品', 3.00, 6.00, 100, '包'),
        ]
        for barcode, name, cat, pp, sp, stock, unit in seed_products:
            cursor.execute(
                "INSERT INTO products (barcode, name, category, purchase_price, "
                "selling_price, stock_quantity, unit, is_active, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)",
                (barcode, name, cat, pp, sp, stock, unit, now, now)
            )

    conn.commit()
    conn.close()
