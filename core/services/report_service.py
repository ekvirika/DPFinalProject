from uuid import UUID

from core.models.report import SalesReport, ShiftReport
from core.models.repositories.report_repository import ReportRepository


class ReportService:
    def __init__(self, report_repository: ReportRepository):
        self.report_repository = report_repository

    def generate_sales_report(self) -> SalesReport:
        return self.report_repository.generate_sales_report()

    def generate_shift_report(self, shift_id: UUID) -> ShiftReport:
        return self.report_repository.generate_shift_report(shift_id)

    def generate_z_report(self, shift_id: UUID) -> ShiftReport:
        return self.report_repository.generate_z_report(shift_id)
