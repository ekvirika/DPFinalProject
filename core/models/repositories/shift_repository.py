from datetime import datetime
from typing import Optional, Protocol
from uuid import UUID

from core.models.shift import Shift, ShiftStatus
from infra.api.schemas.shift import ShiftUpdate


class ShiftRepository(Protocol):
    def create(self) -> Shift: ...

    def get_by_id(self, shift_id: UUID) -> Shift: ...

    def update_status(
        self, shift_id: UUID, status: ShiftUpdate, closed_at: Optional[datetime] = None
    ) -> Shift: ...

    def get_current_open(self) -> Optional[Shift]: ...
