import json
import sqlite3
from contextlib import contextmanager
from typing import Any, Generator


class Database:
    def __init__(self, db_path: str = "pos_system.db"):
        self.db_path = db_path
        self._create_tables()

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, Any, None]:
        """
        Yields a SQLite database connection.
        The connection is automatically closed when the context manager exits.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _create_tables(self) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                price REAL NOT NULL
            )
            """)

            cursor.execute("""
            -- Campaigns table
            CREATE TABLE IF NOT EXISTS campaigns (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                campaign_type TEXT NOT NULL,
                is_active INTEGER DEFAULT 1
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS discount_rules (
                id TEXT PRIMARY KEY,
                campaign_id TEXT NOT NULL,
                discount_value REAL NOT NULL,
                applies_to TEXT NOT NULL,
                min_amount REAL DEFAULT 0,
                FOREIGN KEY (campaign_id) REFERENCES campaigns (id) ON DELETE CASCADE
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS buy_n_get_n_rules (
                id TEXT PRIMARY KEY,
                campaign_id TEXT NOT NULL,
                buy_product_id TEXT NOT NULL,
                buy_quantity INTEGER NOT NULL,
                get_product_id TEXT NOT NULL,
                get_quantity INTEGER NOT NULL,
                FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE
            );
            """)

            cursor.execute("""
            -- Combo rules table
            CREATE TABLE IF NOT EXISTS combo_rules (
                id TEXT PRIMARY KEY,
                campaign_id TEXT NOT NULL,
                discount_type TEXT NOT NULL,
                discount_value REAL NOT NULL,
                FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE
            );
            """)

            cursor.execute("""
            -- Products for combo rules (many-to-many relationship)
            CREATE TABLE IF NOT EXISTS combo_rule_products (
                combo_rule_id TEXT NOT NULL,
                product_id TEXT NOT NULL,
                PRIMARY KEY (combo_rule_id, product_id),
                FOREIGN KEY (combo_rule_id) REFERENCES combo_rules(id) ON DELETE CASCADE
            );
            """)

            cursor.execute("""
            -- Products for discount rules (when applies_to = 'products')
            CREATE TABLE  IF NOT EXISTS discount_rule_products (
                discount_rule_id TEXT NOT NULL,
                product_id TEXT NOT NULL,
                PRIMARY KEY (discount_rule_id, product_id),
                FOREIGN KEY (discount_rule_id) REFERENCES discount_rules(id)
                 ON DELETE CASCADE
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS shifts (
                id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                closed_at TIMESTAMP
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS receipts (
                id TEXT PRIMARY KEY,
                shift_id TEXT NOT NULL,
                status TEXT NOT NULL,
                subtotal REAL NOT NULL DEFAULT 0,
                discount_amount REAL NOT NULL DEFAULT 0,
                total REAL NOT NULL DEFAULT 0,
                FOREIGN KEY (shift_id) REFERENCES shifts (id)
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS receipt_items (
                id TEXT PRIMARY KEY,
                receipt_id TEXT NOT NULL,
                product_id TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                total_price REAL NOT NULL,
                final_price REAL NOT NULL,
                FOREIGN KEY (receipt_id) REFERENCES receipts (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
            """)

            cursor.execute("""
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
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS receipt_item_discounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                receipt_item_id TEXT NOT NULL,
                campaign_id TEXT NOT NULL,
                campaign_name TEXT NOT NULL,
                discount_amount REAL NOT NULL,
                FOREIGN KEY (receipt_item_id) REFERENCES receipt_items
                 (id) ON DELETE CASCADE,
                FOREIGN KEY (campaign_id) REFERENCES campaigns (id)
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS receipt_discounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                receipt_id TEXT NOT NULL,
                campaign_id TEXT NOT NULL,
                campaign_name TEXT NOT NULL,
                discount_amount REAL NOT NULL,
                FOREIGN KEY (receipt_id) REFERENCES receipts
                 (id) ON DELETE CASCADE,
                FOREIGN KEY (campaign_id) REFERENCES campaigns (id)
            );
            """)

            conn.commit()


def serialize_json(obj: Any) -> str:
    return json.dumps(obj)


def deserialize_json(json_str: str) -> Any:
    return json.loads(json_str)
