from typing import Any, Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from core.models.receipt import Currency, Receipt
from core.services.receipt_service import ReceiptService
from infra.api.schemas.receipt import (
    PaymentCompleteResponse,
    PaymentRequest,
    PaymentResponse,
    ProductAddRequest,
    QuoteRequest,
    QuoteResponse,
    ReceiptCreate,
    ReceiptPaymentResponse,
    ReceiptResponse,
)
from runner.dependencies import get_receipt_service

router = APIRouter()


@router.post(
    "/", response_model=Dict[str, ReceiptResponse], status_code=status.HTTP_201_CREATED
)
def create_receipt(
    receipt_data: ReceiptCreate,
    receipt_service: ReceiptService = Depends(get_receipt_service),
) -> dict[str, Receipt]:
    new_receipt = receipt_service.create_receipt(receipt_data.shift_id)
    if not new_receipt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot create receipt. Shift with ID '{receipt_data.shift_id}' not found or closed",
        )
    return {"receipt": new_receipt}


@router.post("/{receipt_id}/products", response_model=Dict[str, ReceiptResponse])
def add_product_to_receipt(
    receipt_id: UUID,
    product_data: ProductAddRequest,
    receipt_service: ReceiptService = Depends(get_receipt_service),
) -> dict[str, Receipt]:
    updated_receipt = receipt_service.add_product(
        receipt_id, product_data.product_id, product_data.quantity
    )
    print(f"Updated receipt: {updated_receipt}")  # Check if products are being added
    if not updated_receipt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot add product. Receipt not found, closed, or product not found",
        )
    return {"receipt": updated_receipt}


@router.post("/receipts/{receipt_id}/quotes", response_model=Dict[str, QuoteResponse])
def calculate_payment_quote(
    receipt_id: UUID,
    quote_data: QuoteRequest,
    receipt_service: ReceiptService = Depends(get_receipt_service),
) -> Dict[str, QuoteResponse]:
    try:
        quote = receipt_service.calculate_payment_quote(
            receipt_id, Currency(quote_data.currency)
        )
        if not quote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Receipt with ID '{receipt_id}' not found",
            )
        return {
            "quote": QuoteResponse(
                receipt_id=receipt_id,
                base_currency=quote.base_currency,
                requested_currency=quote.requested_currency,
                exchange_rate=quote.exchange_rate,
                total_in_base_currency=quote.total_in_base_currency,
                total_in_requested_currency=quote.total_in_requested_currency,
            )
        }
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported currency. Supported currencies are: {[c.value for c in Currency]}",
        )


@router.post("/{receipt_id}/payments", response_model=PaymentCompleteResponse)
def add_payment(
    receipt_id: UUID,
    payment_data: PaymentRequest,
    receipt_service: ReceiptService = Depends(get_receipt_service),
) -> PaymentCompleteResponse:
    try:
        result = receipt_service.add_payment(
            receipt_id, payment_data.amount, payment_data.currency
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot add payment. Receipt with ID '{receipt_id}' not found or closed",
            )

        payment, updated_receipt = result

        # Convert Receipt to ReceiptResponse
        receipt_response = ReceiptPaymentResponse(
            id=updated_receipt.id,
            status=updated_receipt.status.value,
        )

        return PaymentCompleteResponse(
            payment=PaymentResponse(
                id=payment.id,
                payment_amount=payment.payment_amount,
                currency=payment.currency.value,
                total_in_gel=payment.total_in_gel,
                exchange_rate=payment.exchange_rate,
                status=payment.status.value,
            ),
            receipt=receipt_response,
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported currency. Supported currencies are: {[c.value for c in Currency]}",
        )


@router.get("/{receipt_id}", response_model=Dict[str, ReceiptResponse])
def get_receipt(
    receipt_id: UUID, receipt_service: ReceiptService = Depends(get_receipt_service)
) -> dict[str, Any]:
    receipt = receipt_service.get_receipt(receipt_id)
    if not receipt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Receipt with ID '{receipt_id}' not found",
        )
    return {"receipt": receipt}
