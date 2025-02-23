from fastapi import FastAPI
from api.campaigns import router as campaign_router
from infra.db.database import SQLiteDatabase


def create_app() -> FastAPI:
    app = FastAPI(title="POS System")

    # Initialize database
    db = SQLiteDatabase("pos.db")
    db.init_db()

    # Include routers
    app.include_router(campaign_router, prefix="/api/v1")

    return app


app = create_app()