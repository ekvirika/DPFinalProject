from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from core.models.receipt import Currency
from core.models.repositories.receipt_repository import ReceiptStatus
from core.services.receipt_service import ReceiptService
from runner.dependencies import get_receipt_service


# --- Request Models ---
class CreateReceiptRequest(BaseModel):
    shift_id: UUID


class AddItemRequest(BaseModel):
    product_id: UUID
    quantity: int = Field(..., gt=0)


class PaymentQuoteRequest(BaseModel):
    currency: Currency


class PaymentRequest(BaseModel):
    amount: float = Field(..., gt=0)
    currency: Currency


# --- Response Models ---
class ReceiptItemResponse(BaseModel):
    product_id: UUID
    quantity: int
    unit_price: float
    discount: Optional[float] = None
    campaign_id: Optional[int] = None


class PaymentResponse(BaseModel):
    amount: float
    currency: Currency
    exchange_rate: float
    timestamp: datetime


class ReceiptResponse(BaseModel):
    id: UUID
    shift_id: UUID
    items: List[ReceiptItemResponse]
    status: ReceiptStatus
    created_at: datetime
    total_amount: float
    discount_amount: Optional[float] = None
    payments: Optional[List[PaymentResponse]] = None


class PaymentQuoteResponse(BaseModel):
    amount: float
    currency: Currency


# --- Router Initialization ---
router = APIRouter()


# --- Endpoints ---
@router.post("", status_code=status.HTTP_201_CREATED)
def create_receipt(
    request: CreateReceiptRequest,
    service: ReceiptService = Depends(get_receipt_service),
) -> dict[str, ReceiptResponse]:
    receipt = service.create_receipt(request.shift_id)
    return {"receipt": ReceiptResponse.from_orm(receipt)}


@router.post("/{receipt_id}/products")
def add_item(
    receipt_id: UUID,
    request: AddItemRequest,
    service: ReceiptService = Depends(get_receipt_service),
) -> dict[str, ReceiptResponse]:
    receipt = service.add_item(receipt_id, request.product_id, request.quantity)
    return {"receipt": ReceiptResponse.from_orm(receipt)}


@router.post("/{receipt_id}/quotes")
def calculate_payment(
    receipt_id: UUID,
    request: PaymentQuoteRequest,
    service: ReceiptService = Depends(get_receipt_service),
) -> dict[str, PaymentQuoteResponse]:
    amount = service.calculate_payment(receipt_id, request.currency)
    return {"quote": PaymentQuoteResponse(amount=amount, currency=request.currency)}


@router.post("/{receipt_id}/payments")
def add_payment(
    receipt_id: UUID,
    request: PaymentRequest,
    service: ReceiptService = Depends(get_receipt_service),
) -> dict[str, ReceiptResponse]:
    receipt = service.add_payment(receipt_id, request.amount, request.currency)
    return {"receipt": ReceiptResponse.from_orm(receipt)}


@router.post("/{receipt_id}/close")
def close_receipt(
    receipt_id: UUID, service: ReceiptService = Depends(get_receipt_service)
) -> dict[str, ReceiptResponse]:
    receipt = service.close_receipt(receipt_id)
    return {"receipt": ReceiptResponse.from_orm(receipt)}


@router.get("")
def get_shift_receipts(
    shift_id: UUID, service: ReceiptService = Depends(get_receipt_service)
) -> dict[str, List[ReceiptResponse]]:
    receipts = service.get_shift_receipts(shift_id)
    return {"receipts": [ReceiptResponse.from_orm(receipt) for receipt in receipts]}
