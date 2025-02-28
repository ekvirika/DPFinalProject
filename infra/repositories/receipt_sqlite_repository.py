import uuid
from typing import List, Optional
from uuid import UUID, uuid4

from core.models.receipt import (
    Currency,
    Discount,
    Payment,
    PaymentStatus,
    Receipt,
    ReceiptItem,
    ReceiptStatus,
)
from core.models.repositories.receipt_repository import ReceiptRepository
from infra.db.database import Database


class SQLiteReceiptRepository(ReceiptRepository):
    def __init__(self, db: Database):
        self.db = db

    def create(self, shift_id: UUID) -> Receipt:
        """Create a new receipt."""
        receipt_id = uuid4()

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO receipts (id, shift_id, status, subtotal, discount_amount, total)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    str(receipt_id),
                    str(shift_id),
                    ReceiptStatus.OPEN.value,
                    0,
                    0,
                    0,
                ),
            )
            conn.commit()

        return Receipt(shift_id=shift_id, id=receipt_id)

    def get(self, receipt_id: UUID) -> Optional[Receipt]:
        """Get a receipt by ID with all its items, discounts, and payments."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            # Get receipt basic info
            cursor.execute(
                "SELECT * FROM receipts WHERE id = ?",
                (str(receipt_id),),
            )
            receipt_row = cursor.fetchone()

            if not receipt_row:
                return None

            receipt = Receipt(
                id=UUID(receipt_row["id"]),
                shift_id=UUID(receipt_row["shift_id"]),
                status=ReceiptStatus(receipt_row["status"]),
                subtotal=receipt_row["subtotal"],
                discount_amount=receipt_row["discount_amount"],
                total=receipt_row["total"],
            )

            # Get receipt items
            cursor.execute(
                "SELECT * FROM receipt_items WHERE receipt_id = ?",
                (str(receipt_id),),
            )
            item_rows = cursor.fetchall()

            for item_row in item_rows:
                item = ReceiptItem(
                    product_id=UUID(item_row["product_id"]),
                    quantity=item_row["quantity"],
                    unit_price=item_row["unit_price"],
                )
                item.total_price = item_row["total_price"]
                item.final_price = item_row["final_price"]

                # Get discounts for this item
                cursor.execute(
                    "SELECT * FROM receipt_item_discounts WHERE receipt_item_id = ?",
                    (item_row["id"],),
                )
                discount_rows = cursor.fetchall()

                for discount_row in discount_rows:
                    discount = Discount(
                        campaign_id=UUID(discount_row["campaign_id"]),
                        campaign_name=discount_row["campaign_name"],
                        discount_amount=discount_row["discount_amount"],
                    )
                    item.discounts.append(discount)

                receipt.products.append(item)

            # Get payments
            cursor.execute(
                "SELECT * FROM payments WHERE receipt_id = ?",
                (str(receipt_id),),
            )
            payment_rows = cursor.fetchall()

            for payment_row in payment_rows:
                payment = Payment(
                    id=UUID(payment_row["id"]),
                    receipt_id=UUID(payment_row["receipt_id"]),
                    payment_amount=payment_row["payment_amount"],
                    currency=Currency(payment_row["currency"]),
                    total_in_gel=payment_row["total_in_gel"],
                    exchange_rate=payment_row["exchange_rate"],
                    status=PaymentStatus(payment_row["status"]),
                )
                receipt.payments.append(payment)

            return receipt

    def update_status(
        self, receipt_id: UUID, status: ReceiptStatus
    ) -> Optional[Receipt]:
        """Update the status of a receipt."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE receipts SET status = ? WHERE id = ?",
                (status.value, str(receipt_id)),
            )
            conn.commit()

        return self.get(receipt_id)

    def add_payment(self, receipt_id: UUID, payment: Payment) -> Optional[Receipt]:
        """Add a payment to a receipt."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO payments
                (id, receipt_id, payment_amount, currency, total_in_gel, exchange_rate, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(payment.id),
                    str(receipt_id),
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
        """Get all receipts for a shift."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM receipts WHERE shift_id = ?",
                (str(shift_id),),
            )
            receipt_ids = [row["id"] for row in cursor.fetchall()]

        return [self.get(UUID(receipt_id)) for receipt_id in receipt_ids]

    def update(self, receipt_id: UUID, updated_receipt: Receipt) -> Receipt:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            # Update the receipt record
            cursor.execute(
                """UPDATE receipts 
                   SET subtotal = ?, discount_amount = ?, total = ?
                   WHERE id = ?""",
                (
                    updated_receipt.subtotal,
                    updated_receipt.discount_amount,
                    updated_receipt.total,
                    str(receipt_id),
                ),
            )

            # Handle receipt items - first delete existing items
            cursor.execute(
                "DELETE FROM receipt_items WHERE receipt_id = ?", (str(receipt_id),)
            )
            cursor.execute(
                "DELETE FROM receipt_item_discounts WHERE receipt_item_id IN (SELECT id FROM receipt_items WHERE receipt_id = ?)",
                (str(receipt_id),),
            )

            # Insert updated items
            for item in updated_receipt.products:
                # Generate a new ID for each item if not present
                item_id = str(uuid.uuid4()) if not hasattr(item, "id") else str(item.id)

                cursor.execute(
                    """INSERT INTO receipt_items 
                       (id, receipt_id, product_id, quantity, unit_price, total_price, final_price) 
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        item_id,
                        str(receipt_id),
                        str(item.product_id),
                        item.quantity,
                        item.unit_price,
                        item.total_price,
                        item.final_price,
                    ),
                )

                # Handle item discounts
                for discount in item.discounts:
                    cursor.execute(
                        """INSERT INTO receipt_item_discounts
                           (receipt_item_id, campaign_id, campaign_name, discount_amount)
                           VALUES (?, ?, ?, ?)""",
                        (
                            item_id,
                            str(discount.campaign_id),
                            discount.campaign_name,
                            discount.discount_amount,
                        ),
                    )

            # Handle payments if needed
            if hasattr(updated_receipt, "payments") and updated_receipt.payments:
                cursor.execute(
                    "DELETE FROM payments WHERE receipt_id = ?", (str(receipt_id),)
                )

                for payment in updated_receipt.payments:
                    payment_id = (
                        str(uuid.uuid4())
                        if not hasattr(payment, "id")
                        else str(payment.id)
                    )
                    cursor.execute(
                        """INSERT INTO payments
                           (id, receipt_id, payment_amount, currency, total_in_gel,
                            exchange_rate, status)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (
                            payment_id,
                            str(receipt_id),
                            payment.payment_amount,
                            payment.currency,
                            payment.total_in_gel,
                            payment.exchange_rate,
                            payment.status,
                        ),
                    )

            conn.commit()

            # Fetch the updated receipt
            cursor.execute("SELECT * FROM receipts WHERE id = ?", (str(receipt_id),))
            receipt_data = cursor.fetchone()

            if not receipt_data:
                raise ValueError(f"Receipt with id {receipt_id} not found after update")

            # Get the items for this receipt
            cursor.execute(
                "SELECT id, product_id, quantity, unit_price FROM receipt_items WHERE receipt_id = ?",
                (str(receipt_id),),
            )
            items_data = cursor.fetchall()

            # Rebuild receipt items
            items = []
            for item_data in items_data:
                item_id = item_data[0]

                # Get discounts for this item
                cursor.execute(
                    """SELECT campaign_id, campaign_name, discount_amount 
                       FROM receipt_item_discounts 
                       WHERE receipt_item_id = ?""",
                    (item_id,),
                )
                discount_data = cursor.fetchall()

                # Build discounts list
                discounts = []
                for disc in discount_data:
                    discounts.append(
                        Discount(
                            campaign_id=uuid.UUID(disc[0]),
                            campaign_name=disc[1],
                            discount_amount=disc[2],
                        )
                    )

                # Create receipt item - the total_price and final_price will be calculated in __post_init__
                items.append(
                    ReceiptItem(
                        product_id=uuid.UUID(item_data[1]),
                        quantity=item_data[2],
                        unit_price=item_data[3],
                        discounts=discounts,
                    )
                )

            # Get payments if any
            payments = []
            if hasattr(updated_receipt, "payments"):
                cursor.execute(
                    "SELECT id, payment_amount, currency,"
                    " total_in_gel, exchange_rate, status "
                    "FROM payments WHERE receipt_id = ?",
                    (str(receipt_id),),
                )
                payment_data = cursor.fetchall()

                for pay in payment_data:
                    payments.append(
                        Payment(
                            id=uuid.UUID(pay[0]),
                            payment_amount=pay[1],
                            currency=pay[2],
                            total_in_gel=pay[3],
                            exchange_rate=pay[4],
                            status=pay[5],
                        )
                    )

            # Construct and return the updated Receipt object
            return Receipt(
                id=uuid.UUID(receipt_data[0]),
                shift_id=uuid.UUID(receipt_data[1]),
                status=receipt_data[2],
                subtotal=receipt_data[3],
                discount_amount=receipt_data[4],
                total=receipt_data[5],
                products=items,
                payments=payments if hasattr(updated_receipt, "payments") else None,
            )
