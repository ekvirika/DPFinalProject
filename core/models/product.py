from uuid import UUID
from dataclasses import dataclass, field


@dataclass
class Product:
    id: UUID
    name: str
    price: float
