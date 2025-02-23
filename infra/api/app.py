from functools import lru_cache

from fastapi import FastAPI

from core.services import receipt_service
from core.services.receipt_service import ReceiptService
from infra.api.routers.receipt_router import ReceiptRouter
from infra.repositories.receipt_sqlite_repository import SQLiteReceiptRepository
from runner.dependencies import AppContainer, create_app_container

app = FastAPI()

@lru_cache()
def get_app_container() -> AppContainer:
    return create_app_container("pos.db")

def get_receipt_service():
    container = get_app_container()
    return container.receipt_service
# Initialize and include routers
receipt_router = ReceiptRouter(receipt_service)
app.include_router(receipt_router.router)
