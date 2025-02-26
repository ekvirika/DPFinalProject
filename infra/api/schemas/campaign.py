from typing import Any, Dict, List, Optional, Union
from uuid import UUID
from wsgiref.validate import validator

from pydantic import BaseModel

from core.models.campaign import CampaignType


class DiscountRuleModel(BaseModel):
    discount_value: float
    applies_to: str
    product_ids: Optional[List[str]] = None
    min_amount: Optional[float] = None



class BuyNGetNRuleModel(BaseModel):
    buy_product_id: UUID
    buy_quantity: int
    get_product_id: str
    get_quantity: int



class ComboRuleModel(BaseModel):
    product_ids: List[str]
    discount_type: str
    discount_value: float



class CampaignCreate(BaseModel):
    name: str
    campaign_type: str
    rules: Union[Dict[str, Any], DiscountRuleModel, BuyNGetNRuleModel, ComboRuleModel]



class CampaignResponse(BaseModel):
    id: UUID
    name: str
    campaign_type: str
    rules: Dict[str, Any]

    class Config:
        orm_mode = True


class CampaignsResponse(BaseModel):
    campaigns: List[CampaignResponse]
