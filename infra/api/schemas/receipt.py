from typing import List
from uuid import UUID

from pydantic import BaseModel

from core.models.receipt import Currency


class ReceiptCreate(BaseModel):
    shift_id: UUID


class DiscountResponse(BaseModel):
    campaign_id: UUID
    campaign_name: str
    discount_amount: float


class ReceiptItemResponse(BaseModel):
    product_id: UUID
    quantity: int
    unit_price: float
    total_price: float
    discounts: List[DiscountResponse] = []
    final_price: float


class PaymentResponse(BaseModel):
    id: UUID
    payment_amount: float
    currency: str
    total_in_gel: float
    exchange_rate: float
    status: str
    # total_in_requested_currency: float = field(init=False)
    # change : float = field(init=False)
    #
    # def __post_init__(self) -> None:
    #     self.total_in_requested_currency = self.total_in_gel * self.exchange_rate
    #     self.change = self.payment_amount - self.total_in_requested_currency


class ReceiptResponse(BaseModel):
    id: UUID
    shift_id: UUID
    status: str
    products: List[ReceiptItemResponse] = []
    payments: List[PaymentResponse] = []
    discounts: List[DiscountResponse] = []
    subtotal: float
    discount_amount: float
    total: float

    class Config:
        orm_mode = True


class ReceiptPaymentResponse(BaseModel):
    id: UUID
    status: str


class ProductAddRequest(BaseModel):
    product_id: UUID
    quantity: int


class QuoteRequest(BaseModel):
    currency: Currency


class QuoteResponse(BaseModel):
    receipt_id: UUID
    base_currency: Currency
    requested_currency: Currency
    exchange_rate: float
    total_in_base_currency: float
    total_in_requested_currency: float


class PaymentRequest(BaseModel):
    amount: float
    currency: str


class PaymentCompleteResponse(BaseModel):
    payment: PaymentResponse
    receipt: ReceiptPaymentResponse


class ItemSoldResponse(BaseModel):
    product_id: UUID
    quantity: int


class RevenueByCurrencyResponse(BaseModel):
    currency: str
    amount: float
