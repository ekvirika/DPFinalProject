from typing import Protocol
from uuid import UUID

from core.models.report import SalesReport, ShiftReport


class ReportRepository(Protocol):
    def generate_shift_report(self, shift_id: UUID) -> ShiftReport:
        pass

    def generate_z_report(self, shift_id: UUID) -> ShiftReport:
        pass

    def generate_sales_report(self) -> SalesReport:
        pass
