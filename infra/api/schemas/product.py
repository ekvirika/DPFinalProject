from typing import List
from uuid import UUID

from pydantic import BaseModel


class ProductCreate(BaseModel):
    name: str
    price: float


class ProductResponse(BaseModel):
    id: UUID
    name: str
    price: float


class ProductsResponse(BaseModel):
    products: List[ProductResponse]


class ProductUpdate(BaseModel):
    price: float
