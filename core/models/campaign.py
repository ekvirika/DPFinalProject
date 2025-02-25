import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, List, Union
from uuid import UUID

from pydantic import BaseModel, Field


class CampaignType(Enum):
    DISCOUNT = "discount"
    BUY_N_GET_N = "buy_n_get_n"
    COMBO = "combo"


@dataclass
class Discount:
    campaign_id: str
    campaign_name: str
    discount_amount: float


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


@dataclass
class Campaign:
    name: str
    campaign_type: CampaignType
    rules: Union[DiscountRule, BuyNGetNRule, ComboRule]
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    is_active: bool = True
