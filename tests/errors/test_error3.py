import uuid
from unittest.mock import Mock, AsyncMock, patch

import pytest
from fastapi import FastAPI, Request, status
from fastapi.testclient import TestClient
from starlette.middleware.exceptions import ExceptionMiddleware

from core.models.errors import (
    POSException,
    ReceiptNotFoundError,
    ShiftNotFoundError,
    CampaignNotFoundException,
    ProductNotFoundException,
)


@pytest.fixture
def app_with_exception_handler():
    """Create a FastAPI app with exception handlers."""
    app = FastAPI()

    # Register routes that will raise exceptions
    @app.get("/pos-exception")
    async def raise_pos_exception():
        raise POSException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Test error message",
            error_code="TEST_ERROR"
        )

    @app.get("/receipt-not-found")
    async def raise_receipt_not_found():
        receipt_id = str(uuid.uuid4())
        raise ReceiptNotFoundError(receipt_id)

    @app.get("/shift-not-found")
    async def raise_shift_not_found():
        shift_id = str(uuid.uuid4())
        raise ShiftNotFoundError(shift_id)

    @app.get("/campaign-not-found")
    async def raise_campaign_not_found():
        campaign_id = str(uuid.uuid4())
        raise CampaignNotFoundException(campaign_id)

    @app.get("/product-not-found")
    async def raise_product_not_found():
        product_id = str(uuid.uuid4())
        raise ProductNotFoundException(product_id)

    @app.get("/unhandled-exception")
    async def raise_unhandled_exception():
        raise ValueError("This is an unhandled exception")

    return app


@pytest.fixture
def client(app_with_exception_handler):
    """Test client for the FastAPI app."""
    return TestClient(app_with_exception_handler)


def test_pos_exception_handling(client):
    """Test that POSException is handled properly."""
    # Act
    response = client.get("/pos-exception")

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["detail"]["error_code"] == "TEST_ERROR"
    assert data["detail"]["message"] == "Test error message"


def test_receipt_not_found_error_handling(client):
    """Test that ReceiptNotFoundError is handled properly."""
    # Act
    response = client.get("/receipt-not-found")

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"]["error_code"] == "RECEIPT_NOT_FOUND"
    assert "Receipt with ID" in data["detail"]["message"]


def test_shift_not_found_error_handling(client):
    """Test that ShiftNotFoundError is handled properly."""
    # Act
    response = client.get("/shift-not-found")

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"]["error_code"] == "SHIFT_NOT_FOUND"
    assert "Shift with id" in data["detail"]["message"]


def test_campaign_not_found_exception_handling(client):
    """Test that CampaignNotFoundException (HTTPException) is handled properly."""
    # Act
    response = client.get("/campaign-not-found")

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Campaign with ID" in response.json()["detail"]


def test_product_not_found_exception_handling(client):
    """Test that ProductNotFoundException (HTTPException) is handled properly."""
    # Act
    response = client.get("/product-not-found")

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Product with ID" in response.json()["detail"]
