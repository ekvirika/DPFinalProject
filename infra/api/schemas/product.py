from typing import List

from pydantic import BaseModel


class ProductCreate(BaseModel):
    name: str
    price: float


class ProductResponse(BaseModel):
    id: str
    name: str
    price: float


class ProductsResponse(BaseModel):
    products: List[ProductResponse]


class ProductUpdate(BaseModel):
    price: float
