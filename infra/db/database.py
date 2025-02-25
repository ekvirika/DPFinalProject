import json
import sqlite3
from contextlib import contextmanager


class Database:
    def __init__(self, db_path: str = "pos_system.db"):
        self.db_path = db_path
        self._create_tables()

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _create_tables(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                price REAL NOT NULL
            )
            ''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS campaigns (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                campaign_type TEXT NOT NULL,
                rules TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1
            )
            ''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS shifts (
                id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                closed_at TIMESTAMP
            )
            ''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS receipts (
                id TEXT PRIMARY KEY,
                shift_id TEXT NOT NULL,
                status TEXT NOT NULL,
                subtotal REAL NOT NULL DEFAULT 0,
                discount_amount REAL NOT NULL DEFAULT 0,
                total REAL NOT NULL DEFAULT 0,
                FOREIGN KEY (shift_id) REFERENCES shifts (id)
            )
            ''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS receipt_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                receipt_id TEXT NOT NULL,
                product_id TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                total_price REAL NOT NULL,
                discounts TEXT NOT NULL DEFAULT '[]',
                final_price REAL NOT NULL,
                FOREIGN KEY (receipt_id) REFERENCES receipts (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
            ''')

            cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id TEXT PRIMARY KEY,
                receipt_id TEXT NOT NULL,
                payment_amount REAL NOT NULL,
                currency TEXT NOT NULL,
                total_in_gel REAL NOT NULL,
                exchange_rate REAL NOT NULL,
                status TEXT NOT NULL,
                FOREIGN KEY (receipt_id) REFERENCES receipts (id)
            )
            ''')

            conn.commit()


def serialize_json(obj):
    return json.dumps(obj)


def deserialize_json(json_str):
    if not json_str:
        return None
    return json.loads(json_str)