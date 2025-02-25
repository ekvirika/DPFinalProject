from typing import List, Optional

from core.models.receipt import Payment, Currency, PaymentStatus
from infra.db.database import Database


class SQLitePaymentRepository:
    def __init__(self, db: Database):
        self.db = db

    def create(self, receipt_id: str, amount: float, currency: Currency,
               total_in_gel: float, exchange_rate: float) -> Payment:
        payment = Payment(
            receipt_id=receipt_id,
            payment_amount=amount,
            currency=currency,
            total_in_gel=total_in_gel,
            exchange_rate=exchange_rate
        )

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO payments 
                   (id, receipt_id, payment_amount, currency, total_in_gel, exchange_rate, status) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (payment.id, payment.receipt_id, payment.payment_amount, payment.currency.value,
                 payment.total_in_gel, payment.exchange_rate, payment.status.value)
            )
            conn.commit()

        return payment

    def update_status(self, payment_id: str, status: str) -> Optional[Payment]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE payments SET status = ? WHERE id = ?",
                (status, payment_id)
            )
            conn.commit()

            if cursor.rowcount > 0:
                cursor.execute("SELECT * FROM payments WHERE id = ?", (payment_id,))
                row = cursor.fetchone()

                if row:
                    return Payment(
                        id=row["id"],
                        receipt_id=row["receipt_id"],
                        payment_amount=row["payment_amount"],
                        currency=Currency(row["currency"]),
                        total_in_gel=row["total_in_gel"],
                        exchange_rate=row["exchange_rate"],
                        status=PaymentStatus(row["status"])
                    )

            return None

    def get_by_receipt(self, receipt_id: str) -> List[Payment]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM payments WHERE receipt_id = ?", (receipt_id,))
            rows = cursor.fetchall()

            return [
                Payment(
                    id=row["id"],
                    receipt_id=row["receipt_id"],
                    payment_amount=row["payment_amount"],
                    currency=Currency(row["currency"]),
                    total_in_gel=row["total_in_gel"],
                    exchange_rate=row["exchange_rate"],
                    status=PaymentStatus(row["status"])
                )
                for row in rows
            ]