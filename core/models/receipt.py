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
    campaign_id: uuid.UUID
    campaign_name: str
    discount_amount: float


@dataclass
class ReceiptItem:
    product_id: uuid.UUID
    quantity: int
    unit_price: float
    total_price: float = field(init=False)
    discounts: List[Discount] = field(default_factory=list)
    final_price: float = field(init=False)

    def __post_init__(self) -> None:
        self.total_price = self.unit_price * self.quantity
        self.final_price = self.total_price - sum(
            d.discount_amount for d in self.discounts
        )


@dataclass(frozen=True)
class Payment:
    """Represents a payment in the system."""

    receipt_id: uuid.UUID
    payment_amount: float
    currency: Currency
    total_in_gel: float
    exchange_rate: float
    status: PaymentStatus = PaymentStatus.PENDING
    id: uuid.UUID = field(default_factory=uuid.uuid4)

    def update_status(self, new_status: PaymentStatus) -> "Payment":
        """Create a new Payment object with an updated status."""
        return Payment(
            receipt_id=self.receipt_id,
            payment_amount=self.payment_amount,
            currency=self.currency,
            total_in_gel=self.total_in_gel,
            exchange_rate=self.exchange_rate,
            status=new_status,
            id=self.id,
        )


@dataclass
class Receipt:
    shift_id: uuid.UUID
    id: uuid.UUID = field(default_factory=lambda: uuid.uuid4())
    status: ReceiptStatus = ReceiptStatus.OPEN
    products: List[ReceiptItem] = field(default_factory=list)
    payments: List[Payment] = field(default_factory=list)
    discounts: List[Discount] = field(default_factory=list)
    subtotal: float = 0
    discount_amount: float = 0
    total: float = 0

    def recalculate_totals(self) -> None:
        self.subtotal = sum(item.total_price for item in self.products)
        self.discount_amount = sum(
            sum(d.discount_amount for d in item.discounts) for item in self.products
        ) + sum(m.discount_amount for m in self.discounts)
        self.total = self.subtotal - self.discount_amount


@dataclass
class ItemSold:
    product_id: uuid.UUID
    quantity: int


@dataclass
class RevenueByCurrency:
    currency: Currency
    amount: float


@dataclass
class Quote:
    receipt_id: uuid.UUID
    base_currency: Currency
    requested_currency: Currency
    exchange_rate: float
    total_in_base_currency: float
    total_in_requested_currency: float
