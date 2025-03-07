import uuid
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from starlette import status

from core.models.receipt import (
    Currency,
    Payment,
    PaymentStatus,
    Quote,
    Receipt,
    ReceiptItem,
    ReceiptStatus,
)
from core.services.receipt_service import ReceiptService
from infra.api.routers.receipt_router import router
from runner.dependencies import get_receipt_service


@pytest.fixture
def mock_receipt_service() -> Mock:
    """Return a mock receipt service."""
    return Mock(spec=ReceiptService)


@pytest.fixture
def client(mock_receipt_service: Mock) -> TestClient:
    """Test client with mocked dependencies."""
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router, prefix="/receipts")

    # Override dependency
    app.dependency_overrides = {get_receipt_service: lambda: mock_receipt_service}

    return TestClient(app)


def test_create_receipt(client: TestClient, mock_receipt_service: Mock) -> None:
    """Test creating a receipt via the API."""
    # Arrange
    shift_id = uuid.uuid4()

    # Mock service response
    mock_receipt = Receipt(
        id=uuid.uuid4(),
        shift_id=shift_id,
        status=ReceiptStatus.OPEN,
        subtotal=0.0,
        discount_amount=0.0,
        total=0.0,
    )
    mock_receipt_service.create_receipt.return_value = mock_receipt

    # Act
    response = client.post("/receipts/", json={"shift_id": str(shift_id)})

    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "receipt" in data
    receipt = data["receipt"]
    assert receipt["shift_id"] == str(shift_id)
    assert receipt["status"] == "open"

    # Check service calls
    mock_receipt_service.create_receipt.assert_called_once_with(shift_id)


def test_create_receipt_shift_not_found(
    client: TestClient, mock_receipt_service: Mock
) -> None:
    """Test creating a receipt for a non-existent shift."""
    # Arrange
    shift_id = uuid.uuid4()

    # Mock service returns None (shift not found or closed)
    mock_receipt_service.create_receipt.return_value = None

    # Act
    response = client.post("/receipts/", json={"shift_id": str(shift_id)})

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert "detail" in data
    assert f"Shift with ID '{shift_id}'" in data["detail"]

    # Check service calls
    mock_receipt_service.create_receipt.assert_called_once_with(shift_id)


def test_add_product_to_receipt(client: TestClient, mock_receipt_service: Mock) -> None:
    """Test adding a product to a receipt via the API."""
    # Arrange
    receipt_id = uuid.uuid4()
    product_id = uuid.uuid4()
    quantity = 2

    # Mock service response
    mock_receipt = Receipt(
        id=receipt_id,
        shift_id=uuid.uuid4(),
        status=ReceiptStatus.OPEN,
        products=[
            ReceiptItem(
                product_id=product_id,
                quantity=quantity,
                unit_price=10.0,
            )
        ],
        subtotal=20.0,
        total=20.0,
    )
    mock_receipt_service.add_product.return_value = mock_receipt

    # Act
    response = client.post(
        f"/receipts/{receipt_id}/products",
        json={"product_id": str(product_id), "quantity": quantity},
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "receipt" in data
    receipt = data["receipt"]
    assert receipt["id"] == str(receipt_id)
    assert receipt["subtotal"] == 20.0
    assert receipt["total"] == 20.0
    assert len(receipt["products"]) == 1
    assert receipt["products"][0]["product_id"] == str(product_id)
    assert receipt["products"][0]["quantity"] == quantity

    # Check service calls
    mock_receipt_service.add_product.assert_called_once_with(
        receipt_id, product_id, quantity
    )


def test_add_product_receipt_not_found(
    client: TestClient, mock_receipt_service: Mock
) -> None:
    """Test adding a product to a non-existent receipt."""
    # Arrange
    receipt_id = uuid.uuid4()
    product_id = uuid.uuid4()
    quantity = 2

    # Mock service returns None (receipt not found, closed, or product not found)
    mock_receipt_service.add_product.return_value = None

    # Act
    response = client.post(
        f"/receipts/{receipt_id}/products",
        json={"product_id": str(product_id), "quantity": quantity},
    )

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert "detail" in data

    # Check service calls
    mock_receipt_service.add_product.assert_called_once_with(
        receipt_id, product_id, quantity
    )


def test_calculate_payment_quote(
    client: TestClient, mock_receipt_service: Mock
) -> None:
    """Test calculating a payment quote via the API."""
    # Arrange
    receipt_id = uuid.uuid4()

    # Mock service response
    mock_quote = Quote(
        receipt_id=receipt_id,
        base_currency=Currency.GEL,
        requested_currency=Currency.USD,
        exchange_rate=2.5,
        total_in_base_currency=100.0,
        total_in_requested_currency=40.0,  # 100.0 / 2.5
    )
    mock_receipt_service.calculate_payment_quote.return_value = mock_quote

    # Act
    response = client.post(
        f"/receipts/receipts/{receipt_id}/quotes", json={"currency": "USD"}
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "quote" in data
    quote = data["quote"]
    assert quote["receipt_id"] == str(receipt_id)
    assert quote["base_currency"] == "GEL"
    assert quote["requested_currency"] == "USD"
    assert quote["exchange_rate"] == 2.5
    assert quote["total_in_base_currency"] == 100.0
    assert quote["total_in_requested_currency"] == 40.0

    # Check service calls
    mock_receipt_service.calculate_payment_quote.assert_called_once_with(
        receipt_id, Currency.USD
    )


def test_calculate_payment_quote_receipt_not_found(
    client: TestClient, mock_receipt_service: Mock
) -> None:
    """Test calculating a payment quote for a non-existent receipt."""
    # Arrange
    receipt_id = uuid.uuid4()

    # Mock service returns None (receipt not found)
    mock_receipt_service.calculate_payment_quote.return_value = None

    # Act
    response = client.post(
        f"/receipts/receipts/{receipt_id}/quotes", json={"currency": "USD"}
    )

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert "detail" in data
    assert f"Receipt with ID '{receipt_id}'" in data["detail"]

    # Check service calls
    mock_receipt_service.calculate_payment_quote.assert_called_once_with(
        receipt_id, Currency.USD
    )


def test_add_payment(client: TestClient, mock_receipt_service: Mock) -> None:
    """Test adding a payment via the API."""
    # Arrange
    receipt_id = uuid.uuid4()
    payment_id = uuid.uuid4()

    # Mock service response
    payment = Payment(
        id=payment_id,
        receipt_id=receipt_id,
        payment_amount=100.0,
        currency=Currency.GEL,
        total_in_gel=100.0,
        exchange_rate=1.0,
        status=PaymentStatus.COMPLETED,
    )
    updated_receipt = Receipt(
        id=receipt_id,
        shift_id=uuid.uuid4(),
        status=ReceiptStatus.CLOSED,
    )
    mock_receipt_service.add_payment.return_value = (payment, updated_receipt)

    # Act
    response = client.post(
        f"/receipts/{receipt_id}/payments", json={"amount": 100.0, "currency": "GEL"}
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "payment" in data
    assert "receipt" in data

    payment_response = data["payment"]
    assert payment_response["id"] == str(payment_id)
    assert payment_response["payment_amount"] == 100.0
    assert payment_response["currency"] == "GEL"

    receipt_response = data["receipt"]
    assert receipt_response["id"] == str(receipt_id)
    assert receipt_response["status"] == "closed"

    # Check service calls
    mock_receipt_service.add_payment.assert_called_once_with(receipt_id, 100.0, "GEL")


def test_add_payment_receipt_not_found(
    client: TestClient, mock_receipt_service: Mock
) -> None:
    """Test adding a payment to a non-existent receipt."""
    # Arrange
    receipt_id = uuid.uuid4()

    # Mock service returns None (receipt not found or closed)
    mock_receipt_service.add_payment.return_value = None

    # Act
    response = client.post(
        f"/receipts/{receipt_id}/payments", json={"amount": 100.0, "currency": "GEL"}
    )

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert "detail" in data
    assert f"Receipt with ID '{receipt_id}'" in data["detail"]

    # Check service calls
    mock_receipt_service.add_payment.assert_called_once_with(receipt_id, 100.0, "GEL")


def test_add_payment_invalid_currency(
    client: TestClient, mock_receipt_service: Mock
) -> None:
    """Test adding a payment with invalid currency."""
    # Arrange
    receipt_id = uuid.uuid4()

    # Mock service raises ValueError for invalid currency
    mock_receipt_service.add_payment.side_effect = ValueError("Invalid currency")

    # Act
    response = client.post(
        f"/receipts/{receipt_id}/payments",
        json={"amount": 100.0, "currency": "INVALID"},
    )

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert "detail" in data
    assert "Unsupported currency" in data["detail"]

    # Check service calls
    mock_receipt_service.add_payment.assert_called_once_with(
        receipt_id, 100.0, "INVALID"
    )


def test_get_receipt(client: TestClient, mock_receipt_service: Mock) -> None:
    """Test getting a receipt by ID via the API."""
    # Arrange
    receipt_id = uuid.uuid4()
    product_id = uuid.uuid4()

    # Mock service response
    mock_receipt = Receipt(
        id=receipt_id,
        shift_id=uuid.uuid4(),
        status=ReceiptStatus.OPEN,
        products=[
            ReceiptItem(
                product_id=product_id,
                quantity=2,
                unit_price=10.0,
            )
        ],
        subtotal=20.0,
        discount_amount=5.0,
        total=15.0,
    )
    mock_receipt_service.get_receipt.return_value = mock_receipt

    # Act
    response = client.get(f"/receipts/{receipt_id}")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "receipt" in data
    receipt = data["receipt"]
    assert receipt["id"] == str(receipt_id)
    assert receipt["status"] == "open"
    assert receipt["subtotal"] == 20.0
    assert receipt["discount_amount"] == 5.0
    assert receipt["total"] == 15.0

    # Check products
    assert len(receipt["products"]) == 1
    assert receipt["products"][0]["product_id"] == str(product_id)
    assert receipt["products"][0]["quantity"] == 2

    # Check service calls
    mock_receipt_service.get_receipt.assert_called_once_with(receipt_id)


def test_get_receipt_not_found(client: TestClient, mock_receipt_service: Mock) -> None:
    """Test getting a non-existent receipt."""
    # Arrange
    receipt_id = uuid.uuid4()

    # Mock service returns None (receipt not found)
    mock_receipt_service.get_receipt.return_value = None

    # Act
    response = client.get(f"/receipts/{receipt_id}")

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert "detail" in data
    assert f"Receipt with ID '{receipt_id}'" in data["detail"]

    # Check service calls
    mock_receipt_service.get_receipt.assert_called_once_with(receipt_id)
