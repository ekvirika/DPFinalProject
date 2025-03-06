from typing import Any, Dict, List, cast
import uuid
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from core.models.errors import ShiftNotFoundError
from core.models.receipt import Currency, ItemSold, RevenueByCurrency
from core.models.report import SalesReport, ShiftReport
from core.services.report_service import ReportService
from core.services.shift_service import ShiftService
from infra.api.routers.report_router import router
from runner.dependencies import get_report_service, get_shift_service


@pytest.fixture
def mock_report_service() -> Mock:
    """Return a mock report service."""
    return Mock(spec=ReportService)


@pytest.fixture
def mock_shift_service() -> Mock:
    """Return a mock shift service."""
    return Mock(spec=ShiftService)


@pytest.fixture
def client(mock_report_service: Mock, mock_shift_service: Mock) -> TestClient:
    """Test client with mocked dependencies."""
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router, prefix="/reports")

    # Override dependencies
    app.dependency_overrides = {
        get_report_service: lambda: mock_report_service,
        get_shift_service: lambda: mock_shift_service,
    }

    return TestClient(app)


def test_get_x_report(
        client: TestClient, mock_report_service: Mock, mock_shift_service: Mock
) -> None:
    """Test getting an X report via the API."""
    # Arrange
    shift_id = uuid.uuid4()
    product_id_1 = uuid.uuid4()
    product_id_2 = uuid.uuid4()

    # Create expected report
    expected_report = ShiftReport(
        shift_id=shift_id,
        receipt_count=5,
        items_sold=[
            ItemSold(product_id=product_id_1, name="Product 1", quantity=3),
            ItemSold(product_id=product_id_2, name="Product 2", quantity=2),
        ],
        revenue_by_currency=[
            RevenueByCurrency(currency=Currency.GEL, amount=100.0),
            RevenueByCurrency(currency=Currency.USD, amount=50.0),
        ],
    )

    # Mock service response
    mock_report_service.generate_x_report.return_value = expected_report

    # Act
    response = client.get(f"/reports/x-reports?shift_id={shift_id}")

    # Assert
    assert response.status_code == 200
    data = response.json()

    assert "x-report" in data
    report = data["x-report"]

    assert report["shift_id"] == str(shift_id)
    assert report["receipt_count"] == 5

    # Check items sold
    assert len(report["items_sold"]) == 2
    assert any(
        item["product_id"] == str(product_id_1) and item["name"] == "Product 1" and item["quantity"] == 3
        for item in report["items_sold"]
    )
    assert any(
        item["product_id"] == str(product_id_2) and item["name"] == "Product 2" and item["quantity"] == 2
        for item in report["items_sold"]
    )

    # Check revenue by currency
    assert len(report["revenue_by_currency"]) == 2
    assert any(
        revenue["currency"] == "GEL" and revenue["amount"] == 100.0
        for revenue in report["revenue_by_currency"]
    )
    assert any(
        revenue["currency"] == "USD" and revenue["amount"] == 50.0
        for revenue in report["revenue_by_currency"]
    )

    # Check service calls
    mock_report_service.generate_x_report.assert_called_once_with(shift_id, mock_shift_service)


def test_get_x_report_shift_not_found(
        client: TestClient, mock_report_service: Mock
) -> None:
    """Test getting an X report for a non-existent shift."""
    # Arrange
    shift_id = uuid.uuid4()
    mock_report_service.generate_x_report.side_effect = ShiftNotFoundError(str(shift_id))

    # Act
    response = client.get(f"/reports/x-reports?shift_id={shift_id}")

    # Assert
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert data["detail"]["message"] == f"Shift with id {shift_id} not found"


def test_get_sales_report(client: TestClient, mock_report_service: Mock) -> None:
    """Test getting a sales report via the API."""
    # Arrange
    expected_report = SalesReport(
        total_items_sold=100,
        total_receipts=30,
        total_revenue={"GEL": 2000.0, "USD": 500.0},
        total_revenue_gel=2500.0,
    )

    # Mock service response
    mock_report_service.generate_sales_report.return_value = expected_report

    # Act
    response = client.get("/reports/sales")

    # Assert
    assert response.status_code == 200
    data = response.json()

    assert "sales" in data
    report = data["sales"]

    assert report["total_items_sold"] == 100
    assert report["total_receipts"] == 30
    assert report["total_revenue"] == {"GEL": 2000.0, "USD": 500.0}
    assert report["total_revenue_gel"] == 2500.0

    # Check service calls
    mock_report_service.generate_sales_report.assert_called_once()


# Test for invalid UUID format in shift_id
def test_get_x_report_invalid_shift_id(client: TestClient) -> None:
    """Test getting an X report with invalid shift ID format."""
    # Act
    response = client.get("/reports/x-reports?shift_id=invalid-uuid")

    # Assert
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert data["detail"][0]["type"] == "uuid_parsing"