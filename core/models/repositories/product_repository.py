from typing import List, Optional, Protocol
from uuid import UUID

from pydantic.v1 import UUID3

from core.models.product import Product


class ProductRepository(Protocol):
    def create(self, name: str, price: float) -> Product:
        pass

    def get_by_id(self, product_id: UUID) -> Optional[Product]:
        pass

    def get_all(self) -> List[Product]:
        pass

    def update_price(self, product_id: UUID, price: float) -> Optional[Product]:
        pass
