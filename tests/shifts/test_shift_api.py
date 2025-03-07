import uuid
from datetime import datetime
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from starlette import status

from core.models.shift import Shift, ShiftStatus
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
    app.dependency_overrides = {get_shift_service: lambda: mock_shift_service}

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
