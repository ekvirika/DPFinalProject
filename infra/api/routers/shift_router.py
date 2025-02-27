# Shifts
from typing import Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from core.models.shift import Shift, ShiftStatus
from core.services.shift_service import ShiftService  # Import the service
from infra.api.schemas.shift import ShiftResponse, ShiftUpdate
from runner.dependencies import get_shift_service

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
def open_shift(
    shift_service: ShiftService = Depends(get_shift_service),
) -> dict[str, Shift]:
    new_shift = shift_service.open_shift()
    return {"shift": new_shift}


@router.patch("/{shift_id}", response_model=Dict[str, ShiftResponse])
def close_shift(
    shift_id: UUID,
    shift_update: ShiftUpdate,
    shift_service: ShiftService = Depends(get_shift_service),  # Injecting service
) -> dict[str, Shift]:
    updated_shift = shift_service.close_shift(shift_id, shift_update)
    return {"shift": updated_shift}
