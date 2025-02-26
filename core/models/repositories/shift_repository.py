from datetime import datetime
from typing import Optional, Protocol
from uuid import UUID

from core.models.shift import Shift, ShiftStatus


class ShiftRepository(Protocol):
    def create(self) -> Shift: ...

    def get_by_id(self, shift_id: UUID) -> Optional[Shift]: ...

    def update_status(
        self, shift_id: UUID, status: ShiftStatus, closed_at: Optional[datetime] = None
    ) -> Optional[Shift]: ...

    def get_current_open(self) -> Optional[Shift]: ...


