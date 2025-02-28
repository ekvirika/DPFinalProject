from typing import Optional
from uuid import UUID

from core.models.receipt import (
    Currency,
    ItemSold,
    PaymentStatus,
    ReceiptStatus,
    RevenueByCurrency,
)
from core.models.report import SalesReport, ShiftReport
from core.models.repositories.report_repository import ReportRepository
from infra.db.database import Database
from infra.repositories.receipt_sqlite_repository import SQLiteReceiptRepository


class SQLiteReportRepository(ReportRepository):
    def __init__(self, db: Database, receipt_repository: SQLiteReceiptRepository):
        self.db = db
        self.receipt_repository = receipt_repository

    def generate_shift_report(self, shift_id: UUID) -> Optional[ShiftReport]:
        receipts = self.receipt_repository.get_receipts_by_shift(shift_id)

        if not receipts:
            return None

        # Count receipts
        receipt_count = len(receipts)

        # Count items sold
        items_sold_dict = {}
        revenue_by_currency_dict: dict[str, float] = {}

        for receipt in receipts:
            # Count items
            for item in receipt.products:
                if item.product_id not in items_sold_dict:
                    # Get product to get name
                    with self.db.get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            "SELECT name FROM products WHERE id = ?",
                            (str(item.product_id),),
                        )
                        product_row = cursor.fetchone()

                        if product_row:
                            items_sold_dict[item.product_id] = {
                                "product_id": item.product_id,
                                "name": product_row["name"],
                                "quantity": 0,
                            }

                items_sold_dict[item.product_id]["quantity"] += item.quantity

            # Sum revenue by currency
            for payment in receipt.payments:
                currency = payment.currency.value
                if currency not in revenue_by_currency_dict:
                    revenue_by_currency_dict[currency] = 0

                revenue_by_currency_dict[currency] += payment.payment_amount

        items_sold = [ItemSold(**item) for item in items_sold_dict.values()]
        revenue_by_currency = [
            RevenueByCurrency(currency=Currency(currency), amount=amount)
            for currency, amount in revenue_by_currency_dict.items()
        ]

        return ShiftReport(
            shift_id=shift_id,
            receipt_count=receipt_count,
            items_sold=items_sold,
            revenue_by_currency=revenue_by_currency,
        )

    def generate_sales_report(self) -> SalesReport:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            # Get total items sold
            cursor.execute(
                """
                SELECT SUM(quantity) as total_items 
                FROM receipt_items
                JOIN receipts ON receipt_items.receipt_id = receipts.id
                WHERE receipts.status = ?
            """,
                (ReceiptStatus.CLOSED.value,),
            )
            result = cursor.fetchone()
            total_items_sold = (
                result["total_items"] if result and result["total_items"] else 0
            )

            # Get total receipts
            cursor.execute(
                """
                SELECT COUNT(*) as receipt_count 
                FROM receipts 
                WHERE status = ?
            """,
                (ReceiptStatus.CLOSED.value,),
            )
            result = cursor.fetchone()
            total_receipts = result["receipt_count"] if result else 0

            # Get total revenue by currency
            cursor.execute(
                """
                SELECT currency, SUM(payment_amount) as total_amount 
                FROM payments
                WHERE status = ?
                GROUP BY currency
            """,
                (PaymentStatus.COMPLETED.value,),
            )
            rows = cursor.fetchall()

            total_revenue = {}
            for row in rows:
                total_revenue[row["currency"]] = row["total_amount"]

            # Get total revenue in GEL
            cursor.execute(
                """
                SELECT SUM(total_in_gel) as total_gel 
                FROM payments
                WHERE status = ?
            """,
                (PaymentStatus.COMPLETED.value,),
            )
            result = cursor.fetchone()
            total_revenue_gel = (
                result["total_gel"] if result and result["total_gel"] else 0
            )

            return SalesReport(
                total_items_sold=total_items_sold,
                total_receipts=total_receipts,
                total_revenue=total_revenue,
                total_revenue_gel=total_revenue_gel,
            )
