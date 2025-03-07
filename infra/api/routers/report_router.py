from typing import Dict
from uuid import UUID

from fastapi import APIRouter, Depends

from core.models.report import SalesReport, ShiftReport
from core.services.report_service import ReportService
from infra.api.schemas.report import SalesReportResponse, XReportResponse
from runner.dependencies import get_report_service

router = APIRouter()


@router.get("/x-reports")
def get_x_report(
    shift_id: UUID,
    report_service: ReportService = Depends(get_report_service),
) -> dict[str, ShiftReport]:
    report = report_service.generate_shift_report(shift_id)
    print(report)
    return {"x-report": report}


@router.patch("/z-report/{shift_id}", response_model=Dict[str, XReportResponse])
def get_z_report(
    shift_id: UUID,
    report_service: ReportService = Depends(get_report_service),
) -> dict[str, ShiftReport]:
    report = report_service.generate_z_report(shift_id)
    return {"z_report": report}


@router.get("/sales", response_model=Dict[str, SalesReportResponse])
def get_sales_report(
    report_service: ReportService = Depends(get_report_service),
) -> dict[str, SalesReport]:
    report = report_service.generate_sales_report()
    return {"sales": report}
