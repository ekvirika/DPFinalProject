from typing import Dict, List, Any
from uuid import UUID
from sqlite3 import Connection


from core.models.errors import ReceiptNotFoundError
from core.models.receipt import (
    Currency,
    Discount,
    Payment,
    PaymentStatus,
    Receipt,
    ReceiptItem,
    ReceiptStatus,
)
from core.models.repositories.product_repository import ProductRepository
from core.models.repositories.receipt_repository import ReceiptRepository
from infra.db.database import Database, deserialize_json, serialize_json


class SQLiteReceiptRepository(ReceiptRepository):
    def __init__(self, db: Database):
        self.database = db

    def create(self, shift_id: UUID) -> Receipt:
        receipt = Receipt(shift_id)

        with self.database.get_connection() as conn:  # type: Connection
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO receipts (id, shift_id,"
                " status, subtotal, discount_amount, "
                "total) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    receipt.id,
                    receipt.shift_id,
                    receipt.status.value,
                    receipt.subtotal,
                    receipt.discount_amount,
                    receipt.total,
                ),
            )
            conn.commit()

        return receipt

    def get(self, receipt_id: UUID) -> Receipt:
        """Retrieve a receipt by its ID, including its items and payments."""
        with self.database.get_connection() as conn:  # type: Connection
            cursor = conn.cursor()

            # Fetch receipt
            cursor.execute("SELECT * FROM receipts WHERE id = ?", (receipt_id,))
            receipt_row = cursor.fetchone()
            if not receipt_row:
                raise ReceiptNotFoundError(str(receipt_id))

        receipt = Receipt(
            id=receipt_row["id"],
            shift_id=receipt_row["shift_id"],
            status=ReceiptStatus(receipt_row["status"]),
            subtotal=receipt_row["subtotal"],
            discount_amount=receipt_row["discount_amount"],
            total=receipt_row["total"],
        )

        # Get receipt items
        cursor.execute(
            "SELECT * FROM receipt_items WHERE receipt_id = ?", (receipt_id,)
        )
        item_rows = cursor.fetchall()

        for item_row in item_rows:
            discounts = [
                Discount(**discount_dict)
                for discount_dict in deserialize_json(item_row["discounts"])
            ]

            receipt_item = ReceiptItem(
                product_id=UUID(item_row["product_id"]),  # Convert to UUID
                quantity=item_row["quantity"],
                unit_price=item_row["unit_price"],
                discounts=discounts,
            )
            receipt_item.total_price = item_row["total_price"]
            receipt_item.final_price = item_row["final_price"]

            receipt.products.append(receipt_item)

        # Get payments
        cursor.execute("SELECT * FROM payments WHERE receipt_id = ?", (receipt_id,))
        payment_rows = cursor.fetchall()

        for payment_row in payment_rows:
            payment = Payment(
                id=payment_row["id"],
                receipt_id=payment_row["receipt_id"],
                payment_amount=payment_row["payment_amount"],
                currency=Currency(payment_row["currency"]),
                total_in_gel=payment_row["total_in_gel"],
                exchange_rate=payment_row["exchange_rate"],
                status=PaymentStatus(payment_row["status"]),
            )

            receipt.payments.append(payment)

        return receipt

    def add_product(
        self,
        receipt_id: UUID,
        product_id: UUID,
        quantity: int,
        unit_price: float,
        discounts: List[Dict[str, Any]],  # Add type arguments
    ) -> Receipt:
        discount_objects = [Discount(**discount) for discount in discounts]
        receipt_item = ReceiptItem(
            product_id=product_id,  # Already UUID
            quantity=quantity,
            unit_price=unit_price,
            discounts=discount_objects,
        )

        with self.database.get_connection() as conn:  # type: Connection
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO receipt_items 
                   (receipt_id, product_id, 
                   quantity, unit_price, 
                   total_price, discounts, 
                   final_price) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    receipt_id,
                    product_id,
                    quantity,
                    unit_price,
                    receipt_item.total_price,
                    serialize_json([vars(d) for d in discount_objects]),
                    receipt_item.final_price,
                ),
            )

            # Update receipt totals
            receipt = self.get(receipt_id)
            if receipt:
                receipt.recalculate_totals()

                cursor.execute(
                    "UPDATE receipts SET subtotal = ?, "
                    "discount_amount = ?, total = ? WHERE id = ?",
                    (
                        receipt.subtotal,
                        receipt.discount_amount,
                        receipt.total,
                        receipt_id,
                    ),
                )

                conn.commit()
                return receipt

            conn.rollback()
            raise ReceiptNotFoundError(
                str(receipt_id)
            )  # Add a return or raise statement

    def update_status(self, receipt_id: UUID, status: ReceiptStatus) \
            -> Receipt:
        """Update the status of a receipt."""
        with self.database.get_connection() as conn:  # type: Connection
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE receipts SET status = ? WHERE id = ?",
                (status.value, receipt_id),
            )
            conn.commit()

            if cursor.rowcount > 0:
                return self.get(receipt_id)
            raise ReceiptNotFoundError(str(receipt_id))

    def add_payment(self, receipt_id: UUID, payment: Payment) -> Receipt:
        with self.database.get_connection() as conn:  # type: Connection
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO payments 
                   (id, receipt_id, payment_amount, 
                   currency, total_in_gel, exchange_rate, status) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    payment.id,
                    payment.receipt_id,
                    payment.payment_amount,
                    payment.currency.value,
                    payment.total_in_gel,
                    payment.exchange_rate,
                    payment.status.value,
                ),
            )
            conn.commit()

            return self.get(receipt_id)

    def get_receipts_by_shift(self, shift_id: UUID) -> List[Receipt]:
        """Retrieve all receipts for a specific shift."""
        with self.database.get_connection() as conn:  # type: Connection
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM receipts WHERE shift_id = ?", (shift_id,))
            rows = cursor.fetchall()

            return [self.get(UUID(row["id"])) for row in rows]  # Ensure UUID conversion
