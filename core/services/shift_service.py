from uuid import UUID

from core.models.repositories.shift_repository import ShiftRepository
from core.models.shift import Shift, ShiftReport, ShiftStatus


class ShiftService:
    def __init__(self, shift_repository: ShiftRepository):
        self.shift_repository = shift_repository

    def open_shift(self, cashier_id: str) -> Shift:
        """Open a new shift for a cashier."""
        # Check if cashier already has an open shift
        existing_shift = self.shift_repository.get_open_shift_by_cashier(cashier_id)
        if existing_shift:
            raise ValueError(f"Cashier {cashier_id} already has an open shift")

        return self.shift_repository.create(cashier_id)

    def close_shift(self, shift_id: UUID) -> Shift:
        """Close an open shift."""
        shift = self.shift_repository.get_by_id(shift_id)
        if not shift:
            raise ValueError(f"Shift with ID {shift_id} not found")

        if shift.status == ShiftStatus.CLOSED:
            raise ValueError(f"Shift {shift_id} is already closed")

        closed_shift = self.shift_repository.close(shift_id)
        if not closed_shift:
            raise ValueError(f"Failed to close shift {shift_id}")

        return closed_shift

    def get_shift(self, shift_id: UUID) -> Shift:
        """Get a shift by ID."""
        shift = self.shift_repository.get_by_id(shift_id)
        if not shift:
            raise ValueError(f"Shift with ID {shift_id} not found")

        return shift

    def get_all_shifts(self) -> list[Shift]:
        """Get all shifts."""
        return self.shift_repository.get_all()

    def get_x_report(self, shift_id: UUID) -> ShiftReport:
        """
        Get an X report for the current state of the shift.
        X report is a snapshot of the current shift without closing it.
        """
        shift = self.shift_repository.get_by_id(shift_id)
        if not shift:
            raise ValueError(f"Shift with ID {shift_id} not found")

        if shift.status == ShiftStatus.CLOSED:
            raise ValueError(f"Cannot generate X report for closed shift {shift_id}")

        report = self.shift_repository.get_x_report(shift_id)
        if not report:
            raise ValueError(f"Could not generate X report for shift {shift_id}")

        return report

    def get_z_report(self, shift_id: UUID) -> ShiftReport:
        """
        Get a Z report and close the shift.
        Z report is the final report of the shift that closes it.
        """
        shift = self.shift_repository.get_by_id(shift_id)
        if not shift:
            raise ValueError(f"Shift with ID {shift_id} not found")

        if shift.status == ShiftStatus.CLOSED:
            raise ValueError(f"Cannot generate Z report for closed shift {shift_id}")

        report = self.shift_repository.get_z_report(shift_id)
        if not report:
            raise ValueError(f"Could not generate Z report for shift {shift_id}")

        return report