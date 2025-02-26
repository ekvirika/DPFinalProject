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

    @validator("applies_to")
    def validate_applies_to(cls, v):
        if v not in ["product", "receipt"]:
            raise ValueError("applies_to must be either 'product' or 'receipt'")
        return v


class BuyNGetNRuleModel(BaseModel):
    buy_product_id: UUID
    buy_quantity: int
    get_product_id: str
    get_quantity: int

    @validator("buy_quantity", "get_quantity")
    def quantity_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Quantity must be greater than 0")
        return v


class ComboRuleModel(BaseModel):
    product_ids: List[str]
    discount_type: str
    discount_value: float

    @validator("discount_type")
    def validate_discount_type(cls, v):
        if v not in ["percentage", "fixed"]:
            raise ValueError("discount_type must be either 'percentage' or 'fixed'")
        return v

    @validator("product_ids")
    def validate_product_ids(cls, v):
        if len(v) < 2:
            raise ValueError("At least 2 products are required for a combo campaign")
        return v


class CampaignCreate(BaseModel):
    name: str
    campaign_type: str
    rules: Union[Dict[str, Any], DiscountRuleModel, BuyNGetNRuleModel, ComboRuleModel]

    @validator("campaign_type")
    def validate_campaign_type(cls, v):
        if v not in [ct.value for ct in CampaignType]:
            raise ValueError(
                f"campaign_type must be one of {[ct.value for ct in CampaignType]}"
            )
        return v


class CampaignResponse(BaseModel):
    id: UUID
    name: str
    campaign_type: str
    rules: Dict[str, Any]

    class Config:
        orm_mode = True


class CampaignsResponse(BaseModel):
    campaigns: List[CampaignResponse]
