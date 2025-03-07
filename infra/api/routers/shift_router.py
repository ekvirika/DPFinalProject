# Shifts

from fastapi import APIRouter, Depends
from starlette import status

from core.models.shift import Shift
from core.services.shift_service import ShiftService  # Import the service
from runner.dependencies import get_shift_service

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
def open_shift(
    shift_service: ShiftService = Depends(get_shift_service),
) -> dict[str, Shift]:
    new_shift = shift_service.open_shift()
    return {"shift": new_shift}
