from functools import lru_cache

from fastapi import FastAPI

from infra.api.routers.receipt_router import router as receipt_router
from runner.dependencies import AppContainer, create_app_container

app = FastAPI()


@lru_cache()
def get_app_container() -> AppContainer:
    """Create and cache the application container."""
    return create_app_container("pos.db")


# Include the router in the app
app.include_router(receipt_router)
