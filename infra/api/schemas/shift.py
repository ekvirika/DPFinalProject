from datetime import datetime
from typing import Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ShiftCreate(BaseModel):
    cashier_id: str = Field(..., min_length=1)


class ShiftResponse(BaseModel):
    id: UUID
    cashier_id: str
    start_time: datetime
    status: str
    end_time: Optional[datetime] = None
    created_at: datetime


class ShiftReportResponse(BaseModel):
    total_receipts: int
    items_sold: Dict[str, int]  # product_id -> quantity
    revenue_by_currency: Dict[str, float]  # currency_code -> amount


class ShiftListResponse(BaseModel):
    shifts: list[ShiftResponse]