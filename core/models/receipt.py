from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID


class PaymentCurrency(str, Enum):
    GEL = "GEL"
    USD = "USD"
    EUR = "EUR"


class ReceiptStatus(str, Enum):
    OPEN = "OPEN"
    PENDING_PAYMENT = "PENDING_PAYMENT"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True)
class ReceiptItem:
    product_id: UUID
    quantity: int
    unit_price: float
    discount: Optional[float] = None
    campaign_id: Optional[int] = None


@dataclass(frozen=True)
class Payment:
    amount: float
    currency: PaymentCurrency
    exchange_rate: float
    timestamp: datetime


@dataclass(frozen=True)
class Receipt:
    id: UUID
    shift_id: UUID
    items: List[ReceiptItem]
    status: ReceiptStatus
    created_at: datetime
    total_amount: float
    discount_amount: Optional[float] = None
    payments: List[Payment] = field(default_factory=list)
