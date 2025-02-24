from functools import lru_cache
from fastapi import FastAPI

from infra.api.routers.receipt_router import router as receipt_router
from infra.api.routers.product_routes import router as product_router
from infra.api.routers.campaign_routes import router as campaign_router
from runner.dependencies import AppContainer, create_app_container

app = FastAPI()

@lru_cache()
def get_app_container() -> AppContainer:
    """Create and cache the application container."""
    return create_app_container("pos.db")

# Include routers with prefixes and tags
app.include_router(receipt_router, prefix="/receipts", tags=["Receipts"])
app.include_router(campaign_router, prefix="/campaigns", tags=["Campaigns"])
app.include_router(product_router, prefix="/products", tags=["Products"])
