from datetime import datetime
from typing import Protocol, Optional

from core.models.shift import Shift, ShiftStatus


class ShiftRepository(Protocol):
    def create(self) -> Shift:
        ...

    def get_by_id(self, shift_id: str) -> Optional[Shift]:
        ...

    def update_status(self, shift_id: str, status: ShiftStatus,
                      closed_at: Optional[datetime] = None) -> Optional[Shift]:
        ...

    def get_current_open(self) -> Optional[Shift]:
        ...