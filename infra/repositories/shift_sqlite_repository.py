from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from core.models.errors import (
    ShiftNotFoundError,
    ShiftStatusError,
    ShiftStatusValueError,
)
from core.models.repositories.shift_repository import ShiftRepository
from core.models.shift import Shift, ShiftStatus
from infra.api.schemas.shift import ShiftUpdate
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

    def get_by_id(self, shift_id: UUID) -> Shift:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM shifts WHERE id = ?", (str(shift_id),))
            row = cursor.fetchone()

            if row is None:
                raise ShiftNotFoundError(str(shift_id))

            return Shift(
                id=row["id"],
                status=ShiftStatus(row["status"]),
                created_at=datetime.fromisoformat(row["created_at"]),
                closed_at=datetime.fromisoformat(row["closed_at"])
                if row["closed_at"]
                else None,
            )

    def update_status(
        self, shift_id: UUID, status: ShiftUpdate, closed_at: Optional[datetime] = None
    ) -> Shift:
        try:
            status_enum = ShiftStatus(status.status)
        except ValueError:
            raise ShiftStatusValueError

        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            result = self.get_by_id(shift_id)

            current_status = ShiftStatus(result.status)
            if current_status == status_enum:
                raise ShiftStatusError()

            cursor.execute(
                "UPDATE shifts SET status = ?, closed_at = ? WHERE id = ?",
                (status_enum.value, closed_at, str(shift_id)),
            )
            conn.commit()

            return self.get_by_id(shift_id)
