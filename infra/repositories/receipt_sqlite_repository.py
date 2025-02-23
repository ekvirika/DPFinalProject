from datetime import datetime
from decimal import Decimal
from typing import List, Optional
import sqlite3

from core.models.receipt import (
    Receipt,
    ReceiptItem,
    ReceiptStatus,
    Payment,
)
from core.models.repositories.receipt_repository import ReceiptRepository


class SQLiteReceiptRepository(ReceiptRepository):
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS receipts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    shift_id INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    total_amount DECIMAL NOT NULL,
                    discount_amount DECIMAL
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS receipt_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    receipt_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    unit_price DECIMAL NOT NULL,
                    discount DECIMAL,
                    campaign_id INTEGER,
                    FOREIGN KEY (receipt_id) REFERENCES receipts (id)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    receipt_id INTEGER NOT NULL,
                    amount DECIMAL NOT NULL,
                    currency TEXT NOT NULL,
                    exchange_rate DECIMAL NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    FOREIGN KEY (receipt_id) REFERENCES receipts (id)
                )
            """)

    def create(self, shift_id: int) -> Receipt:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO receipts (shift_id, status, created_at, total_amount)
                VALUES (?, ?, ?, ?)
                """,
                (shift_id, ReceiptStatus.OPEN.value, datetime.now(), Decimal("0.0")),
            )
            receipt_id = cursor.lastrowid
            return Receipt(
                id=receipt_id,
                shift_id=shift_id,
                items=[],
                status=ReceiptStatus.OPEN,
                created_at=datetime.now(),
                total_amount=Decimal("0.0"),
                payments=[]
            )

    def get(self, receipt_id: int) -> Optional[Receipt]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get receipt
            cursor.execute("SELECT * FROM receipts WHERE id = ?", (receipt_id,))
            receipt_row = cursor.fetchone()
            if not receipt_row:
                return None

            # Get items
            cursor.execute("SELECT * FROM receipt_items WHERE receipt_id = ?", (receipt_id,))
            items = [
                ReceiptItem(
                    product_id=row["product_id"],
                    quantity=row["quantity"],
                    unit_price=Decimal(str(row["unit_price"])),
                    discount=Decimal(str(row["discount"])) if row["discount"] else None,
                    campaign_id=row["campaign_id"]
                )
                for row in cursor.fetchall()
            ]

            # Get payments
            cursor.execute("SELECT * FROM payments WHERE receipt_id = ?", (receipt_id,))
            payments = [
                Payment(
                    amount=Decimal(str(row["amount"])),
                    currency=PaymentCurrency(row["currency"]),
                    exchange_rate=Decimal(str(row["exchange_rate"])),
                    timestamp=datetime.fromisoformat(row["timestamp"])
                )
                for row in cursor.fetchall()
            ]

            return Receipt(
                id=receipt_row["id"],
                shift_id=receipt_row["shift_id"],
                items=items,
                status=ReceiptStatus(receipt_row["status"]),
                created_at=datetime.fromisoformat(receipt_row["created_at"]),
                total_amount=Decimal(str(receipt_row["total_amount"])),
                discount_amount=Decimal(str(receipt_row["discount_amount"])) if receipt_row[
                    "discount_amount"] else None,
                payments=payments
            )

    def add_item(self, receipt_id: int, product_id: int, quantity: int) -> Receipt:
        # Note: This is a simplified version. In a real implementation,
        # you would need to fetch the product price and apply campaign rules
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO receipt_items (receipt_id, product_id, quantity, unit_price)
                VALUES (?, ?, ?, ?)
                """,
                (receipt_id, product_id, quantity, Decimal("0.0")),  # Price should come from product service
            )
        return self.get(receipt_id)

    def update_status(self, receipt_id: int, status: ReceiptStatus) -> Receipt:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE receipts SET status = ? WHERE id = ?",
                (status.value, receipt_id),
            )
        return self.get(receipt_id)

    def add_payment(self, receipt_id: int, payment: Payment) -> Receipt:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO payments (receipt_id, amount, currency, exchange_rate, timestamp)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    receipt_id,
                    str(payment.amount),
                    payment.currency.value,
                    str(payment.exchange_rate),
                    payment.timestamp.isoformat(),
                ),
            )
            conn.execute(
                "UPDATE receipts SET status = ? WHERE id = ?",
                (ReceiptStatus.PAID.value, receipt_id),
            )
        return self.get(receipt_id)

    def get_receipts_by_shift(self, shift_id: int) -> List[Receipt]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM receipts WHERE shift_id = ?", (shift_id,))
            receipt_ids = [row["id"] for row in cursor.fetchall()]
            return [self.get(receipt_id) for receipt_id in receipt_ids]