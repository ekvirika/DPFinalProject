from typing import List, Optional
from uuid import UUID

from core.models.product import Product
from core.models.repositories.product_repository import ProductRepository
from infra.db.database import Database


class SQLiteReceiptRepository(ProductRepository):
    def __init__(self, database: Database):
        self.database = database

    def create(self, product: Product) -> Product:
        with self.database.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO products (id, name, price)
                VALUES (?, ?, ?)
                """,
                (Product.id, product.name, product.price),
            )
            return Product(
                id=product.id,
                name=product.name,
                price=product.price,
            )

    def get_by_id(self, product_id: UUID) -> Optional[Product]:
        pass

    def get_all(self) -> List[Product]:
        pass

    def update(self, product_id: UUID, product: Product) -> Optional[Product]:
        pass
