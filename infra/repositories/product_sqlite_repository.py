from typing import List, Optional
from uuid import UUID

from core.models.product import Product
from core.models.repositories.product_repository import ProductRepository
from infra.db.database import Database


class SQLiteProductRepository(ProductRepository):
    def __init__(self, database: Database):
        self.database = database

    def create(self, product: Product) -> Product:
        with self.database.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO products (id, name, price)
                VALUES (?, ?, ?)
                """,
                (str(product.id),
                 product.name,
                 product.price),
            )
            return Product(
                id=product.id,
                name=product.name,
                price=product.price,
            )

    def get_by_id(self, product_id: UUID) -> Optional[Product]:
        with self.database.get_connection() as conn:
            result = conn.execute(
                'SELECT * FROM products WHERE id = ?', (str(product_id),)
            ).fetchone()

            if result:
                return Product(
                    id=result[0],
                    name=result[2],
                    price=float(result[4]))
        return None

    def get_all(self) -> List[Product]:
        with self.database.get_connection() as conn:
            result = conn.execute(
                'SELECT * FROM products'
            ).fetchall()
        return [
            Product(
                id=UUID(row['id']),
                name=row['name'],
                price=float(row['price'])
            )
            for row in result
        ]

    def update(self, product_id: UUID, product: Product) -> Optional[Product]:
        with self.database.get_connection() as conn:
            result = conn.execute(
                'UPDATE products SET price = ? WHERE id = ?',
                (float(product.price), str(product_id))
            )
            conn.commit()
            if result:
                return product
        return None
