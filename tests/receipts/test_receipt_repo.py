from typing import Any, Dict, List, cast
import uuid
from unittest.mock import Mock, MagicMock, patch

import pytest

from core.models.errors import ReceiptNotFoundError
from core.models.receipt import (
    Currency,
    Discount,
    Payment,
    PaymentStatus,
    Receipt,
    ReceiptItem,
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


def test_create_receipt(receipt_repository: SQLiteReceiptRepository, mock_db: Mock) -> None:
    """Test creating a new receipt."""
    # Arrange
    shift_id = uuid.uuid4()

    # Set up the mock connection and cursor
    mock_connection = mock_db.get_connection.return_value.__enter__.return_value
    mock_cursor = mock_connection.cursor.return_value

    # Act
    with patch('uuid.UUID', return_value=uuid.UUID('00000000-0000-0000-0000-000000000001')):
        receipt = receipt_repository.create(shift_id)

    # Assert
    assert receipt.id == uuid.UUID('00000000-0000-0000-0000-000000000001')
    assert receipt.shift_id == shift_id
    assert receipt.status == ReceiptStatus.OPEN
    assert receipt.products == []
    assert receipt.payments == []
    assert receipt.subtotal == 0
    assert receipt.discount_amount == 0
    assert receipt.total == 0

    # Check DB calls
    mock_cursor.execute.assert_called_once_with(
        """
                INSERT INTO receipts (id, shift_id, status, subtotal, 
                discount_amount, total)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
        (
            '00000000-0000-0000-0000-000000000001',
            str(shift_id),
            ReceiptStatus.OPEN.value,
            0,
            0,
            0,
        ),
    )
    mock_connection.commit.assert_called_once()


def test_get_receipt(receipt_repository: SQLiteReceiptRepository, mock_db: Mock) -> None:
    """Test getting a receipt by ID."""
    # Arrange
    receipt_id = uuid.uuid4()
    shift_id = uuid.uuid4()

    # Set up the mock cursor for fetching data
    mock_cursor = mock_db.get_connection.return_value.__enter__.return_value.cursor.return_value

    # Mock receipt basic info
    receipt_row = {
        "id": str(receipt_id),
        "shift_id": str(shift_id),
        "status": ReceiptStatus.OPEN.value,
        "subtotal": 100.0,
        "discount_amount": 20.0,
        "total": 80.0,
    }

    # Mock receipt items
    product_id_1 = uuid.uuid4()
    product_id_2 = uuid.uuid4()

    item_rows = [
        {
            "id": str(uuid.uuid4()),
            "receipt_id": str(receipt_id),
            "product_id": str(product_id_1),
            "quantity": 2,
            "unit_price": 30.0,
            "total_price": 60.0,
            "final_price": 50.0,
        },
        {
            "id": str(uuid.uuid4()),
            "receipt_id": str(receipt_id),
            "product_id": str(product_id_2),
            "quantity": 1,
            "unit_price": 40.0,
            "total_price": 40.0,
            "final_price": 30.0,
        },
    ]

    # Mock discount data
    campaign_id_1 = uuid.uuid4()
    campaign_id_2 = uuid.uuid4()

    discount_rows_1 = [
        {
            "campaign_id": str(campaign_id_1),
            "campaign_name": "Summer Sale",
            "discount_amount": 10.0,
        }
    ]

    discount_rows_2 = [
        {
            "campaign_id": str(campaign_id_2),
            "campaign_name": "Loyalty Discount",
            "discount_amount": 10.0,
        }
    ]

    # Mock payment data
    payment_id = uuid.uuid4()
    payment_rows = [
        {
            "id": str(payment_id),
            "receipt_id": str(receipt_id),
            "payment_amount": 80.0,
            "currency": Currency.GEL.value,
            "total_in_gel": 80.0,
            "exchange_rate": 1.0,
            "status": PaymentStatus.COMPLETED.value,
        }
    ]

    # Set up mock cursor to return the expected data
    mock_cursor.fetchone.side_effect = [receipt_row]
    mock_cursor.fetchall.side_effect = [item_rows, discount_rows_1, discount_rows_2, payment_rows]

    # Act
    receipt = receipt_repository.get(receipt_id)

    # Assert
    assert receipt.id == receipt_id
    assert receipt.shift_id == shift_id
    assert receipt.status == ReceiptStatus.OPEN
    assert receipt.subtotal == 100.0
    assert receipt.discount_amount == 20.0
    assert receipt.total == 80.0

    # Check items
    assert len(receipt.products) == 2
    assert receipt.products[0].product_id == product_id_1
    assert receipt.products[0].quantity == 2
    assert receipt.products[0].unit_price == 30.0
    assert receipt.products[0].total_price == 60.0
    assert receipt.products[0].final_price == 50.0

    assert receipt.products[1].product_id == product_id_2
    assert receipt.products[1].quantity == 1
    assert receipt.products[1].unit_price == 40.0
    assert receipt.products[1].total_price == 40.0
    assert receipt.products[1].final_price == 30.0

    # Check payments
    assert len(receipt.payments) == 1
    assert receipt.payments[0].id == payment_id
    assert receipt.payments[0].receipt_id == receipt_id
    assert receipt.payments[0].payment_amount == 80.0
    assert receipt.payments[0].currency == Currency.GEL
    assert receipt.payments[0].total_in_gel == 80.0
    assert receipt.payments[0].exchange_rate == 1.0
    assert receipt.payments[0].status == PaymentStatus.COMPLETED

    # Check DB calls
    mock_cursor.execute.assert_any_call(
        "SELECT * FROM receipts WHERE id = ?",
        (str(receipt_id),),
    )
    mock_cursor.execute.assert_any_call(
        "SELECT * FROM receipt_items WHERE receipt_id = ?",
        (str(receipt_id),),
    )
    mock_cursor.execute.assert_any_call(
        "SELECT * FROM payments WHERE receipt_id = ?",
        (str(receipt_id),),
    )


def test_get_receipt_not_found(receipt_repository: SQLiteReceiptRepository, mock_db: Mock) -> None:
    """Test getting a non-existent receipt."""
    # Arrange
    receipt_id = uuid.uuid4()

    # Set up the mock cursor to return no data
    mock_cursor = mock_db.get_connection.return_value.__enter__.return_value.cursor.return_value
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


def test_update_status(receipt_repository: SQLiteReceiptRepository, mock_db: Mock) -> None:
    """Test updating the status of a receipt."""
    # Arrange
    receipt_id = uuid.uuid4()
    new_status = ReceiptStatus.CLOSED

    # Mock the get method to return a receipt after update
    with patch.object(
            SQLiteReceiptRepository,
            'get',
            return_value=Receipt(
                id=receipt_id,
                shift_id=uuid.uuid4(),
                status=new_status
            )
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


def test_add_payment(receipt_repository: SQLiteReceiptRepository, mock_db: Mock) -> None:
    """Test adding a payment to a receipt."""
    # Arrange
    receipt_id = uuid.uuid4()
    payment_id = uuid.uuid4()
    payment = Payment(
        id=payment_id,
        receipt_id=receipt_id,
        payment_amount=80.0,
        currency=Currency.GEL,
        total_in_gel=80.0,
        exchange_rate=1.0,
        status=PaymentStatus.COMPLETED,
    )

    # Mock the get method to return a receipt after adding payment
    with patch.object(
            SQLiteReceiptRepository,
            'get',
            return_value=Receipt(
                id=receipt_id,
                shift_id=uuid.uuid4(),
                payments=[payment]
            )
    ):
        # Act
        updated_receipt = receipt_repository.add_payment(receipt_id, payment)

    # Assert
    assert updated_receipt.id == receipt_id
    assert len(updated_receipt.payments) == 1
    assert updated_receipt.payments[0].id == payment_id

    # Check DB calls
    mock_db.get_connection.return_value.__enter__.return_value.cursor.return_value.execute.assert_called_once_with(
        """
                INSERT INTO payments
                (id, receipt_id, payment_amount, currency, total_in_gel,
                 exchange_rate, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
        (
            str(payment_id),
            str(receipt_id),
            payment.payment_amount,
            payment.currency.value,
            payment.total_in_gel,
            payment.exchange_rate,
            payment.status.value,
        ),
    )
    mock_db.get_connection.return_value.__enter__.return_value.commit.assert_called_once()


def test_get_receipts_by_shift(receipt_repository: SQLiteReceiptRepository, mock_db: Mock) -> None:
    """Test getting all receipts for a shift."""
    # Arrange
    shift_id = uuid.uuid4()
    receipt_id_1 = uuid.uuid4()
    receipt_id_2 = uuid.uuid4()

    # Set up the mock cursor
    mock_cursor = mock_db.get_connection.return_value.__enter__.return_value.cursor.return_value
    mock_cursor.fetchall.return_value = [
        {"id": str(receipt_id_1)},
        {"id": str(receipt_id_2)},
    ]

    # Mock receipt objects to be returned by get method
    receipt_1 = Receipt(id=receipt_id_1, shift_id=shift_id, status=ReceiptStatus.OPEN)
    receipt_2 = Receipt(id=receipt_id_2, shift_id=shift_id, status=ReceiptStatus.CLOSED)

    # Set up mock for the get method
    with patch.object(
            SQLiteReceiptRepository,
            'get',
            side_effect=[receipt_1, receipt_2]
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


def test_update_receipt(receipt_repository: SQLiteReceiptRepository, mock_db: Mock) -> None:
    """Test updating a receipt."""
    # Arrange
    receipt_id = uuid.uuid4()
    shift_id = uuid.uuid4()
    product_id = uuid.uuid4()

    # Create a receipt to update
    updated_receipt = Receipt(
        id=receipt_id,
        shift_id=shift_id,
        status=ReceiptStatus.OPEN,
        subtotal=30.0,
        discount_amount=5.0,
        total=25.0,
        products=[
            ReceiptItem(
                product_id=product_id,
                quantity=1,
                unit_price=30.0,
                discounts=[
                    Discount(
                        campaign_id=uuid.uuid4(),
                        campaign_name="Test Discount",
                        discount_amount=5.0
                    )
                ]
            )
        ]
    )

    # Set up the mock cursor
    mock_cursor = mock_db.get_connection.return_value.__enter__.return_value.cursor.return_value

    # Mock the fetch data for the verification query
    receipt_data = [
        str(receipt_id), str(shift_id), ReceiptStatus.OPEN.value, 30.0, 5.0, 25.0
    ]
    items_data = [
        [str(uuid.uuid4()), str(product_id), 1, 30.0]
    ]
    discount_data = [
        [str(uuid.uuid4()), "Test Discount", 5.0]
    ]
    payment_data = []

    mock_cursor.fetchone.side_effect = [receipt_data, None]
    mock_cursor.fetchall.side_effect = [items_data, discount_data, payment_data]

    # Act
    with patch.object(
            SQLiteReceiptRepository,
            'get',
            return_value=updated_receipt
    ):
        result = receipt_repository.update(receipt_id, updated_receipt)

    # Assert
    assert result.id == receipt_id
    assert result.shift_id == shift_id
    assert result.subtotal == 30.0
    assert result.discount_amount == 5.0
    assert result.total == 25.0

    # Check DB calls for updating receipt
    mock_cursor.execute.assert_any_call(
        """UPDATE receipts 
                   SET subtotal = ?, discount_amount = ?, total = ?
                   WHERE id = ?""",
        (
            updated_receipt.subtotal,
            updated_receipt.discount_amount,
            updated_receipt.total,
            str(receipt_id),
        ),
    )
    # Check calls for deleting existing items and discounts
    mock_cursor.execute.assert_any_call(
        "DELETE FROM receipt_items WHERE receipt_id = ?", (str(receipt_id),)
    )
    mock_cursor.execute.assert_any_call(
        "DELETE FROM receipt_item_discounts WHERE receipt_item_id IN "
        "(SELECT id FROM receipt_items WHERE receipt_id = ?)",
        (str(receipt_id),),
    )