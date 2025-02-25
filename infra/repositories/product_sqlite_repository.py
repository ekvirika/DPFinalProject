from typing import Optional, List

from core.models.product import Product
from infra.db.database import Database


class SQLiteProductRepository:
    def __init__(self, db: Database):
        self.db = db

    def create(self, name: str, price: float) -> Product:
        product = Product(name=name, price=price)

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO products (id, name, price) VALUES (?, ?, ?)",
                (product.id, product.name, product.price)
            )
            conn.commit()

        return product

    def get_by_id(self, product_id: str) -> Optional[Product]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
            row = cursor.fetchone()

            if row:
                return Product(
                    id=row["id"],
                    name=row["name"],
                    price=row["price"]
                )

            return None

    def get_all(self) -> List[Product]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products")
            rows = cursor.fetchall()

            return [
                Product(
                    id=row["id"],
                    name=row["name"],
                    price=row["price"]
                )
                for row in rows
            ]

    def update_price(self, product_id: str, price: float) -> Optional[Product]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE products SET price = ? WHERE id = ?",
                (price, product_id)
            )
            conn.commit()

            if cursor.rowcount > 0:
                return self.get_by_id(product_id)

            return None
