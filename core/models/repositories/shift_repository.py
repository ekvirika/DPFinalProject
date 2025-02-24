# core/repositories/shift_repository.py
from typing import List, Optional, Protocol
from uuid import UUID

from core.models.shift import Shift, ShiftReport


class ShiftRepository(Protocol):
    def create(self, cashier_id: str) -> Shift:
        """Create a new shift for a cashier."""
        pass

    def get_by_id(self, shift_id: UUID) -> Optional[Shift]:
        """Retrieve a shift by its ID."""
        pass

    def get_all(self) -> List[Shift]:
        """Retrieve all shifts."""
        pass

    def close(self, shift_id: UUID) -> Optional[Shift]:
        """Close an open shift."""
        pass

    def get_open_shift_by_cashier(self, cashier_id: str) -> Optional[Shift]:
        """Get open shift for a cashier if exists."""
        pass

    def get_x_report(self, shift_id: UUID) -> Optional[ShiftReport]:
        """Generate X report for a shift without closing it."""
        pass

    def get_z_report(self, shift_id: UUID) -> Optional[ShiftReport]:
        """Generate Z report and close the shift."""
        pass