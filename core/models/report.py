from dataclasses import dataclass
from typing import Dict, List
from uuid import UUID

from core.models.receipt import ItemSold, RevenueByCurrency


@dataclass
class ShiftReport:
    shift_id: UUID
    receipt_count: int
    items_sold: List[ItemSold]
    revenue_by_currency: List[RevenueByCurrency]


@dataclass
class SalesReport:
    total_items_sold: int
    total_receipts: int
    total_revenue: Dict[str, float]
    total_revenue_gel: float
