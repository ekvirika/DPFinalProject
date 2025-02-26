from typing import Optional
from uuid import UUID

from core.models.report import ShiftReport, SalesReport
from core.models.repositories.report_repository import ReportRepository
from core.models.repositories.shift_repository import ShiftRepository


class ReportService:
    def __init__(self, report_repository: ReportRepository, shift_repository: ShiftRepository):
        self.report_repository = report_repository
        self.shift_repository = shift_repository

    def generate_x_report(self, shift_id: UUID) -> Optional[ShiftReport]:
        """Generate an X report for a shift."""
        shift = self.shift_repository.get_by_id(shift_id)
        if not shift:
            return None

        return self.report_repository.generate_shift_report(shift_id)

    def generate_sales_report(self) -> SalesReport:
        """Generate a lifetime sales report."""
        return self.report_repository.generate_sales_report()