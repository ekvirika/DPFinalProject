from typing import List, Optional, Protocol
from uuid import UUID

from core.models.product import Product


class ProductRepository(Protocol):
    def create(self, product: Product) -> Product:
        pass

    def get_by_id(self, id: UUID) -> Optional[Product]:
        pass

    def get_all(self) -> List[Product]:
        pass

    def update(self, product_id: UUID, product: Product) -> Optional[Product]:
        pass
