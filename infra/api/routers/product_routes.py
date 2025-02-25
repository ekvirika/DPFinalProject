from dataclasses import dataclass
from http.client import HTTPException
from typing import Dict, List
from uuid import UUID

from fastapi import APIRouter, Depends

from core.services.product_service import ProductService
from infra.repositories.product_sqlite_repository import SQLiteProductRepository
from runner.dependencies import get_product_service


@dataclass
class ProductsCreate:
    name: str
    price: float


@dataclass
class ProductsResponse:
    id: UUID
    name: str
    price: float


@dataclass
class ProductsListResponse:
    products: list[ProductsResponse]


@dataclass
class ProductUpdate:
    price: float

class ErrorResponse:
    error: dict[str, str]





router = APIRouter(prefix="/products", tags=["Products"])


@router.post("", responses={409: {"model": ErrorResponse}}, status_code=201)
def create_product(
    product_data: ProductsCreate,
    service: ProductService = Depends(get_product_service),
) -> dict[str, ProductsResponse]:
    try:
        product = service.create_product(product_data)
        return {
            "product": ProductsResponse(
                id=product.id,
                name=product.name,
                price=product.price,
            )
        }
    except ValueError as e:
        raise HTTPException()


@router.get("", response_model=ProductsListResponse)
def get_all_products(
        service: ProductService = Depends(get_product_service)
) -> Dict[str, List[Dict[str, str]]]:
    products = service.get_all_products()
    return {
        "products": [
            {"id": str(product.id),
             "name": product.name,
             "price": str(product.price)} for product in products
        ]
    }


@router.patch(
    "/{product_id}",
    responses={404: {"model": ErrorResponse}},
    status_code=200)
def update_product(
    product_id: UUID,
    product_update: ProductUpdate,
    service: ProductService = Depends(get_product_service)
) -> dict[str, ProductsResponse]:
    try:
        service.update_product_price(product_id, product_update.price)
        return {}
    except ValueError as e:
        raise HTTPException()
