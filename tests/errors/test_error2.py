import uuid
from typing import Awaitable, Callable, Type, TypeVar, Union

import pytest
from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from core.models.errors import (
    CampaignNotFoundException,
    InvalidCampaignRulesException,
    InvalidCampaignTypeException,
    ShiftNotFoundError,
    ShiftReportDoesntExistError,
)

# Create a type variable for our exception types
E = TypeVar("E", bound=Exception)

# Define the correct return type for exception handlers
ExceptionHandlerType = Callable[
    [Request, Exception], Union[Response, Awaitable[Response]]
]


def create_exception_handler(exception_class: Type[E]) -> ExceptionHandlerType:
    """Create an exception handler for the given exception class."""

    async def exception_handler(request: Request, exc: Exception) -> JSONResponse:
        # If it's a POSException, it already has detail as a dict
        if hasattr(exc, "detail") and isinstance(getattr(exc, "detail"), dict):
            return JSONResponse(
                status_code=getattr(exc, "status_code"), content=getattr(exc, "detail")
            )
        # For standard HTTPException
        return JSONResponse(
            status_code=getattr(exc, "status_code"),
            content={"detail": str(getattr(exc, "detail"))},
        )

    return exception_handler


@pytest.fixture
def app_with_custom_handlers() -> FastAPI:
    """Create a FastAPI app with custom exception handlers."""
    app = FastAPI()

    # Register custom exception handlers
    app.add_exception_handler(
        ShiftNotFoundError, create_exception_handler(ShiftNotFoundError)
    )
    app.add_exception_handler(
        ShiftReportDoesntExistError,
        create_exception_handler(ShiftReportDoesntExistError),
    )
    app.add_exception_handler(
        CampaignNotFoundException, create_exception_handler(CampaignNotFoundException)
    )
    app.add_exception_handler(
        InvalidCampaignTypeException,
        create_exception_handler(InvalidCampaignTypeException),
    )
    app.add_exception_handler(
        InvalidCampaignRulesException,
        create_exception_handler(InvalidCampaignRulesException),
    )

    # Add test routes that raise exceptions
    @app.get("/shift-not-found")
    async def get_shift_not_found() -> None:
        raise ShiftNotFoundError(str(uuid.uuid4()))

    @app.get("/shift-report-not-exist")
    async def get_shift_report_not_exist() -> None:
        raise ShiftReportDoesntExistError(str(uuid.uuid4()))

    @app.get("/campaign-not-found")
    async def get_campaign_not_found() -> None:
        raise CampaignNotFoundException(str(uuid.uuid4()))

    @app.get("/invalid-campaign-type")
    async def get_invalid_campaign_type() -> None:
        raise InvalidCampaignTypeException("invalid_type")

    @app.get("/invalid-campaign-rules")
    async def get_invalid_campaign_rules() -> None:
        raise InvalidCampaignRulesException("Invalid rules configuration")

    return app


@pytest.fixture
def client(app_with_custom_handlers: FastAPI) -> TestClient:
    """Test client for the FastAPI app."""
    return TestClient(app_with_custom_handlers)


def test_shift_not_found_handler(client: TestClient) -> None:
    """Test custom handler for ShiftNotFoundError."""
    # Act
    response = client.get("/shift-not-found")

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["error_code"] == "SHIFT_NOT_FOUND"
    assert "Shift with id" in data["message"]


def test_shift_report_doesnt_exist_handler(client: TestClient) -> None:
    """Test custom handler for ShiftReportDoesntExistError."""
    # Act
    response = client.get("/shift-report-not-exist")

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = response.json()
    assert data["error_code"] == "INVALID_STATUS"
    assert "doesnt have receipts" in data["message"]


def test_campaign_not_found_handler(client: TestClient) -> None:
    """Test custom handler for CampaignNotFoundException."""
    # Act
    response = client.get("/campaign-not-found")

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert "Campaign with ID" in data["detail"]


def test_invalid_campaign_type_handler(client: TestClient) -> None:
    """Test custom handler for InvalidCampaignTypeException."""
    # Act
    response = client.get("/invalid-campaign-type")

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert "Unknown campaign type: invalid_type" in data["detail"]


def test_invalid_campaign_rules_handler(client: TestClient) -> None:
    """Test custom handler for InvalidCampaignRulesException."""
    # Act
    response = client.get("/invalid-campaign-rules")

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert "Invalid rules configuration" in data["detail"]


def test_handler_registration() -> None:
    """Test that exception handlers are properly registered with the app."""
    # Arrange
    app = FastAPI()

    # Initially, the app should have no exception handlers for our custom exceptions
    assert ShiftNotFoundError not in app.exception_handlers

    # Act - register a handler
    handler = create_exception_handler(ShiftNotFoundError)
    app.add_exception_handler(ShiftNotFoundError, handler)

    # Assert - handler should now be registered
    assert ShiftNotFoundError in app.exception_handlers
    assert app.exception_handlers[ShiftNotFoundError] == handler
