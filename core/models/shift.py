# core/schemas/shift.py
from dataclasses import dataclass, field
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
    status: ShiftStatus = ShiftStatus.OPEN
    created_at: datetime = field(default_factory=datetime.now)
    closed_at: Optional[datetime] = None
