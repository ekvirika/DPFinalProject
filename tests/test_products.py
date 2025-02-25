import pytest
from fastapi.testclient import TestClient
from uuid import uuid4


# ------------------------ CREATE PRODUCT ------------------------
def test_create_product_success(client: TestClient):
    response = client.post(
        "/products",
        json={"name": "Apple", "price": 1.5}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["product"]["name"] == "Apple"
    assert float(data["product"]["price"]) == 1.5


def test_create_product_conflict(client: TestClient):
    """Assume product with name already exists."""
    client.post("/products", json={"name": "Banana", "price": 1.0})
    response = client.post("/products", json={"name": "Banana", "price": 1.0})
    assert response.status_code == 409


# ------------------------ LIST ALL PRODUCTS ------------------------
def test_get_all_products(client: TestClient):
    response = client.get("/products")
    assert response.status_code == 200
    data = response.json()
    assert "products" in data
    assert isinstance(data["products"], list)


# ------------------------ UPDATE PRODUCT PRICE ------------------------
def test_update_product_price_success(client: TestClient):
    create_response = client.post("/products", json={"name": "Milk", "price": 2.5})
    product_id = create_response.json()["product"]["id"]

    update_response = client.patch(
        f"/products/{product_id}",
        json={"price": 3.0}
    )
    assert update_response.status_code == 200


def test_update_product_price_not_found(client: TestClient):
    fake_id = str(uuid4())
    response = client.patch(
        f"/products/{fake_id}",
        json={"price": 4.0}
    )
    assert response.status_code == 404


# ------------------------ VALIDATION ERRORS ------------------------
def test_create_product_validation_error(client: TestClient):
    """Invalid data should return 422 Unprocessable Entity"""
    response = client.post(
        "/products",
        json={"name": "", "price": -5.0}
    )
    assert response.status_code == 422
