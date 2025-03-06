from typing import Any, Optional, cast
import uuid
from unittest.mock import Mock

import pytest

from core.models.product import Product
from core.models.repositories.product_repository import ProductRepository
from core.services.product_service import ProductService


@pytest.fixture
def mock_product_repository() -> Mock:
    """Return a mock product repository."""
    return Mock(spec=ProductRepository)


@pytest.fixture
def product_service(mock_product_repository: Mock) -> ProductService:
    """Return a ProductService with a mock repository."""
    return ProductService(mock_product_repository)


def test_create_product(
        product_service: ProductService, mock_product_repository: Mock
) -> None:
    """Test creating a product through the service layer."""
    # Arrange
    product_id = uuid.uuid4()
    expected_product = Product(id=product_id, name="Test Product", price=10.99)
    mock_product_repository.create.return_value = expected_product

    # Act
    result = product_service.create_product("Test Product", 10.99)

    # Assert
    assert result == expected_product
    mock_product_repository.create.assert_called_once_with("Test Product", 10.99)


def test_get_product(
        product_service: ProductService, mock_product_repository: Mock
) -> None:
    """Test retrieving a product by ID through the service layer."""
    # Arrange
    product_id = uuid.uuid4()
    expected_product = Product(id=product_id, name="Test Product", price=10.99)
    mock_product_repository.get_by_id.return_value = expected_product

    # Act
    result = product_service.get_product(product_id)

    # Assert
    assert result == expected_product
    mock_product_repository.get_by_id.assert_called_once_with(product_id)


def test_get_product_not_found(
        product_service: ProductService, mock_product_repository: Mock
) -> None:
    """Test retrieving a non-existent product."""
    # Arrange
    product_id = uuid.uuid4()
    mock_product_repository.get_by_id.return_value = None

    # Act
    result = product_service.get_product(product_id)

    # Assert
    assert result is None
    mock_product_repository.get_by_id.assert_called_once_with(product_id)


def test_get_all_products(
        product_service: ProductService, mock_product_repository: Mock
) -> None:
    """Test retrieving all products through the service layer."""
    # Arrange
    product_1 = Product(id=uuid.uuid4(), name="Product 1", price=10.99)
    product_2 = Product(id=uuid.uuid4(), name="Product 2", price=20.99)
    expected_products = [product_1, product_2]
    mock_product_repository.get_all.return_value = expected_products

    # Act
    result = product_service.get_all_products()

    # Assert
    assert result == expected_products
    mock_product_repository.get_all.assert_called_once()


def test_update_product_price(
        product_service: ProductService, mock_product_repository: Mock
) -> None:
    """Test updating a product's price through the service layer."""
    # Arrange
    product_id = uuid.uuid4()
    updated_product = Product(id=product_id, name="Test Product", price=15.99)
    mock_product_repository.update_price.return_value = updated_product

    # Act
    result = product_service.update_product_price(product_id, 15.99)

    # Assert
    assert result == updated_product
    mock_product_repository.update_price.assert_called_once_with(product_id, 15.99)


def test_update_product_price_not_found(
        product_service: ProductService, mock_product_repository: Mock
) -> None:
    """Test updating the price of a non-existent product."""
    # Arrange
    product_id = uuid.uuid4()
    mock_product_repository.update_price.return_value = None

    # Act
    result = product_service.update_product_price(product_id, 15.99)

    # Assert
    assert result is None
    mock_product_repository.update_price.assert_called_once_with(product_id, 15.99)