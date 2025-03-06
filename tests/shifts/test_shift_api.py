from typing import Any, Dict, cast
import uuid
from datetime import datetime
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from starlette import status

from core.models.shift import Shift, ShiftStatus
from core.models.errors import ShiftNotFoundError, ShiftStatusError, ShiftStatusValueError
from core.services.shift_service import ShiftService
from infra.api.routers.shift_router import router
from runner.dependencies import get_shift_service


@pytest.fixture
def mock_shift_service() -> Mock:
    """Return a mock shift service."""
    return Mock(spec=ShiftService)


@pytest.fixture
def client(mock_shift_service: Mock) -> TestClient:
    """Test client with mocked dependencies."""
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router, prefix="/shifts")

    # Override dependency
    app.dependency_overrides = {
        get_shift_service: lambda: mock_shift_service
    }

    return TestClient(app)


def test_open_shift(client: TestClient, mock_shift_service: Mock) -> None:
    """Test opening a shift via the API."""
    # Arrange
    shift_id = uuid.uuid4()

    # Mock service response
    mock_shift = Shift(
        id=shift_id,
        status=ShiftStatus.OPEN,
        created_at=datetime.now(),
    )
    mock_shift_service.open_shift.return_value = mock_shift

    # Act
    response = client.post("/shifts/")

    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "shift" in data
    shift = data["shift"]
    assert shift["id"] == str(shift_id)
    assert shift["status"] == "open"

    # Check service calls
    mock_shift_service.open_shift.assert_called_once()


def test_close_shift(client: TestClient, mock_shift_service: Mock) -> None:
    """Test closing a shift via the API."""
    # Arrange
    shift_id = uuid.uuid4()

    # Mock service response
    mock_shift = Shift(
        id=shift_id,
        status=ShiftStatus.CLOSED,
        created_at=datetime.now(),
        closed_at=datetime.now(),
    )
    mock_shift_service.close_shift.return_value = mock_shift

    # Act
    response = client.patch(
        f"/shifts/{shift_id}",
        json={"status": "closed"}
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "shift" in data
    shift = data["shift"]
    assert shift["id"] == str(shift_id)
    assert shift["status"] == "closed"

    # Check service calls
    mock_shift_service.close_shift.assert_called_once()
    # Verify the call arguments
    args, kwargs = mock_shift_service.close_shift.call_args
    assert args[0] == shift_id
    assert args[1].status == "closed"


def test_close_shift_not_found(client: TestClient, mock_shift_service: Mock) -> None:
    """Test closing a non-existent shift via the API."""
    # Arrange
    shift_id = uuid.uuid4()

    # Mock service to raise an exception
    mock_shift_service.close_shift.side_effect = ShiftNotFoundError(str(shift_id))

    # Act
    response = client.patch(
        f"/shifts/{shift_id}",
        json={"status": "closed"}
    )

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert "detail" in data
    assert str(shift_id) in data["detail"]["message"]

    # Check service calls
    mock_shift_service.close_shift.assert_called_once()


def test_close_shift_invalid_status(client: TestClient, mock_shift_service: Mock) -> None:
    """Test closing a shift with an invalid status via the API."""
    # Arrange
    shift_id = uuid.uuid4()

    # Mock service to raise an exception
    mock_shift_service.close_shift.side_effect = ShiftStatusValueError()

    # Act
    response = client.patch(
        f"/shifts/{shift_id}",
        json={"status": "invalid_status"}
    )

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = response.json()
    assert "detail" in data

    # Check service calls
    mock_shift_service.close_shift.assert_called_once()


def test_close_shift_already_closed(client: TestClient, mock_shift_service: Mock) -> None:
    """Test closing a shift that is already closed via the API."""
    # Arrange
    shift_id = uuid.uuid4()

    # Mock service to raise an exception
    mock_shift_service.close_shift.side_effect = ShiftStatusError()

    # Act
    response = client.patch(
        f"/shifts/{shift_id}",
        json={"status": "closed"}
    )

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = response.json()
    assert "detail" in data

    # Check service calls
    mock_shift_service.close_shift.assert_called_once()


def test_close_shift_invalid_uuid(client: TestClient) -> None:
    """Test closing a shift with an invalid UUID format."""
    # Act
    response = client.patch(
        "/shifts/invalid-uuid",
        json={"status": "closed"}
    )

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = response.json()
    assert "detail" in data