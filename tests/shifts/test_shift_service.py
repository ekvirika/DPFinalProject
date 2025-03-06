from typing import Any, cast
import uuid
from datetime import datetime
from unittest.mock import Mock

import pytest

from core.models.shift import Shift, ShiftStatus
from core.models.repositories.shift_repository import ShiftRepository
from core.services.shift_service import ShiftService
from infra.api.schemas.shift import ShiftUpdate


@pytest.fixture
def mock_shift_repository() -> Mock:
    """Return a mock shift repository."""
    return Mock(spec=ShiftRepository)


@pytest.fixture
def shift_service(mock_shift_repository: Mock) -> ShiftService:
    """Return a shift service with a mock repository."""
    return ShiftService(mock_shift_repository)


def test_open_shift(shift_service: ShiftService, mock_shift_repository: Mock) -> None:
    """Test opening a new shift through the service layer."""
    # Arrange
    shift_id = uuid.uuid4()
    expected_shift = Shift(
        id=shift_id,
        status=ShiftStatus.OPEN,
        created_at=datetime.now(),
    )
    mock_shift_repository.create.return_value = expected_shift

    # Act
    result = shift_service.open_shift()

    # Assert
    assert result == expected_shift
    mock_shift_repository.create.assert_called_once()


def test_get_shift(shift_service: ShiftService, mock_shift_repository: Mock) -> None:
    """Test getting a shift by ID through the service layer."""
    # Arrange
    shift_id = uuid.uuid4()
    expected_shift = Shift(
        id=shift_id,
        status=ShiftStatus.OPEN,
        created_at=datetime.now(),
    )
    mock_shift_repository.get_by_id.return_value = expected_shift

    # Act
    result = shift_service.get_shift(shift_id)

    # Assert
    assert result == expected_shift
    mock_shift_repository.get_by_id.assert_called_once_with(shift_id)