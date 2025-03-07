import uuid
from unittest.mock import MagicMock, Mock

import pytest

from core.models.report import SalesReport
from infra.db.database import Database
from infra.repositories.receipt_sqlite_repository import SQLiteReceiptRepository
from infra.repositories.report_sqlite_repository import SQLiteReportRepository


@pytest.fixture
def mock_db() -> Mock:
    """Mock database connection."""
    mock_db = Mock(spec=Database)
    mock_connection = MagicMock()
    mock_cursor = MagicMock()
    mock_connection.__enter__.return_value = mock_connection
    mock_connection.cursor.return_value = mock_cursor
    mock_db.get_connection.return_value = mock_connection
    return mock_db


@pytest.fixture
def mock_receipt_repository() -> Mock:
    """Mock receipt repository."""
    return Mock(spec=SQLiteReceiptRepository)


@pytest.fixture
def mock_shift_repository() -> Mock:
    """Mock shift repository."""
    return Mock()


@pytest.fixture
def report_repository(
    mock_db: Mock, mock_receipt_repository: Mock, mock_shift_repository: Mock
) -> SQLiteReportRepository:
    """Repository with mocked dependencies."""
    return SQLiteReportRepository(
        mock_db, mock_receipt_repository, mock_shift_repository
    )


def test_generate_shift_report_no_receipts(
    report_repository: SQLiteReportRepository, mock_receipt_repository: Mock
) -> None:
    """Test generating a shift report with no receipts."""
    # Arrange
    shift_id = uuid.uuid4()
    mock_receipt_repository.get_receipts_by_shift.return_value = []

    # Act & Assert
    shift_report = report_repository.generate_shift_report(shift_id)

    assert shift_report.receipt_count == 0
    assert len(shift_report.items_sold) == 0


def test_generate_sales_report(
    report_repository: SQLiteReportRepository, mock_db: Mock
) -> None:
    """Test generating a sales report."""
    # Arrange
    mock_cursor = mock_db.get_connection().__enter__().cursor()

    # Mock query results
    mock_cursor.fetchone.side_effect = [
        {"total_items": 100},  # Total items sold
        {"receipt_count": 30},  # Total receipts
        {"total_gel": 2500.0},  # Total revenue in GEL
    ]

    mock_cursor.fetchall.return_value = [
        {"currency": "GEL", "total_amount": 2000.0},
        {"currency": "USD", "total_amount": 500.0},
    ]

    # Act
    report = report_repository.generate_sales_report()

    # Assert
    assert isinstance(report, SalesReport)
    assert report.total_items_sold == 100
    assert report.total_receipts == 30
    assert report.total_revenue == {"GEL": 2000.0, "USD": 500.0}
    assert report.total_revenue_gel == 2500.0


def test_generate_sales_report_no_data(
    report_repository: SQLiteReportRepository, mock_db: Mock
) -> None:
    """Test generating a sales report with no data."""
    # Arrange
    mock_cursor = mock_db.get_connection().__enter__().cursor()

    # Mock query results with no data
    mock_cursor.fetchone.side_effect = [
        {"total_items": None},  # No items sold
        {"receipt_count": 0},  # No receipts
        {"total_gel": None},  # No revenue in GEL
    ]

    mock_cursor.fetchall.return_value = []  # No revenue by currency

    # Act
    report = report_repository.generate_sales_report()

    # Assert
    assert isinstance(report, SalesReport)
    assert report.total_items_sold == 0
    assert report.total_receipts == 0
    assert report.total_revenue == {}
    assert report.total_revenue_gel == 0
