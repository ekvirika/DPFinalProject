from dataclasses import dataclass
from typing import Generator

from fastapi import Depends

from core.services.receipt_service import ReceiptService, CampaignService
from infra.db.database import Database, SQLiteDatabase  # Import SQLiteDatabase
from infra.repositories.campaign_sqlite_repository import SQLiteCampaignRepository
from infra.repositories.receipt_sqlite_repository import SQLiteReceiptRepository


@dataclass
class AppContainer:
    db: Database
    receipt_repository: SQLiteReceiptRepository
    receipt_service: ReceiptService


def create_app_container(db_path: str) -> AppContainer:
    """Create and initialize the application container."""
    # Initialize database
    db = SQLiteDatabase(db_path)  # Use SQLiteDatabase instead of Database
    db.init_db()

    # Initialize repositories
    receipt_repository = SQLiteReceiptRepository(db)

    # Initialize services
    receipt_service = ReceiptService(receipt_repo=receipt_repository)  # Use receipt_repo

    return AppContainer(
        db=db,
        receipt_repository=receipt_repository,
        receipt_service=receipt_service
    )


def get_receipt_service(container: AppContainer = Depends(create_app_container)) -> ReceiptService:
    """Dependency to get the ReceiptService instance."""
    return container.receipt_service

def get_campaign_repository() -> SQLiteCampaignRepository:
    return SQLiteCampaignRepository("pos.db")

def get_campaign_service() -> Generator[    CampaignService, None, None]:
    repository = get_campaign_repository()
    service = CampaignService(repository)
    yield service