from abc import abstractmethod
from typing import List, Optional, Protocol
from uuid import UUID

from core.models.product import Product


class ProductRepository(Protocol):
    @abstractmethod
    def create(self, product: Product) -> Product:
        pass

    @abstractmethod
    def get_by_id(self, product_id: UUID) -> Optional[Product]:
        pass

    @abstractmethod
    def get_all(self) -> List[Product]:
        pass

    @abstractmethod
    def update(self, product_id: UUID, product: Product) -> Optional[Product]:
        pass
