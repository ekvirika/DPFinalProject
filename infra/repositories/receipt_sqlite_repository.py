from typing import List, Optional
from uuid import UUID, uuid4

from core.models.receipt import (
    Currency,
    Discount,
    Payment,
    Receipt,
    ReceiptItem,
    ReceiptStatus,
    PaymentStatus,
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

    def update(self, receipt: Receipt) -> Receipt:
        """Update a receipt and all its items, discounts, and payments."""
        with self.db.get_connection() as conn:
            conn.execute("BEGIN TRANSACTION")
            cursor = conn.cursor()

            # Update receipt basics
            cursor.execute(
                """
                UPDATE receipts 
                SET status = ?, subtotal = ?, discount_amount = ?, total = ?
                WHERE id = ?
                """,
                (
                    receipt.status.value,
                    receipt.subtotal,
                    receipt.discount_amount,
                    receipt.total,
                    str(receipt.id),
                ),
            )

            # Get existing items
            cursor.execute(
                "SELECT id, product_id FROM receipt_items WHERE receipt_id = ?",
                (str(receipt.id),),
            )
            existing_items = {UUID(row["product_id"]): row["id"] for row in cursor.fetchall()}

            # Update or insert items
            for item in receipt.products:
                if item.product_id in existing_items:
                    # Update existing item
                    item_id = existing_items[item.product_id]
                    cursor.execute(
                        """
                        UPDATE receipt_items
                        SET quantity = ?, unit_price = ?, total_price = ?, final_price = ?
                        WHERE id = ?
                        """,
                        (
                            item.quantity,
                            item.unit_price,
                            item.total_price,
                            item.final_price,
                            item_id,
                        ),
                    )

                    # Delete old discounts
                    cursor.execute(
                        "DELETE FROM receipt_item_discounts WHERE receipt_item_id = ?",
                        (item_id,),
                    )

                    # Insert new discounts
                    for discount in item.discounts:
                        cursor.execute(
                            """
                            INSERT INTO receipt_item_discounts 
                            (receipt_item_id, campaign_id, campaign_name, discount_amount)
                            VALUES (?, ?, ?, ?)
                            """,
                            (
                                item_id,
                                str(discount.campaign_id),
                                discount.campaign_name,
                                discount.discount_amount,
                            ),
                        )
                else:
                    # Insert new item
                    item_id = str(uuid4())
                    cursor.execute(
                        """
                        INSERT INTO receipt_items
                        (id, receipt_id, product_id, quantity, unit_price, total_price, final_price)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            item_id,
                            str(receipt.id),
                            str(item.product_id),
                            item.quantity,
                            item.unit_price,
                            item.total_price,
                            item.final_price,
                        ),
                    )

                    # Insert discounts
                    for discount in item.discounts:
                        cursor.execute(
                            """
                            INSERT INTO receipt_item_discounts 
                            (receipt_item_id, campaign_id, campaign_name, discount_amount)
                            VALUES (?, ?, ?, ?)
                            """,
                            (
                                item_id,
                                str(discount.campaign_id),
                                discount.campaign_name,
                                discount.discount_amount,
                            ),
                        )

            # Remove items not in updated receipt
            current_product_ids = {str(item.product_id) for item in receipt.products}
            for product_id, item_id in existing_items.items():
                if product_id not in current_product_ids:
                    cursor.execute(
                        "DELETE FROM receipt_item_discounts WHERE receipt_item_id = ?",
                        (item_id,),
                    )
                    cursor.execute(
                        "DELETE FROM receipt_items WHERE id = ?",
                        (item_id,),
                    )

            conn.commit()

        return receipt

    def update_status(self, receipt_id: UUID, status: ReceiptStatus) -> Optional[Receipt]:
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