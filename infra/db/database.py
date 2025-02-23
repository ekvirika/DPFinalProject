import sqlite3
from contextlib import contextmanager
from typing import Generator, Protocol

class Database(Protocol):
    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        ...

    def init_db(self) -> None:
        ...

class SQLiteDatabase:
    def __init__(self, db_path: str):
        self.db_path = db_path

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def init_db(self) -> None:
        with self.get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    price REAL NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS campaigns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    start_date TIMESTAMP NOT NULL,
                    end_date TIMESTAMP NOT NULL,
                    conditions JSON NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT 1,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS shifts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cashier_id INTEGER NOT NULL,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP,
                    status TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS receipts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    shift_id INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    total_amount REAL NOT NULL,
                    discount_amount REAL,
                    FOREIGN KEY (shift_id) REFERENCES shifts (id)
                );

                CREATE TABLE IF NOT EXISTS receipt_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    receipt_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    unit_price REAL NOT NULL,
                    discount REAL,
                    campaign_id INTEGER,
                    FOREIGN KEY (receipt_id) REFERENCES receipts (id),
                    FOREIGN KEY (product_id) REFERENCES products (id),
                    FOREIGN KEY (campaign_id) REFERENCES campaigns (id)
                );

                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    receipt_id INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    currency TEXT NOT NULL,
                    exchange_rate REAL NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    FOREIGN KEY (receipt_id) REFERENCES receipts (id)
                );
            """)