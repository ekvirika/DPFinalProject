# infra/repositories/shift_sqlite_repository.py
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from core.models.shift import Shift, ShiftReport, ShiftStatus
from infra.db.database import Database


class SQLiteShiftRepository:
    def __init__(self, database: Database):
        self.database = database

    def create(self, cashier_id: str) -> Shift:
        """Create a new shift for a cashier."""
        new_shift_id = uuid4()
        now = datetime.utcnow()

        with self.database.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO shifts (id, cashier_id, start_time, status, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    str(new_shift_id),
                    cashier_id,
                    now.isoformat(),
                    ShiftStatus.OPEN.value,
                    now.isoformat()
                )
            )
            conn.commit()

            shift = Shift(
                id=new_shift_id,
                cashier_id=cashier_id,
                start_time=now,
                status=ShiftStatus.OPEN,
                created_at=now
            )

            return shift

    def get_by_id(self, shift_id: UUID) -> Optional[Shift]:
        """Retrieve a shift by its ID."""
        with self.database.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM shifts WHERE id = ?",
                (str(shift_id),)
            ).fetchone()

            if not row:
                return None

            return Shift(
                id=UUID(row["id"]),
                cashier_id=row["cashier_id"],
                start_time=datetime.fromisoformat(row["start_time"]),
                status=ShiftStatus(row["status"]),
                end_time=datetime.fromisoformat(row["end_time"]) if row["end_time"] else None,
                created_at=datetime.fromisoformat(row["created_at"])
            )

    def get_all(self) -> List[Shift]:
        """Retrieve all shifts."""
        with self.database.get_connection() as conn:
            rows = conn.execute("SELECT * FROM shifts").fetchall()

            shifts = []
            for row in rows:
                shifts.append(Shift(
                    id=UUID(row["id"]),
                    cashier_id=row["cashier_id"],
                    start_time=datetime.fromisoformat(row["start_time"]),
                    status=ShiftStatus(row["status"]),
                    end_time=datetime.fromisoformat(row["end_time"]) if row["end_time"] else None,
                    created_at=datetime.fromisoformat(row["created_at"])
                ))

            return shifts

    def close(self, shift_id: UUID) -> Optional[Shift]:
        """Close an open shift."""
        shift = self.get_by_id(shift_id)

        if not shift:
            return None

        if shift.status == ShiftStatus.CLOSED:
            return shift

        now = datetime.utcnow()

        with self.database.get_connection() as conn:
            conn.execute(
                """
                UPDATE shifts
                SET status = ?, end_time = ?
                WHERE id = ?
                """,
                (ShiftStatus.CLOSED.value, now.isoformat(), str(shift_id))
            )
            conn.commit()

            return Shift(
                id=shift.id,
                cashier_id=shift.cashier_id,
                start_time=shift.start_time,
                status=ShiftStatus.CLOSED,
                end_time=now,
                created_at=shift.created_at
            )

    def get_open_shift_by_cashier(self, cashier_id: str) -> Optional[Shift]:
        """Get open shift for a cashier if exists."""
        with self.database.get_connection() as conn:
            row = conn.execute(
                """
                SELECT * FROM shifts
                WHERE cashier_id = ? AND status = ?
                """,
                (cashier_id, ShiftStatus.OPEN.value)
            ).fetchone()

            if not row:
                return None

            return Shift(
                id=UUID(row["id"]),
                cashier_id=row["cashier_id"],
                start_time=datetime.fromisoformat(row["start_time"]),
                status=ShiftStatus(row["status"]),
                end_time=datetime.fromisoformat(row["end_time"]) if row["end_time"] else None,
                created_at=datetime.fromisoformat(row["created_at"])
            )

    def get_x_report(self, shift_id: UUID) -> Optional[ShiftReport]:
        """Generate X report for a shift without closing it."""
        shift = self.get_by_id(shift_id)

        if not shift:
            return None

        return self._generate_report(shift_id)

    def get_z_report(self, shift_id: UUID) -> Optional[ShiftReport]:
        """Generate Z report and close the shift."""
        shift = self.get_by_id(shift_id)

        if not shift or shift.status == ShiftStatus.CLOSED:
            return None

        # Close the shift
        self.close(shift_id)

        return self._generate_report(shift_id)

    def _generate_report(self, shift_id: UUID) -> ShiftReport:
        """Generate a report with statistics for a shift."""
        with self.database.get_connection() as conn:
            # Count total receipts in shift
            total_receipts = conn.execute(
                """
                SELECT COUNT(*) as count
                FROM receipts
                WHERE shift_id = ? AND status = 'PAID'
                """,
                (str(shift_id),)
            ).fetchone()["count"]

            # Get items sold grouped by product
            items_sold: Dict[UUID, int] = {}
            product_rows = conn.execute(
                """
                SELECT ri.product_id, SUM(ri.quantity) as total_quantity
                FROM receipt_items ri
                JOIN receipts r ON r.id = ri.receipt_id
                WHERE r.shift_id = ? AND r.status = 'PAID'
                GROUP BY ri.product_id
                """,
                (str(shift_id),)
            ).fetchall()

            for row in product_rows:
                items_sold[UUID(row["product_id"])] = row["total_quantity"]

            # Get revenue by currency
            revenue_by_currency: Dict[str, float] = {}
            revenue_rows = conn.execute(
                """
                SELECT p.currency, SUM(p.amount) as total_amount
                FROM payments p
                JOIN receipts r ON r.id = p.receipt_id
                WHERE r.shift_id = ? AND r.status = 'PAID'
                GROUP BY p.currency
                """,
                (str(shift_id),)
            ).fetchall()

            for row in revenue_rows:
                revenue_by_currency[row["currency"]] = float(row["total_amount"])

            return ShiftReport(
                total_receipts=total_receipts,
                items_sold=items_sold,
                revenue_by_currency=revenue_by_currency
            )