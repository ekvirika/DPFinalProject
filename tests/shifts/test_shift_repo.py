import uuid
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pytest

from core.models.errors import (
    ShiftNotFoundError,
    ShiftStatusError,
    ShiftStatusValueError,
)
from core.models.shift import Shift, ShiftStatus
from infra.api.schemas.shift import ShiftUpdate
from infra.db.database import Database
from infra.repositories.shift_sqlite_repository import SQLiteShiftRepository


@pytest.fixture
def mock_db() -> Mock:
    """Return a mock database."""
    mock_db = Mock(spec=Database)
    mock_connection = MagicMock()
    mock_cursor = MagicMock()
    mock_connection.__enter__.return_value = mock_connection
    mock_connection.cursor.return_value = mock_cursor
    mock_db.get_connection.return_value = mock_connection
    return mock_db


@pytest.fixture
def shift_repository(mock_db: Mock) -> SQLiteShiftRepository:
    """Return a shift repository with a mock database."""
    return SQLiteShiftRepository(mock_db)


def test_get_shift_by_id(
    shift_repository: SQLiteShiftRepository, mock_db: Mock
) -> None:
    """Test getting a shift by ID."""
    # Arrange
    shift_id = uuid.uuid4()
    created_at = datetime(2023, 1, 1, 10, 0, 0)

    # Set up the mock cursor to return a shift
    mock_cursor = (
        mock_db.get_connection.return_value.__enter__.return_value.cursor.return_value
    )
    mock_cursor.fetchone.return_value = {
        "id": str(shift_id),
        "status": ShiftStatus.OPEN.value,
        "created_at": created_at.isoformat(),
        "closed_at": None,
    }

    # Act
    shift = shift_repository.get_by_id(shift_id)

    # Assert
    assert str(shift.id) == str(shift_id)
    assert shift.status == ShiftStatus.OPEN
    assert shift.created_at == created_at
    assert shift.closed_at is None

    # Check DB calls
    mock_cursor.execute.assert_called_once_with(
        "SELECT * FROM shifts WHERE id = ?", (str(shift_id),)
    )


def test_get_shift_by_id_not_found(
    shift_repository: SQLiteShiftRepository, mock_db: Mock
) -> None:
    """Test getting a non-existent shift by ID."""
    # Arrange
    shift_id = uuid.uuid4()

    # Set up the mock cursor to return no shift
    mock_cursor = (
        mock_db.get_connection.return_value.__enter__.return_value.cursor.return_value
    )
    mock_cursor.fetchone.return_value = None

    # Act & Assert
    with pytest.raises(ShiftNotFoundError) as exc_info:
        shift_repository.get_by_id(shift_id)

    assert str(shift_id) in str(exc_info.value)

    # Check DB calls
    mock_cursor.execute.assert_called_once_with(
        "SELECT * FROM shifts WHERE id = ?", (str(shift_id),)
    )


def test_update_status_open_to_closed(
    shift_repository: SQLiteShiftRepository, mock_db: Mock
) -> None:
    """Test updating a shift status from open to closed."""
    # Arrange
    shift_id = uuid.uuid4()
    created_at = datetime(2023, 1, 1, 10, 0, 0)
    closed_at = datetime(2023, 1, 1, 18, 0, 0)

    # Mock get_by_id to return an open shift
    open_shift = Shift(
        id=shift_id,
        status=ShiftStatus.OPEN,
        created_at=created_at,
    )

    # Mock get_by_id after update to return a closed shift
    closed_shift = Shift(
        id=shift_id,
        status=ShiftStatus.CLOSED,
        created_at=created_at,
        closed_at=closed_at,
    )

    # Set up the mock cursor
    mock_cursor = (
        mock_db.get_connection.return_value.__enter__.return_value.cursor.return_value
    )

    # Act
    with patch.object(
        SQLiteShiftRepository, "get_by_id", side_effect=[open_shift, closed_shift]
    ):
        result = shift_repository.update_status(
            shift_id, ShiftUpdate(status="closed"), closed_at
        )

    # Assert
    assert result.id == shift_id
    assert result.status == ShiftStatus.CLOSED
    assert result.created_at == created_at
    assert result.closed_at == closed_at

    # Check DB calls
    mock_cursor.execute.assert_called_once_with(
        "UPDATE shifts SET status = ?, closed_at = ? WHERE id = ?",
        (ShiftStatus.CLOSED.value, closed_at, str(shift_id)),
    )
    mock_db.get_connection.return_value.__enter__.return_value.commit.assert_called_once()


def test_update_status_already_closed(
    shift_repository: SQLiteShiftRepository, mock_db: Mock
) -> None:
    """Test updating a shift status that is already in the target state."""
    # Arrange
    shift_id = uuid.uuid4()
    created_at = datetime(2023, 1, 1, 10, 0, 0)
    closed_at = datetime(2023, 1, 1, 18, 0, 0)

    # Mock get_by_id to return a closed shift
    closed_shift = Shift(
        id=shift_id,
        status=ShiftStatus.CLOSED,
        created_at=created_at,
        closed_at=closed_at,
    )

    # Act & Assert
    with (
        patch.object(SQLiteShiftRepository, "get_by_id", return_value=closed_shift),
        pytest.raises(ShiftStatusError),
    ):
        shift_repository.update_status(
            shift_id, ShiftUpdate(status="closed"), datetime.now()
        )


def test_update_status_invalid_status(shift_repository: SQLiteShiftRepository) -> None:
    """Test updating a shift with an invalid status value."""
    # Arrange
    shift_id = uuid.uuid4()

    # Act & Assert
    with pytest.raises(ShiftStatusValueError):
        shift_repository.update_status(
            shift_id, ShiftUpdate(status="invalid"), datetime.now()
        )
