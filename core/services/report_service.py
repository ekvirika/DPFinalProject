from typing import Optional
from uuid import UUID

from core.models.report import SalesReport, ShiftReport
from core.models.repositories.report_repository import ReportRepository
from core.models.repositories.shift_repository import ShiftRepository
from core.models.errors import ShiftNotFoundError
from core.services.shift_service import ShiftService


class ReportService:
    def __init__(
        self, report_repository: ReportRepository, shift_repository: ShiftRepository
    ):
        self.report_repository = report_repository
        self.shift_repository = shift_repository

    def generate_x_report(self, shift_id: UUID, shift: ShiftService) -> Optional[ShiftReport]:
        """Generate an X report for a shift."""
        if shift.shift_repository.get_by_id(shift_id) is None:
            raise ShiftNotFoundError(str(shift_id))
        return self.report_repository.generate_shift_report(shift_id)

    def generate_sales_report(self) -> SalesReport:
        """Generate a lifetime sales report."""
        return self.report_repository.generate_sales_report()
