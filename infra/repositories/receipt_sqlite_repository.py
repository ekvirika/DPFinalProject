from datetime import datetime
from typing import List
from uuid import UUID, uuid4

from core.models.errors import (
    InsufficientPaymentError,
    ReceiptNotFoundError,
    ReceiptStatusError,
)
from core.models.receipt import (
    Payment,
    PaymentCurrency,
    Receipt,
    ReceiptItem,
    ReceiptStatus,
)
from core.models.repositories.receipt_repository import ReceiptRepository
from infra.db.database import Database


class SQLiteReceiptRepository(ReceiptRepository):
    def __init__(self, database: Database):
        self.database = database

    def create(self, shift_id: UUID) -> Receipt:
        """Create a new receipt in the database."""
        with self.database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO receipts (shift_id, status, created_at, total_amount)
                VALUES (?, ?, ?, ?)
                """,
                (shift_id, ReceiptStatus.OPEN.value, datetime.now(), 0.0),
            )
            receipt_id = uuid4()
            return Receipt(
                id=receipt_id,
                shift_id=shift_id,
                items=[],
                status=ReceiptStatus.OPEN,
                created_at=datetime.now(),
                total_amount=0.0,
                payments=[],
            )

    def get(self, receipt_id: UUID) -> Receipt:
        """Retrieve a receipt by its ID, including its items and payments."""
        with self.database.get_connection() as conn:
            cursor = conn.cursor()

            # Fetch receipt
            cursor.execute("SELECT * FROM receipts WHERE id = ?", (receipt_id,))
            receipt_row = cursor.fetchone()
            if not receipt_row:
                raise ReceiptNotFoundError(str(receipt_id))

            # Fetch receipt items
            cursor.execute(
                "SELECT * FROM receipt_items WHERE receipt_id = ?", (receipt_id,)
            )
            items = [
                ReceiptItem(
                    product_id=row["product_id"],
                    quantity=row["quantity"],
                    unit_price=row["unit_price"],
                    discount=row["discount"],
                    campaign_id=row["campaign_id"],
                )
                for row in cursor.fetchall()
            ]

            # Fetch payments
            cursor.execute("SELECT * FROM payments WHERE receipt_id = ?", (receipt_id,))
            payments = [
                Payment(
                    amount=row["amount"],
                    currency=PaymentCurrency(row["currency"]),
                    exchange_rate=row["exchange_rate"],
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                )
                for row in cursor.fetchall()
            ]

            return Receipt(
                id=receipt_row["id"],
                shift_id=receipt_row["shift_id"],
                items=items,
                status=ReceiptStatus(receipt_row["status"]),
                created_at=datetime.fromisoformat(receipt_row["created_at"]),
                total_amount=receipt_row["total_amount"],
                discount_amount=receipt_row["discount_amount"],
                payments=payments,
            )

    def add_item(self, receipt_id: UUID, product_id: UUID, quantity: int) -> Receipt:
        """Add an item to a receipt."""
        receipt = self.get(receipt_id)
        if receipt.status != ReceiptStatus.OPEN:
            raise ReceiptStatusError(receipt.status, "add items to")

        with self.database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO receipt_items (receipt_id, product_id, quantity, unit_price)
                VALUES (?, ?, ?, ?)
                """,
                (receipt_id, product_id, quantity, 0.0),
            )
        return self.get(receipt_id)

    def update_status(self, receipt_id: UUID, status: ReceiptStatus) -> Receipt:
        """Update the status of a receipt."""
        receipt = self.get(receipt_id)
        if receipt.status == ReceiptStatus.PAID:
            raise ReceiptStatusError(receipt.status, "update")

        with self.database.get_connection() as conn:
            conn.execute(
                "UPDATE receipts SET status = ? WHERE id = ?",
                (status.value, receipt_id),
            )
        return self.get(receipt_id)

    def add_payment(self, receipt_id: UUID, payment: Payment) -> Receipt:
        """Add a payment to a receipt."""
        receipt = self.get(receipt_id)
        if receipt.status != ReceiptStatus.OPEN:
            raise ReceiptStatusError(receipt.status, "add payment to")

        if payment.amount < receipt.total_amount:
            raise InsufficientPaymentError()

        with self.database.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO payments (receipt_id, 
                amount,
                 currency,
                 exchange_rate,
                  timestamp)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    receipt_id,
                    payment.amount,
                    payment.currency.value,
                    payment.exchange_rate,
                    payment.timestamp.isoformat(),
                ),
            )
            conn.execute(
                "UPDATE receipts SET status = ? WHERE id = ?",
                (ReceiptStatus.PAID.value, receipt_id),
            )
        return self.get(receipt_id)

    def get_receipts_by_shift(self, shift_id: UUID) -> List[Receipt]:
        """Retrieve all receipts for a specific shift."""
        with self.database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM receipts WHERE shift_id = ?", (shift_id,))
            receipt_ids = [row["id"] for row in cursor.fetchall()]
            return [self.get(receipt_id) for receipt_id in receipt_ids]
