from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, List
from uuid import UUID

from pydantic import BaseModel, Field



class CampaignType(Enum):
    DISCOUNT = "discount"
    BUY_N_GET_N = "buy_n_get_n"
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

@dataclass
class DiscountRule:
    discount_value: float
    applies_to: str
    product_ids: List[str] = field(default_factory=list)
    min_amount: Optional[float] = None


@dataclass
class BuyNGetNRule:
    buy_product_id: str
    buy_quantity: int
    get_product_id: str
    get_quantity: int


@dataclass
class ComboRule:
    product_ids: List[str]
    discount_type: str
    discount_value: float
