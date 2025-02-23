from dataclasses import dataclass
from uuid import UUID

from fastapi import APIRouter


@dataclass
class ProductCreate:
    name: str
    price: float
    currency: str


@dataclass
class ProductResponse:
    id: UUID
    name: str
    price: float
    currency: str


router = APIRouter(prefix="/products", tags=["Products"])
