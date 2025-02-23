from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CampaignType(Enum):
    BUY_N_GET_N = "buy_n_get_n"
    DISCOUNT = "discount"
    COMBO = "combo"


class CampaignCreate(BaseModel):
    name: str = Field(..., min_length=1)
    type: CampaignType
    start_date: datetime
    end_date: datetime
    conditions: Dict[str, Any]  # Store campaign-specific conditions as JSON
    is_active: bool = True


class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[CampaignType] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    conditions: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


@dataclass
class Campaign:
    id: UUID
    name: str
    type: CampaignType
    start_date: datetime
    end_date: datetime
    conditions: Dict[str, Any]
    is_active: bool
    created_at: datetime
