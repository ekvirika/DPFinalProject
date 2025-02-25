import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import List


class ReceiptStatus(Enum):
    OPEN = "open"
    CLOSED = "closed"


class Currency(Enum):
    GEL = "GEL"
    USD = "USD"
    EUR = "EUR"


class PaymentStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class Discount:
    campaign_id: str
    campaign_name: str
    discount_amount: float


@dataclass
class ReceiptItem:
    product_id: str
    quantity: int
    unit_price: float
    total_price: float = field(init=False)
    discounts: List[Discount] = field(default_factory=list)
    final_price: float = field(init=False)

    def __post_init__(self) -> None:
        self.total_price = self.unit_price * self.quantity
        self.final_price = self.total_price - sum(d.discount_amount for d in self.discounts)


@dataclass
class Payment:
    receipt_id: str
    payment_amount: float
    currency: Currency
    total_in_gel: float
    exchange_rate: float
    status: PaymentStatus = PaymentStatus.PENDING
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class Receipt:
    shift_id: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: ReceiptStatus = ReceiptStatus.OPEN
    products: List[ReceiptItem] = field(default_factory=list)
    payments: List[Payment] = field(default_factory=list)
    subtotal: float = 0
    discount_amount: float = 0
    total: float = 0

    def recalculate_totals(self) -> None:
        self.subtotal = sum(item.total_price for item in self.products)
        self.discount_amount = sum(sum(d.discount_amount for d in item.discounts) for item in self.products)
        self.total = self.subtotal - self.discount_amount


@dataclass
class ItemSold:
    product_id: str
    name: str
    quantity: int


@dataclass
class RevenueByCurrency:
    currency: Currency
    amount: float

@dataclass
class Quote:
    receipt_id: str
    base_currency: Currency
    requested_currency: Currency
    exchange_rate: float
    total_in_base_currency: float
    total_in_requested_currency: float