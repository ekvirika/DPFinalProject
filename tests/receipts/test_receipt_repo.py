from unittest.mock import MagicMock, Mock, patch
from uuid import UUID, uuid4

import pytest

from core.models.errors import ReceiptNotFoundError
from core.models.receipt import (
    Currency,
    PaymentStatus,
    Receipt,
    ReceiptStatus,
)
from infra.db.database import Database
from infra.repositories.receipt_sqlite_repository import SQLiteReceiptRepository


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
def receipt_repository(mock_db: Mock) -> SQLiteReceiptRepository:
    """Return a receipt repository with a mock database."""
    return SQLiteReceiptRepository(mock_db)


def test_create_receipt(
    receipt_repository: SQLiteReceiptRepository, mock_db: Mock
) -> None:
    """Test creating a new receipt."""
    # Arrange
    shift_id = uuid4()

    # Set up the mock connection and cursor
    mock_connection = mock_db.get_connection.return_value.__enter__.return_value
    mock_cursor = mock_connection.cursor.return_value

    # Act
    with patch("uuid.UUID", return_value=UUID("00000000-0000-0000-0000-000000000001")):
        receipt = receipt_repository.create(shift_id)

    # Assert
    assert receipt.id == UUID("00000000-0000-0000-0000-000000000001")
    assert receipt.shift_id == shift_id
    assert receipt.status == ReceiptStatus.OPEN
    assert receipt.products == []
    assert receipt.payments == []
    assert receipt.subtotal == 0
    assert receipt.discount_amount == 0
    assert receipt.total == 0
    assert receipt.discounts == []

    # Check DB calls
    mock_cursor.execute.assert_called_once_with(
        """
                INSERT INTO receipts (id, shift_id, status, subtotal, 
                discount_amount, total)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
        (
            "00000000-0000-0000-0000-000000000001",
            str(shift_id),
            ReceiptStatus.OPEN.value,
            0,
            0,
            0,
        ),
    )
    mock_connection.commit.assert_called_once()


def test_get_receipt_with_discounts(
    receipt_repository: SQLiteReceiptRepository, mock_db: Mock
) -> None:
    """Test getting a receipt by ID with all its items, discounts, and payments."""
    # Arrange
    receipt_id = uuid4()
    shift_id = uuid4()

    # Set up the mock cursor for fetching data
    mock_cursor = (
        mock_db.get_connection.return_value.__enter__.return_value.cursor.return_value
    )

    # Mock receipt basic info
    receipt_row = {
        "id": str(receipt_id),
        "shift_id": str(shift_id),
        "status": ReceiptStatus.OPEN.value,
        "subtotal": 150.0,
        "discount_amount": 25.0,
        "total": 125.0,
    }

    # Mock receipt-level discounts
    campaign_id_receipt = uuid4()
    receipt_discount_rows = [
        {
            "campaign_id": str(campaign_id_receipt),
            "campaign_name": "Weekend Special",
            "discount_amount": 15.0,
        }
    ]

    # Mock receipt items
    item_id_1 = uuid4()
    item_id_2 = uuid4()
    product_id_1 = uuid4()
    product_id_2 = uuid4()

    item_rows = [
        {
            "id": str(item_id_1),
            "receipt_id": str(receipt_id),
            "product_id": str(product_id_1),
            "quantity": 2,
            "unit_price": 45.0,
            "total_price": 90.0,
            "final_price": 85.0,
        },
        {
            "id": str(item_id_2),
            "receipt_id": str(receipt_id),
            "product_id": str(product_id_2),
            "quantity": 3,
            "unit_price": 20.0,
            "total_price": 60.0,
            "final_price": 55.0,
        },
    ]

    # Mock item discount data for first item
    campaign_id_1 = uuid4()
    discount_rows_1 = [
        {
            "campaign_id": str(campaign_id_1),
            "campaign_name": "First Item Discount",
            "discount_amount": 5.0,
        }
    ]

    # Mock item discount data for second item
    campaign_id_2 = uuid4()
    discount_rows_2 = [
        {
            "campaign_id": str(campaign_id_2),
            "campaign_name": "Bulk Purchase",
            "discount_amount": 5.0,
        }
    ]

    # Mock payment data
    payment_id = uuid4()
    payment_rows = [
        {
            "id": str(payment_id),
            "receipt_id": str(receipt_id),
            "payment_amount": 125.0,
            "currency": Currency.GEL.value,
            "total_in_gel": 125.0,
            "exchange_rate": 1.0,
            "status": PaymentStatus.COMPLETED.value,
        }
    ]

    # Set up mock cursor to return the expected data in the correct sequence
    mock_cursor.fetchone.side_effect = [
        receipt_row,
        None,
    ]  # For receipt and potential non-existing receipt
    mock_cursor.fetchall.side_effect = [
        receipt_discount_rows,  # For receipt-level discounts
        item_rows,  # For receipt items
        discount_rows_1,  # For first item discounts
        discount_rows_2,  # For second item discounts
        payment_rows,  # For payments
    ]

    # Act
    receipt = receipt_repository.get(receipt_id)

    # Assert
    assert receipt.id == receipt_id
    assert receipt.shift_id == shift_id
    assert receipt.status == ReceiptStatus.OPEN
    assert receipt.subtotal == 150.0
    assert receipt.discount_amount == 25.0
    assert receipt.total == 125.0

    # Check receipt-level discounts
    assert len(receipt.discounts) == 1
    assert receipt.discounts[0].campaign_id == campaign_id_receipt
    assert receipt.discounts[0].campaign_name == "Weekend Special"
    assert receipt.discounts[0].discount_amount == 15.0

    # Check items
    assert len(receipt.products) == 2

    # First item
    assert receipt.products[0].product_id == product_id_1
    assert receipt.products[0].quantity == 2
    assert receipt.products[0].unit_price == 45.0
    assert receipt.products[0].total_price == 90.0
    assert receipt.products[0].final_price == 85.0

    # First item discounts
    assert len(receipt.products[0].discounts) == 1
    assert receipt.products[0].discounts[0].campaign_id == campaign_id_1
    assert receipt.products[0].discounts[0].campaign_name == "First Item Discount"
    assert receipt.products[0].discounts[0].discount_amount == 5.0

    # Second item
    assert receipt.products[1].product_id == product_id_2
    assert receipt.products[1].quantity == 3
    assert receipt.products[1].unit_price == 20.0
    assert receipt.products[1].total_price == 60.0
    assert receipt.products[1].final_price == 55.0

    # Second item discounts
    assert len(receipt.products[1].discounts) == 1
    assert receipt.products[1].discounts[0].campaign_id == campaign_id_2
    assert receipt.products[1].discounts[0].campaign_name == "Bulk Purchase"
    assert receipt.products[1].discounts[0].discount_amount == 5.0

    # Check payments
    assert len(receipt.payments) == 1
    assert receipt.payments[0].id == payment_id
    assert receipt.payments[0].receipt_id == receipt_id
    assert receipt.payments[0].payment_amount == 125.0
    assert receipt.payments[0].currency == Currency.GEL
    assert receipt.payments[0].total_in_gel == 125.0
    assert receipt.payments[0].exchange_rate == 1.0
    assert receipt.payments[0].status == PaymentStatus.COMPLETED

    # Check DB calls
    mock_cursor.execute.assert_any_call(
        "SELECT * FROM receipts WHERE id = ?",
        (str(receipt_id),),
    )
    mock_cursor.execute.assert_any_call(
        "SELECT * FROM receipt_discounts WHERE receipt_id = ?",
        (str(receipt_id),),
    )
    mock_cursor.execute.assert_any_call(
        "SELECT * FROM receipt_items WHERE receipt_id = ?",
        (str(receipt_id),),
    )

    # Check that item discount queries were made with correct item IDs
    mock_cursor.execute.assert_any_call(
        "SELECT * FROM receipt_item_discounts WHERE receipt_item_id = ?",
        (str(item_id_1),),
    )
    mock_cursor.execute.assert_any_call(
        "SELECT * FROM receipt_item_discounts WHERE receipt_item_id = ?",
        (str(item_id_2),),
    )

    mock_cursor.execute.assert_any_call(
        "SELECT * FROM payments WHERE receipt_id = ?",
        (str(receipt_id),),
    )


def test_get_receipt_not_found(
    receipt_repository: SQLiteReceiptRepository, mock_db: Mock
) -> None:
    """Test getting a non-existent receipt."""
    # Arrange
    receipt_id = uuid4()

    # Set up the mock cursor to return no data
    mock_cursor = (
        mock_db.get_connection.return_value.__enter__.return_value.cursor.return_value
    )
    mock_cursor.fetchone.return_value = None

    # Act & Assert
    with pytest.raises(ReceiptNotFoundError) as exc_info:
        receipt_repository.get(receipt_id)

    assert str(receipt_id) in str(exc_info.value)

    # Check DB calls
    mock_cursor.execute.assert_called_once_with(
        "SELECT * FROM receipts WHERE id = ?",
        (str(receipt_id),),
    )


def test_update_status(
    receipt_repository: SQLiteReceiptRepository, mock_db: Mock
) -> None:
    """Test updating the status of a receipt."""
    # Arrange
    receipt_id = uuid4()
    new_status = ReceiptStatus.CLOSED

    # Mock the get method to return a receipt after update
    with patch.object(
        SQLiteReceiptRepository,
        "get",
        return_value=Receipt(id=receipt_id, shift_id=uuid4(), status=new_status),
    ):
        # Act
        updated_receipt = receipt_repository.update_status(receipt_id, new_status)

    # Assert
    assert updated_receipt.id == receipt_id
    assert updated_receipt.status == new_status

    # Check DB calls
    mock_db.get_connection.return_value.__enter__.return_value.cursor.return_value.execute.assert_called_once_with(
        "UPDATE receipts SET status = ? WHERE id = ?",
        (new_status.value, str(receipt_id)),
    )
    mock_db.get_connection.return_value.__enter__.return_value.commit.assert_called_once()


def test_get_receipts_by_shift(
    receipt_repository: SQLiteReceiptRepository, mock_db: Mock
) -> None:
    """Test getting all receipts for a shift."""
    # Arrange
    shift_id = uuid4()
    receipt_id_1 = uuid4()
    receipt_id_2 = uuid4()

    # Set up the mock cursor
    mock_cursor = (
        mock_db.get_connection.return_value.__enter__.return_value.cursor.return_value
    )
    mock_cursor.fetchall.return_value = [
        {"id": str(receipt_id_1)},
        {"id": str(receipt_id_2)},
    ]

    # Mock receipt objects to be returned by get method
    receipt_1 = Receipt(id=receipt_id_1, shift_id=shift_id, status=ReceiptStatus.OPEN)
    receipt_2 = Receipt(id=receipt_id_2, shift_id=shift_id, status=ReceiptStatus.CLOSED)

    # Set up mock for the get method
    with patch.object(
        SQLiteReceiptRepository, "get", side_effect=[receipt_1, receipt_2]
    ):
        # Act
        receipts = receipt_repository.get_receipts_by_shift(shift_id)

    # Assert
    assert len(receipts) == 2
    assert receipts[0].id == receipt_id_1
    assert receipts[1].id == receipt_id_2

    # Check DB calls
    mock_cursor.execute.assert_called_once_with(
        "SELECT id FROM receipts WHERE shift_id = ?",
        (str(shift_id),),
    )
