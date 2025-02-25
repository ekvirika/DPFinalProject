from fastapi import FastAPI, Depends, HTTPException
from infra.api.schemas.product import ProductCreate, ProductUpdate
from infra.db.database import Database
from infra.repositories.product_sqlite_repository import SQLiteProductRepository
from core.services.product_service import ProductService


app = FastAPI(title="Products")


def get_product_service() -> ProductService:
    db = Database()
    product_repo = SQLiteProductRepository(db)
    return ProductService(product_repo)


@app.post("/products", response_model=dict, status_code=201)
def create_product(product_data: ProductCreate, product_service: ProductService = Depends(get_product_service)):
    product = product_service.create_product(product_data.name, product_data.price)
    return {"product": product}


@app.get("/products", response_model=dict)
def list_products(product_service: ProductService = Depends(get_product_service)):
    products = product_service.get_all_products()
    return {"products": products}


@app.patch("/products/{product_id}", response_model=dict)
def update_product(product_id: str, product_data: ProductUpdate, product_service: ProductService = Depends(get_product_service)):
    product = product_service.update_product_price(product_id, product_data.price)
    return {"product": product}
