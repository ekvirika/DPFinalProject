from uuid import UUID
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator
from dataclasses import dataclass
from typing import Optional, Dict, Any

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

    @validator('end_date')
    def validate_dates(cls, end_date, values):
        if 'start_date' in values and end_date <= values['start_date']:
            raise ValueError('end_date must be after start_date')
        return end_date

class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[CampaignType] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    conditions: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

    @validator('end_date')
    def validate_dates(cls, end_date, values):
        if end_date and 'start_date' in values and values['start_date'] and end_date <= values['start_date']:
            raise ValueError('end_date must be after start_date')
        return end_date

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