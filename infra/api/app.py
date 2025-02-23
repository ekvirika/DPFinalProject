from fastapi import FastAPI
from core.services.receipt_service import ReceiptService
from infra.api.routers.receipt_router import ReceiptRouter
from infra.repositories.receipt_sqlite_repository import SQLiteReceiptRepository

app = FastAPI()

# Initialize dependencies
receipt_repo = SQLiteReceiptRepository("pos.db")
receipt_service = ReceiptService(
    receipt_repo=receipt_repo,
    exchange_service=exchange_service,
    campaign_service=campaign_service
)

# Initialize and include routers
receipt_router = ReceiptRouter(receipt_service)
app.include_router(receipt_router.router)