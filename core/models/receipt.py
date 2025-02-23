from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List
from uuid import UUID

from pydantic.v1 import UUID1


class PaymentCurrency(str, Enum):
    GEL = "GEL"
    USD = "USD"
    EUR = "EUR"


class ReceiptStatus(str, Enum):
    OPEN = "OPEN"
    PENDING_PAYMENT = "PENDING_PAYMENT"
    PAID = "PAID"
    CANCELLED = "CANCELLED"

@dataclass
class ReceiptItem:
    product_id: UUID
    quantity: int
    unit_price: float
    discount: Optional[float] = None
    campaign_id: Optional[int] = None

@dataclass
class Payment:
    amount: float
    currency: PaymentCurrency
    exchange_rate: float
    timestamp: datetime

@dataclass
class Receipt:
    id: UUID
    shift_id: UUID
    items: List[ReceiptItem]
    status: ReceiptStatus
    created_at: datetime
    total_amount: float
    discount_amount: Optional[float] = None
    payments: List[Payment] = None