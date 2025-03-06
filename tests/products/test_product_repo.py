from typing import Any, Dict, List, cast
import sqlite3
import uuid
from unittest.mock import Mock, patch

import pytest

from core.models.errors import ProductNotFoundError
from core.models.product import Product
from infra.db.database import Database
from infra.repositories.product_sqlite_repository import SQLiteProductRepository


class MockConnection:
    """Mock SQLite connection for testing."""

    def __init__(self, mock_cursor: Mock) -> None:
        self.mock_cursor = mock_cursor
        self.committed = False

    def cursor(self) -> Mock:
        return self.mock_cursor

    def commit(self) -> None:
        self.committed = True

    def __enter__(self) -> 'MockConnection':
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        pass


@pytest.fixture
def mock_cursor() -> Mock:
    """Mock cursor for database operations."""
    return Mock()


@pytest.fixture
def mock_db(mock_cursor: Mock) -> Mock:
    """Mock database with connection that returns mock cursor."""
    mock_connection = MockConnection(mock_cursor)
    mock_db = Mock(spec=Database)
    mock_db.get_connection.return_value = mock_connection
    return mock_db


@pytest.fixture
def product_repository(mock_db: Mock) -> SQLiteProductRepository:
    """Repository with mocked database dependency."""
    return SQLiteProductRepository(mock_db)


def test_create_product(
        product_repository: SQLiteProductRepository, mock_db: Mock, mock_cursor: Mock
) -> None:
    """Test creating a product in the repository."""
    # Arrange
    name = "Test Product"
    price = 10.99

    # Act
    with patch('uuid.UUID', return_value=uuid.UUID('00000000-0000-0000-0000-000000000001')):
        product = product_repository.create(name, price)

    # Assert
    assert product.id == uuid.UUID('00000000-0000-0000-0000-000000000001')
    assert product.name == name
    assert product.price == price

    mock_cursor.execute.assert_called_once_with(
        "INSERT INTO products (id, name, price) VALUES (?, ?, ?)",
        ('00000000-0000-0000-0000-000000000001', name, price)
    )
    conn = cast(MockConnection, mock_db.get_connection())
    assert conn.committed is True


def test_get_by_id_found(
        product_repository: SQLiteProductRepository, mock_db: Mock, mock_cursor: Mock
) -> None:
    """Test retrieving an existing product by ID."""
    # Arrange
    product_id = uuid.UUID('00000000-0000-0000-0000-000000000001')
    mock_cursor.fetchone.return_value = {
        "id": product_id,
        "name": "Test Product",
        "price": 10.99
    }

    # Act
    product = product_repository.get_by_id(product_id)

    # Assert
    assert product.id == product_id
    assert product.name == "Test Product"
    assert product.price == 10.99

    mock_cursor.execute.assert_called_once_with(
        "SELECT * FROM products WHERE id = ?",
        (str(product_id),)
    )


def test_get_all(
        product_repository: SQLiteProductRepository, mock_db: Mock, mock_cursor: Mock
) -> None:
    """Test retrieving all products."""
    # Arrange
    product_id_1 = uuid.UUID('00000000-0000-0000-0000-000000000001')
    product_id_2 = uuid.UUID('00000000-0000-0000-0000-000000000002')

    mock_cursor.fetchall.return_value = [
        {"id": product_id_1, "name": "Product 1", "price": 10.99},
        {"id": product_id_2, "name": "Product 2", "price": 20.99}
    ]

    # Act
    products = product_repository.get_all()

    # Assert
    assert len(products) == 2
    assert products[0].id == product_id_1
    assert products[0].name == "Product 1"
    assert products[0].price == 10.99
    assert products[1].id == product_id_2
    assert products[1].name == "Product 2"
    assert products[1].price == 20.99

    mock_cursor.execute.assert_called_once_with("SELECT * FROM products")


def test_update_price_success(
        product_repository: SQLiteProductRepository, mock_db: Mock, mock_cursor: Mock
) -> None:
    """Test successfully updating a product's price."""
    # Arrange
    product_id = uuid.UUID('00000000-0000-0000-0000-000000000001')
    mock_cursor.rowcount = 1

    # Mock the get_by_id method to return a product after update
    with patch.object(
            SQLiteProductRepository,
            'get_by_id',
            return_value=Product(id=product_id, name="Test Product", price=15.99)
    ):
        # Act
        product = product_repository.update_price(product_id, 15.99)

    # Assert
    assert product.id == product_id
    assert product.name == "Test Product"
    assert product.price == 15.99

    mock_cursor.execute.assert_called_once_with(
        "UPDATE products SET price = ? WHERE id = ?",
        (15.99, str(product_id))
    )
    conn = cast(MockConnection, mock_db.get_connection())
    assert conn.committed is True

