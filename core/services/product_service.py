from typing import List
from uuid import uuid4

from core.models.product import Product
from core.models.repositories.product_repository import ProductRepository
from infra.api.routers.product_routes import ProductCreate


class ProductService:
    def __init__(self, product_repository: ProductRepository):
        self.product_repository = product_repository

    def create_product(self, product_data: ProductCreate) -> Product:
        new_product = Product(
            id=uuid4(),
            name=product_data.name,
            price=product_data.price,
        )

        return self.product_repository.create(new_product)

    def get_all_products(self) -> List[Product]:
        return self.product_repository.get_all()

