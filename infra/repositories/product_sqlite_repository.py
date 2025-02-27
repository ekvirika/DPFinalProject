from typing import List, Optional
from uuid import UUID, uuid4

from core.models.product import Product
from core.models.repositories.product_repository import ProductRepository
from infra.db.database import Database
from core.models.errors import ProductNotFoundError


class SQLiteProductRepository(ProductRepository):
    def __init__(self, db: Database):
        self.db = db

    def create(self, name: str, price: float) -> Product:
        product = Product(id = uuid4(), name=name, price=price)

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO products (id, name, price) VALUES (?, ?, ?)",
                (str(product.id), product.name, product.price),
            )
            conn.commit()

        return product

    def get_by_id(self, product_id: UUID) -> Optional[Product]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products WHERE id = ?", (str(product_id),))
            row = cursor.fetchone()

            if row is None:
                raise ProductNotFoundError(str(product_id))
            return Product(id=row["id"], name=row["name"], price=row["price"])

    def get_all(self) -> List[Product]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products")
            rows = cursor.fetchall()

            return [
                Product(id=row["id"], name=row["name"], price=row["price"])
                for row in rows
            ]

    def update_price(self, product_id: UUID, price: float) -> Optional[Product]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE products SET price = ? WHERE id = ?", (price, str(product_id))
            )
            conn.commit()

            if cursor.rowcount <= 0:
                raise ProductNotFoundError(str(product_id))
            return self.get_by_id(product_id)
