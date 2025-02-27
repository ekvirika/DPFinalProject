from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from core.models.repositories.shift_repository import ShiftRepository
from core.models.shift import Shift, ShiftStatus
from infra.db.database import Database


class SQLiteShiftRepository(ShiftRepository):
    def __init__(self, db: Database):
        self.db = db

    def create(self) -> Shift:
        shift = Shift(id=uuid4())

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO shifts (id, status,"
                " created_at, closed_at) VALUES (?, ?, ?, ?)",
                (str(shift.id), shift.status.value, shift.created_at, shift.closed_at),
            )
            conn.commit()

        return shift

    def get_by_id(self, shift_id: UUID) -> Optional[Shift]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM shifts WHERE id = ?", (str(shift_id),))
            row = cursor.fetchone()

            if row:
                return Shift(
                    id=row["id"],
                    status=ShiftStatus(row["status"]),
                    created_at=datetime.fromisoformat(row["created_at"]),
                    closed_at=datetime.fromisoformat(row["closed_at"])
                    if row["closed_at"]
                    else None,
                )

            return None

    def update_status(
        self, shift_id: UUID, status: ShiftStatus, closed_at: Optional[datetime] = None
    ) -> Optional[Shift]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE shifts SET status = ?, closed_at = ? WHERE id = ?",
                (status.value, closed_at, str(shift_id)),
            )
            conn.commit()

            if cursor.rowcount > 0:
                return self.get_by_id(shift_id)

            return None

    def get_current_open(self) -> Optional[Shift]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM shifts WHERE status = ? "
                "ORDER BY created_at DESC LIMIT 1",
                (ShiftStatus.OPEN.value,),
            )
            row = cursor.fetchone()

            if row:
                return Shift(
                    id=row["id"],
                    status=ShiftStatus(row["status"]),
                    created_at=datetime.fromisoformat(row["created_at"]),
                    closed_at=datetime.fromisoformat(row["closed_at"])
                    if row["closed_at"]
                    else None,
                )

            return None
