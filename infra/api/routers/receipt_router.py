from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse



from core.models.receipt import PaymentCurrency, ReceiptStatus
from core.services.receipt_service import ReceiptService


class CreateReceiptRequest(BaseModel):
    shift_id: int = Field(..., description="ID of the shift")

class AddItemRequest(BaseModel):
    product_id: int = Field(..., description="ID of the product to add")
    quantity: int = Field(..., gt=0, description="Quantity of the product")

class PaymentQuoteRequest(BaseModel):
    currency: PaymentCurrency = Field(..., description="Currency for payment calculation")

class PaymentRequest(BaseModel):
    amount: float = Field(..., gt=0, description="Payment amount")
    currency: PaymentCurrency = Field(..., description="Payment currency")

class ReceiptItemResponse(BaseModel):
    product_id: int
    quantity: int
    unit_price: float
    discount: Optional[float] = None
    campaign_id: Optional[int] = None

class PaymentResponse(BaseModel):
    amount: float
    currency: PaymentCurrency
    exchange_rate: float
    timestamp: datetime

class ReceiptResponse(BaseModel):
    id: int
    shift_id: int
    items: List[ReceiptItemResponse]
    status: ReceiptStatus
    created_at: datetime
    total_amount: float
    discount_amount: Optional[float] = None
    payments: Optional[List[PaymentResponse]] = None

class PaymentQuoteResponse(BaseModel):
    amount: float
    currency: PaymentCurrency


class ReceiptRouter:
    def __init__(self, receipt_service: ReceiptService):
        self.receipt_service = receipt_service
        self.router = APIRouter(prefix="/receipts", tags=["receipts"])
        self._init_routes()

    def _init_routes(self):
        @self.router.post(
            "",
            response_model=ReceiptResponse,
            status_code=status.HTTP_201_CREATED,
            summary="Create a new receipt"
        )
        def create_receipt(request: CreateReceiptRequest):
            try:
                receipt = self.receipt_service.create_receipt(request.shift_id)
                return ReceiptResponse.from_orm(receipt)
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )

        @self.router.post(
            "/{receipt_id}/products",
            response_model=ReceiptResponse,
            summary="Add item to receipt"
        )
        def add_item(receipt_id: int, request: AddItemRequest):
            try:
                receipt = self.receipt_service.add_item(
                    receipt_id=receipt_id,
                    product_id=request.product_id,
                    quantity=request.quantity
                )
                return ReceiptResponse.from_orm(receipt)
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )

        @self.router.post(
            "/{receipt_id}/quotes",
            response_model=PaymentQuoteResponse,
            summary="Calculate payment amount in specified currency"
        )
        def calculate_payment(receipt_id: int, request: PaymentQuoteRequest):
            try:
                amount = self.receipt_service.calculate_payment(
                    receipt_id=receipt_id,
                    currency=request.currency
                )
                return PaymentQuoteResponse(
                    amount=amount,
                    currency=request.currency
                )
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )

        @self.router.post(
            "/{receipt_id}/payments",
            response_model=ReceiptResponse,
            summary="Add payment to receipt"
        )
        def add_payment(receipt_id: int, request: PaymentRequest):
            try:
                receipt = self.receipt_service.add_payment(
                    receipt_id=receipt_id,
                    amount=request.amount,
                    currency=request.currency
                )
                return ReceiptResponse.from_orm(receipt)
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )

        @self.router.post(
            "/{receipt_id}/close",
            response_model=ReceiptResponse,
            summary="Close receipt"
        )
        def close_receipt(receipt_id: int):
            try:
                receipt = self.receipt_service.close_receipt(receipt_id)
                return ReceiptResponse.from_orm(receipt)
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )

        @self.router.get(
            "",
            response_model=List[ReceiptResponse],
            summary="Get receipts by shift"
        )
        def get_shift_receipts(shift_id: int):
            receipts = self.receipt_service.get_shift_receipts(shift_id)
            return [ReceiptResponse.from_orm(receipt) for receipt in receipts]
