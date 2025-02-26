from dataclasses import Field
from typing import List
from uuid import UUID
from wsgiref.validate import validator

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


class ReceiptResponse(BaseModel):
    id: UUID
    shift_id: UUID
    status: str
    products: List[ReceiptItemResponse] = []
    payments: List[PaymentResponse] = []
    subtotal: float
    discount_amount: float
    total: float

    class Config:
        orm_mode = True


class ProductAddRequest(BaseModel):
    product_id: UUID
    quantity: int = Field(..., gt=0)


class QuoteRequest(BaseModel):
    currency: Currency

    @validator("currency")
    def validate_currency(cls, v):
        if v not in [c.value for c in Currency]:
            raise ValueError(f"currency must be one of {[c.value for c in Currency]}")
        return v


class QuoteResponse(BaseModel):
    receipt_id: UUID
    base_currency: str
    requested_currency: str
    exchange_rate: float
    total_in_base_currency: float
    total_in_requested_currency: float


class PaymentRequest(BaseModel):
    amount: float
    currency: str

    @validator("amount")
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Amount must be greater than 0")
        return v

    @validator("currency")
    def validate_currency(cls, v):
        if v not in [c.value for c in Currency]:
            raise ValueError(f"currency must be one of {[c.value for c in Currency]}")
        return v


class PaymentCompleteResponse(BaseModel):
    payment: PaymentResponse
    receipt: ReceiptResponse


class ItemSoldResponse(BaseModel):
    product_id: UUID
    name: str
    quantity: int


class RevenueByCurrencyResponse(BaseModel):
    currency: str
    amount: float
