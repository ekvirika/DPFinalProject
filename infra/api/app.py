from functools import lru_cache

from fastapi import FastAPI

from infra.api.routers.campaign_router import router as campaign_router
from infra.api.routers.product_router import router as product_router
from infra.api.routers.receipt_router import router as receipt_router
from infra.api.routers.shift_router import router as shift_router
from infra.api.routers.report_router import router as report_router
from runner.dependencies import AppContainer, get_app_container

app = FastAPI()


@lru_cache()
def create_app_container() -> AppContainer:
    """Create and cache the application container."""
    return get_app_container("pos.db")


# Include routers with prefixes and tags
app.include_router(receipt_router, prefix="/receipts", tags=["Receipts"])
app.include_router(campaign_router, prefix="/campaigns", tags=["Campaigns"])
app.include_router(product_router, prefix="/products", tags=["Products"])
app.include_router(shift_router, prefix="/shifts", tags=["Shifts"])
app.include_router(shift_router, prefix="/reports", tags=["Reports"])
