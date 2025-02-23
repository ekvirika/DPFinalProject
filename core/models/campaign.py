from enum import Enum
from pydantic import BaseModel
from typing import Optional

class CampaignType(str, Enum):
    BUY_N_GET_N = "buy_n_get_n"
    DISCOUNT = "discount"
    COMBO = "combo"

class Campaign(BaseModel):
    id: int
    name: str
    type: CampaignType
    details: dict
    is_active: bool = True