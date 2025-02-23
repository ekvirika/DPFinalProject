from fastapi import HTTPException, status


class POSException(HTTPException):
    def __init__(self, status_code: int, detail: str, error_code: str):
        super().__init__(status_code=status_code, detail={"error_code": error_code, "message": detail})


# 🧾 Receipt Errors
class ReceiptNotFoundError(POSException):
    def __init__(self, receipt_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Receipt with ID {receipt_id} not found.",
            error_code="RECEIPT_NOT_FOUND"
        )


class ReceiptStatusError(POSException):
    def __init__(self, status: str, action: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot {action} receipt in {status} status.",
            error_code="INVALID_RECEIPT_STATUS"
        )


class InsufficientPaymentError(POSException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment amount is insufficient.",
            error_code="INSUFFICIENT_PAYMENT"
        )


# 🛍️ Product Errors
class ProductNotFoundError(POSException):
    def __init__(self, product_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found.",
            error_code="PRODUCT_NOT_FOUND"
        )


# 💱 Exchange Rate Errors
class ExchangeRateNotFoundError(POSException):
    def __init__(self, from_currency: str, to_currency: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exchange rate from {from_currency} to {to_currency} not found.",
            error_code="EXCHANGE_RATE_NOT_FOUND"
        )
