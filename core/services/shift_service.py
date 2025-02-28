from datetime import datetime
from uuid import UUID

from core.models.repositories.shift_repository import ShiftRepository
from core.models.shift import Shift
from infra.api.schemas.shift import ShiftUpdate


class ShiftService:
    def __init__(self, shift_repository: ShiftRepository):
        self.shift_repository = shift_repository

    def open_shift(self) -> Shift:
        """Open a new shift."""
        return self.shift_repository.create()

    def close_shift(self, shift_id: UUID, shift_update: ShiftUpdate) -> Shift:
        """Close an open shift."""
        now = datetime.now()
        return self.shift_repository.update_status(shift_id, shift_update, now)

    def get_shift(self, shift_id: UUID) -> Shift:
        """Get a shift by ID."""
        return self.shift_repository.get_by_id(shift_id)

