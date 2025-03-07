import uuid

from fastapi import HTTPException, status

from core.models.errors import (
    CampaignDatabaseError,
    CampaignNotFoundError,
    CampaignNotFoundException,
    CampaignValidationError,
    ExchangeRateNotFoundError,
    InsufficientPaymentError,
    InvalidCampaignRulesException,
    InvalidCampaignTypeException,
    POSException,
    ProductNotFoundError,
    ProductNotFoundException,
    ReceiptNotFoundError,
    ReceiptStatusError,
    ShiftNotFoundError,
    ShiftReportDoesntExistError,
    ShiftStatusError,
    ShiftStatusValueError,
)


def test_pos_exception_base_class() -> None:
    """Test that POSException has expected properties."""
    # Arrange
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Test error message"
    error_code = "TEST_ERROR"

    # Act
    exception = POSException(status_code, detail, error_code)

    # Assert
    assert exception.status_code == status_code
    assert isinstance(exception.detail, dict)  # Ensure detail is a dictionary
    assert exception.detail == {"error_code": error_code, "message": detail}


def test_receipt_not_found_error() -> None:
    """Test ReceiptNotFoundError construction."""
    # Arrange
    receipt_id = str(uuid.uuid4())

    # Act
    exception = ReceiptNotFoundError(receipt_id)

    # Assert
    assert exception.status_code == status.HTTP_404_NOT_FOUND
    assert isinstance(exception.detail, dict)  # Ensure detail is a dictionary
    assert exception.detail["error_code"] == "RECEIPT_NOT_FOUND"
    assert f"Receipt with ID '{receipt_id}' not found" in exception.detail["message"]


def test_receipt_status_error() -> None:
    """Test ReceiptStatusError construction."""
    # Arrange
    receipt_status = "closed"
    action = "modify"

    # Act
    exception = ReceiptStatusError(receipt_status, action)

    # Assert
    assert exception.status_code == status.HTTP_400_BAD_REQUEST
    assert isinstance(exception.detail, dict)  # Ensure detail is a dictionary
    assert exception.detail["error_code"] == "INVALID_RECEIPT_STATUS"
    assert (
        f"Cannot {action} receipt in '{receipt_status}' status"
        in exception.detail["message"]
    )


def test_insufficient_payment_error() -> None:
    """Test InsufficientPaymentError construction."""
    # Act
    exception = InsufficientPaymentError()

    # Assert
    assert exception.status_code == status.HTTP_400_BAD_REQUEST
    assert isinstance(exception.detail, dict)  # Ensure detail is a dictionary
    assert exception.detail["error_code"] == "INSUFFICIENT_PAYMENT"
    assert "Payment amount is insufficient" in exception.detail["message"]


def test_product_not_found_error() -> None:
    """Test ProductNotFoundError construction."""
    # Arrange
    product_id = str(uuid.uuid4())

    # Act
    exception = ProductNotFoundError(product_id)

    # Assert
    assert exception.status_code == status.HTTP_404_NOT_FOUND
    assert isinstance(exception.detail, dict)  # Ensure detail is a dictionary
    assert exception.detail["error_code"] == "PRODUCT_NOT_FOUND"
    assert f"Product with ID '{product_id}' not found" in exception.detail["message"]


def test_exchange_rate_not_found_error() -> None:
    """Test ExchangeRateNotFoundError construction."""
    # Arrange
    from_currency = "USD"
    to_currency = "GEL"

    # Act
    exception = ExchangeRateNotFoundError(from_currency, to_currency)

    # Assert
    assert exception.status_code == status.HTTP_404_NOT_FOUND
    assert isinstance(exception.detail, dict)  # Ensure detail is a dictionary
    assert exception.detail["error_code"] == "EXCHANGE_RATE_NOT_FOUND"
    assert (
        f"Exchange rate from '{from_currency}' to '{to_currency}' not found"
        in exception.detail["message"]
    )


def test_campaign_not_found_error() -> None:
    """Test CampaignNotFoundError construction."""
    # Arrange
    campaign_id = str(uuid.uuid4())

    # Act
    exception = CampaignNotFoundError(campaign_id)

    # Assert
    assert exception.status_code == status.HTTP_404_NOT_FOUND
    assert isinstance(exception.detail, dict)  # Ensure detail is a dictionary
    assert exception.detail["error_code"] == "CAMPAIGN_NOT_FOUND"
    assert f"Campaign with id {campaign_id} not found" in exception.detail["message"]


def test_campaign_validation_error() -> None:
    """Test CampaignValidationError construction."""
    # Arrange
    message = "Invalid campaign parameters"

    # Act
    exception = CampaignValidationError(message)

    # Assert
    assert exception.status_code == status.HTTP_400_BAD_REQUEST
    assert isinstance(exception.detail, dict)  # Ensure detail is a dictionary
    assert exception.detail["error_code"] == "CAMPAIGN_VALIDATION_ERROR"
    assert message in exception.detail["message"]


def test_campaign_database_error() -> None:
    """Test CampaignDatabaseError construction."""
    # Arrange
    message = "Database connection error"

    # Act
    exception = CampaignDatabaseError(message)

    # Assert
    assert exception.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert isinstance(exception.detail, dict)  # Ensure detail is a dictionary
    assert exception.detail["error_code"] == "CAMPAIGN_DATABASE_ERROR"
    assert message in exception.detail["message"]


def test_campaign_not_found_exception() -> None:
    """Test CampaignNotFoundException construction."""
    # Arrange
    campaign_id = str(uuid.uuid4())

    # Act
    exception = CampaignNotFoundException(campaign_id)

    # Assert
    assert exception.status_code == status.HTTP_404_NOT_FOUND
    assert isinstance(exception.detail, str)  # Ensure detail is a string
    assert f"Campaign with ID '{campaign_id}' not found" in exception.detail


def test_product_not_found_exception() -> None:
    """Test ProductNotFoundException construction."""
    # Arrange
    product_id = str(uuid.uuid4())

    # Act
    exception = ProductNotFoundException(product_id)

    # Assert
    assert exception.status_code == status.HTTP_400_BAD_REQUEST
    assert isinstance(exception.detail, str)  # Ensure detail is a string
    assert f"Product with ID '{product_id}' not found" in exception.detail


def test_invalid_campaign_type_exception() -> None:
    """Test InvalidCampaignTypeException construction."""
    # Arrange
    campaign_type = "invalid_type"

    # Act
    exception = InvalidCampaignTypeException(campaign_type)

    # Assert
    assert exception.status_code == status.HTTP_400_BAD_REQUEST
    assert isinstance(exception.detail, str)  # Ensure detail is a string
    assert f"Unknown campaign type: {campaign_type}" in exception.detail


def test_invalid_campaign_rules_exception() -> None:
    """Test InvalidCampaignRulesException construction."""
    # Arrange
    message = "Invalid rules configuration"

    # Act
    exception = InvalidCampaignRulesException(message)

    # Assert
    assert exception.status_code == status.HTTP_400_BAD_REQUEST
    assert isinstance(exception.detail, str)  # Ensure detail is a string
    assert message in exception.detail


def test_shift_not_found_error() -> None:
    """Test ShiftNotFoundError construction."""
    # Arrange
    shift_id = str(uuid.uuid4())

    # Act
    exception = ShiftNotFoundError(shift_id)

    # Assert
    assert exception.status_code == status.HTTP_404_NOT_FOUND
    assert isinstance(exception.detail, dict)  # Ensure detail is a dictionary
    assert exception.detail["error_code"] == "SHIFT_NOT_FOUND"
    assert f"Shift with id {shift_id} not found" in exception.detail["message"]


def test_shift_status_error() -> None:
    """Test ShiftStatusError construction."""
    # Act
    exception = ShiftStatusError()

    # Assert
    assert exception.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert isinstance(exception.detail, dict)  # Ensure detail is a dictionary
    assert exception.detail["error_code"] == "SHIFT_IS_CLOSED"
    assert "Shift is already closed" in exception.detail["message"]


def test_shift_status_value_error() -> None:
    """Test ShiftStatusValueError construction."""
    # Act
    exception = ShiftStatusValueError()

    # Assert
    assert exception.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert isinstance(exception.detail, dict)  # Ensure detail is a dictionary
    assert exception.detail["error_code"] == "INVALID_STATUS"
    assert "Invalid status. Must be 'closed'" in exception.detail["message"]


def test_shift_report_doesnt_exist_error() -> None:
    """Test ShiftReportDoesntExistError construction."""
    # Arrange
    shift_id = str(uuid.uuid4())

    # Act
    exception = ShiftReportDoesntExistError(shift_id)

    # Assert
    assert exception.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert isinstance(exception.detail, dict)  # Ensure detail is a dictionary
    assert exception.detail["error_code"] == "INVALID_STATUS"
    assert (
        f"This shift with id <{shift_id}> doesnt have receipts"
        in exception.detail["message"]
    )


def test_exception_inheritance() -> None:
    """Test that all exceptions inherit properly from base classes."""
    # POS Exceptions
    assert issubclass(ReceiptNotFoundError, POSException)
    assert issubclass(ReceiptStatusError, POSException)
    assert issubclass(InsufficientPaymentError, POSException)
    assert issubclass(ProductNotFoundError, POSException)
    assert issubclass(ExchangeRateNotFoundError, POSException)
    assert issubclass(CampaignNotFoundError, POSException)
    assert issubclass(CampaignValidationError, POSException)
    assert issubclass(CampaignDatabaseError, POSException)
    assert issubclass(ShiftNotFoundError, POSException)
    assert issubclass(ShiftStatusError, POSException)
    assert issubclass(ShiftStatusValueError, POSException)
    assert issubclass(ShiftReportDoesntExistError, POSException)

    # HTTPException subclasses
    assert issubclass(POSException, HTTPException)
    assert issubclass(CampaignNotFoundException, HTTPException)
    assert issubclass(ProductNotFoundException, HTTPException)
    assert issubclass(InvalidCampaignTypeException, HTTPException)
    assert issubclass(InvalidCampaignRulesException, HTTPException)
