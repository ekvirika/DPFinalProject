from datetime import datetime
from typing import Union
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
from infra.api.schemas.shift import ShiftUpdate
from infra.db.database import Database
from infra.repositories.receipt_sqlite_repository import SQLiteReceiptRepository
from infra.repositories.shift_sqlite_repository import SQLiteShiftRepository


class SQLiteReportRepository(ReportRepository):
    def __init__(
        self,
        db: Database,
        receipt_repository: SQLiteReceiptRepository,
        shift_repository: SQLiteShiftRepository,
    ):
        self.db = db
        self.receipt_repository = receipt_repository
        self.shift_repository = shift_repository

    def generate_sales_report(self) -> SalesReport:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

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
                result["total_items"]
                if result and result["total_items"] is not None
                else 0
            )

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

            total_revenue = {}
            cursor.execute(
                """
                SELECT currency, SUM(payment_amount) as total_amount
                FROM payments
                WHERE status = ?
                GROUP BY currency
                """,
                (PaymentStatus.COMPLETED.value,),
            )
            payment_rows = cursor.fetchall()

            for row in payment_rows:
                currency_value = row["currency"]
                try:
                    currency_enum = Currency(currency_value)
                    total_revenue[currency_enum.value] = float(row["total_amount"])
                except (ValueError, TypeError) as e:
                    print(f"Error with currency {currency_value}: {e}")

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
                float(result["total_gel"])
                if result and result["total_gel"] is not None
                else 0.0
            )

            return SalesReport(
                total_items_sold=total_items_sold,
                total_receipts=total_receipts,
                total_revenue=total_revenue,
                total_revenue_gel=total_revenue_gel,
            )

    def generate_shift_report(self, shift_id: UUID) -> ShiftReport:
        receipts = self.receipt_repository.get_receipts_by_shift(shift_id)
        receipt_count = len(receipts)
        items_sold_dict: dict[UUID, dict[str, Union[UUID, int]]] = {}
        revenue_by_currency_dict: dict[str, float] = {}

        for receipt in receipts:
            for item in receipt.products:
                if item.product_id not in items_sold_dict:
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
                                "quantity": 0,
                            }

                # Fix for line 125 error - ensure we're using an integer
                current_quantity = int(items_sold_dict[item.product_id]["quantity"])
                items_sold_dict[item.product_id]["quantity"] = current_quantity + int(
                    item.quantity
                )

            for payment in receipt.payments:
                if payment.status == PaymentStatus.COMPLETED:
                    currency = payment.currency.value
                    if currency not in revenue_by_currency_dict:
                        revenue_by_currency_dict[currency] = 0.0
                    revenue_by_currency_dict[currency] += float(payment.payment_amount)

        # Fix for line 135 errors - explicitly cast types to ensure compatibility
        items_sold = [
            ItemSold(
                product_id=UUID(str(item["product_id"]))
                if not isinstance(item["product_id"], UUID)
                else item["product_id"],
                quantity=int(item["quantity"]),
            )
            for item in items_sold_dict.values()
        ]
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

    def generate_z_report(self, shift_id: UUID) -> ShiftReport:
        shift_report = self.generate_shift_report(shift_id)
        self.shift_repository.update_status(
            shift_id, ShiftUpdate(status="closed"), datetime.now()
        )
        return shift_report
