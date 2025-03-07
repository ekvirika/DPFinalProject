import uuid
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from core.models.product import Product
from core.services.product_service import ProductService
from infra.api.routers.product_router import router
from runner.dependencies import get_product_service


@pytest.fixture
def mock_product_service() -> Mock:
    return Mock(spec=ProductService)


@pytest.fixture
def client(mock_product_service: Mock) -> TestClient:
    """Test client with mocked dependencies."""
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router, prefix="/products")

    # Override dependency
    app.dependency_overrides = {get_product_service: lambda: mock_product_service}

    return TestClient(app)


def test_create_product(client: TestClient, mock_product_service: Mock) -> None:
    """Test creating a product via the API."""
    # Arrange
    product_id = uuid.uuid4()
    mock_product_service.create_product.return_value = Product(
        id=product_id, name="Test Product", price=10.99
    )

    # Act
    response = client.post("/products/", json={"name": "Test Product", "price": 10.99})

    # Assert
    assert response.status_code == 201
    assert response.json() == {
        "product": {"id": str(product_id), "name": "Test Product", "price": 10.99}
    }
    mock_product_service.create_product.assert_called_once_with("Test Product", 10.99)


def test_list_products(client: TestClient, mock_product_service: Mock) -> None:
    """Test listing all products via the API."""
    # Arrange
    product_1 = Product(id=uuid.uuid4(), name="Product 1", price=10.99)
    product_2 = Product(id=uuid.uuid4(), name="Product 2", price=20.99)
    mock_product_service.get_all_products.return_value = [product_1, product_2]

    # Act
    response = client.get("/products/")

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "products": [
            {"id": str(product_1.id), "name": product_1.name, "price": product_1.price},
            {"id": str(product_2.id), "name": product_2.name, "price": product_2.price},
        ]
    }
    mock_product_service.get_all_products.assert_called_once()


def test_update_product(client: TestClient, mock_product_service: Mock) -> None:
    """Test updating a product's price via the API."""
    # Arrange
    product_id = uuid.uuid4()
    updated_product = Product(id=product_id, name="Test Product", price=15.99)
    mock_product_service.update_product_price.return_value = updated_product

    # Act
    response = client.patch(f"/products/{product_id}", json={"price": 15.99})

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "product": {"id": str(product_id), "name": "Test Product", "price": 15.99}
    }
    mock_product_service.update_product_price.assert_called_once_with(product_id, 15.99)


def test_update_product_not_found(
    client: TestClient, mock_product_service: Mock
) -> None:
    """Test updating a product that doesn't exist."""
    # Arrange
    product_id = uuid.uuid4()
    mock_product_service.update_product_price.return_value = None

    # Act
    response = client.patch(f"/products/{product_id}", json={"price": 15.99})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"product": None}
