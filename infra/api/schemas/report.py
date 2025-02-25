from typing import List, Dict

from pydantic import BaseModel

from infra.api.schemas.receipt import ItemSoldResponse, RevenueByCurrencyResponse


class XReportResponse(BaseModel):
    shift_id: str
    receipt_count: int
    items_sold: List[ItemSoldResponse]
    revenue_by_currency: List[RevenueByCurrencyResponse]


class SalesReportResponse(BaseModel):
    total_items_sold: int
    total_receipts: int
    total_revenue: Dict[str, float]
    total_revenue_gel: float