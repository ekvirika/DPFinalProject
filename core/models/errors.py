from fastapi import HTTPException, status


# Base POS Exception
class POSException(HTTPException):
    def __init__(self, status_code: int, detail: str, error_code: str) -> None:
        super().__init__(
            status_code=status_code,
            detail={"error_code": error_code, "message": detail},
        )


class ReceiptNotFoundError(POSException):
    def __init__(self, receipt_id: str) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Receipt with ID '{receipt_id}' not found.",
            error_code="RECEIPT_NOT_FOUND",
        )


class ReceiptStatusError(POSException):
    def __init__(self, receipt_status: str, action: str) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot {action} receipt in '{receipt_status}' status.",
            error_code="INVALID_RECEIPT_STATUS",
        )


class InsufficientPaymentError(POSException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment amount is insufficient.",
            error_code="INSUFFICIENT_PAYMENT",
        )


class ProductNotFoundError(POSException):
    def __init__(self, product_id: str) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID '{product_id}' not found.",
            error_code="PRODUCT_NOT_FOUND",
        )


class ExchangeRateNotFoundError(POSException):
    def __init__(self, from_currency: str, to_currency: str) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exchange rate from '{from_currency}'"
            f" to '{to_currency}' not found.",
            error_code="EXCHANGE_RATE_NOT_FOUND",
        )


class CampaignNotFoundError(POSException):
    def __init__(self, campaign_id: str) -> None:
        super().__init__(
            detail=f"Campaign with id {campaign_id} not found",
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="CAMPAIGN_NOT_FOUND",
        )


class CampaignValidationError(POSException):
    def __init__(self, message: str) -> None:
        super().__init__(
            detail=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="CAMPAIGN_VALIDATION_ERROR",
        )


class CampaignDatabaseError(POSException):
    def __init__(self, message: str) -> None:
        super().__init__(
            detail=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="CAMPAIGN_DATABASE_ERROR",
        )


class CampaignNotFoundException(HTTPException):
    def __init__(self, campaign_id: str) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign with ID '{campaign_id}' not found",
        )


class ProductNotFoundException(HTTPException):
    def __init__(self, product_id: str) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product with ID '{product_id}' not found",
        )


class InvalidCampaignTypeException(HTTPException):
    def __init__(self, campaign_type: str) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown campaign type: {campaign_type}",
        )


class InvalidCampaignRulesException(HTTPException):
    def __init__(self, message: str) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )


class ShiftNotFoundError(POSException):
    def __init__(self, shift_id: str) -> None:
        super().__init__(
            detail=f"Shift with id {shift_id} not found",
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="SHIFT_NOT_FOUND",
        )


class ShiftStatusError(POSException):
    def __init__(self) -> None:
        super().__init__(
            detail="Shift is already closed",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="SHIFT_IS_CLOSED",
        )


class ShiftStatusValueError(POSException):
    def __init__(self) -> None:
        super().__init__(
            detail="Invalid status. Must be 'closed'",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="INVALID_STATUS",
        )


class ShiftReportDoesntExistError(POSException):
    def __init__(self, shift_id: str) -> None:
        super().__init__(
            detail=f"This shift with id <{shift_id}> doesnt have receipts",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="INVALID_STATUS",
        )
