from typing import Dict, List

from fastapi import Depends, FastAPI, APIRouter

from core.models.product import Product
from core.services.product_service import ProductService
from infra.api.schemas.product import ProductCreate, ProductUpdate
from infra.db.database import Database
from infra.repositories.product_sqlite_repository import SQLiteProductRepository
from runner.dependencies import get_product_service

router =  APIRouter()

@router.post("/", response_model=dict, status_code=201)
def create_product(
    product_data: ProductCreate,
    product_service: ProductService = Depends(get_product_service),
) -> dict[str, Product]:
    product = product_service.create_product(product_data.name, product_data.price)
    return {"product": product}


@router.get("/", response_model=dict)
def list_products(product_service: ProductService
                  = Depends(get_product_service)) -> dict[str, list[Product]]:
    products = product_service.get_all_products()
    return {"products": products}


@router.patch("/{product_id}", response_model=dict)
def update_product(
    product_id: str,
    product_data: ProductUpdate,
    product_service: ProductService = Depends(get_product_service),
) -> dict[str, Product | None]:
    product = product_service.update_product_price(product_id, product_data.price)
    return {"product": product}
