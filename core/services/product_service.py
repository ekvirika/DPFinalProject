from typing import List, Optional
from uuid import UUID

from core.models.product import Product
from core.models.repositories.product_repository import ProductRepository


class ProductService:
    def __init__(self, product_repository: ProductRepository):
        self.product_repository = product_repository

    def create_product(self, name: str, price: float) -> Product:
        return self.product_repository.create(name, price)

    def get_product(self, product_id: UUID) -> Optional[Product]:
        return self.product_repository.get_by_id(product_id)

    def get_all_products(self) -> List[Product]:
        return self.product_repository.get_all()

    def update_product_price(self, product_id: UUID, price: float) -> Optional[Product]:
        return self.product_repository.update_price(product_id, price)
