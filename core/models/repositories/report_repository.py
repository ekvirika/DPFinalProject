from asyncio import Protocol
from typing import Optional
from uuid import UUID

from core.models.report import SalesReport, ShiftReport


class ReportRepository(Protocol):
    def generate_shift_report(self, shift_id: UUID) -> Optional[ShiftReport]:
        ...

    def generate_sales_report(self) -> SalesReport:
        ...