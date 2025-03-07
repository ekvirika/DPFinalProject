from datetime import datetime
from typing import Optional
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

    def get_shift(self, shift_id: UUID) -> Shift:
        """Get a shift by ID."""
        return self.shift_repository.get_by_id(shift_id)

    def update_shift_status(
        self, shift_id: UUID, status: ShiftUpdate, closed_at: Optional[datetime] = None
    ) -> Shift:
        return self.shift_repository.update_status(shift_id, status, closed_at)
