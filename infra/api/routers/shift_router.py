from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from core.services.shift_service import ShiftService
from infra.api.schemas.shift import (
    ShiftCreate,
    ShiftListResponse,
    ShiftReportResponse,
    ShiftResponse,
)
from runner.dependencies import get_shift_service

router = APIRouter(prefix="/shifts", tags=["Shifts"])


@router.post("", response_model=ShiftResponse, status_code=201)
def open_shift(shift_data: ShiftCreate, service: ShiftService = Depends(get_shift_service)):
    """Open a new shift for a cashier."""
    try:
        shift = service.open_shift(shift_data.cashier_id)
        return ShiftResponse(
            id=shift.id,
            cashier_id=shift.cashier_id,
            start_time=shift.start_time,
            status=shift.status.value,
            end_time=shift.end_time,
            created_at=shift.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{shift_id}", response_model=ShiftResponse)
def get_shift(shift_id: UUID, service: ShiftService = Depends(get_shift_service)):
    """Get a shift by ID."""
    try:
        shift = service.get_shift(shift_id)
        return ShiftResponse(
            id=shift.id,
            cashier_id=shift.cashier_id,
            start_time=shift.start_time,
            status=shift.status.value,
            end_time=shift.end_time,
            created_at=shift.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("", response_model=ShiftListResponse)
def get_shifts(service: ShiftService = Depends(get_shift_service)):
    """Get all shifts."""
    shifts = service.get_all_shifts()
    return ShiftListResponse(
        shifts=[
            ShiftResponse(
                id=shift.id,
                cashier_id=shift.cashier_id,
                start_time=shift.start_time,
                status=shift.status.value,
                end_time=shift.end_time,
                created_at=shift.created_at,
            )
            for shift in shifts
        ]
    )


@router.patch("/{shift_id}/close", response_model=ShiftResponse)
def close_shift(shift_id: UUID, service: ShiftService = Depends(get_shift_service)):
    """Close an open shift."""
    try:
        shift = service.close_shift(shift_id)
        return ShiftResponse(
            id=shift.id,
            cashier_id=shift.cashier_id,
            start_time=shift.start_time,
            status=shift.status.value,
            end_time=shift.end_time,
            created_at=shift.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{shift_id}/x-report", response_model=ShiftReportResponse)
def get_x_report(shift_id: UUID, service: ShiftService = Depends(get_shift_service)):
    """Get an X report for a shift."""
    try:
        report = service.get_x_report(shift_id)
        return ShiftReportResponse(
            total_receipts=report.total_receipts,
            items_sold={str(k): v for k, v in report.items_sold.items()},
            revenue_by_currency=report.revenue_by_currency,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{shift_id}/z-report", response_model=ShiftReportResponse)
def get_z_report(shift_id: UUID, service: ShiftService = Depends(get_shift_service)):
    """Get a Z report and close the shift."""
    try:
        report = service.get_z_report(shift_id)
        return ShiftReportResponse(
            total_receipts=report.total_receipts,
            items_sold={str(k): v for k, v in report.items_sold.items()},
            revenue_by_currency=report.revenue_by_currency,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))