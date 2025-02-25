import uuid
from dataclasses import dataclass, field


@dataclass
class Product:
    name: str
    price: float
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
