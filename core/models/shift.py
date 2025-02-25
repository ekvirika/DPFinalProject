# core/schemas/shift.py
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID


class ShiftStatus(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


@dataclass(frozen=True)
class Shift:
    id: UUID
    cashier_id: str
    start_time: datetime
    status: ShiftStatus
    end_time: Optional[datetime] = None
    created_at: Optional[datetime] = None


@dataclass(frozen=True)
class ShiftReport:
    """Report model for shift statistics."""
    total_receipts: int
    items_sold: dict[UUID, int]  # product_id -> quantity
    revenue_by_currency: dict[str, float]  # currency_code -> amount