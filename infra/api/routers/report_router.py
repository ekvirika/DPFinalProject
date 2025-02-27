from typing import Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from core.models.report import SalesReport, ShiftReport
from core.services.report_service import ReportService
from core.services.shift_service import ShiftService
from infra.api.schemas.report import SalesReportResponse, XReportResponse
from runner.dependencies import get_report_service, get_shift_service

router = APIRouter()


@router.get("/x-reports", response_model=Dict[str, XReportResponse])
def get_x_report(
    shift_id: UUID,
        report_service: ReportService = Depends(get_report_service),
        shift_service: ShiftService = Depends(get_shift_service)
) -> dict[str, ShiftReport]:
    report = report_service.generate_x_report(shift_id, shift_service)
    return {"x-report": report}


@router.get("/sales", response_model=Dict[str, SalesReportResponse])
def get_sales_report(
    report_service: ReportService = Depends(get_report_service),
) -> dict[str, SalesReport]:
    report = report_service.generate_sales_report()
    return {"sales": report}
