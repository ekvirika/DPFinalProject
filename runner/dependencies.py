from dataclasses import dataclass

from fastapi import Depends

from core.services.receipt_service import CampaignService, ReceiptService
from infra.db.database import Database, SQLiteDatabase
from infra.repositories.campaign_sqlite_repository import SQLiteCampaignRepository
from infra.repositories.receipt_sqlite_repository import SQLiteReceiptRepository


@dataclass
class AppContainer:
    db: Database
    receipt_repository: SQLiteReceiptRepository
    receipt_service: ReceiptService
    campaign_repository: SQLiteCampaignRepository
    campaign_service: CampaignService


def create_app_container(db_path: str) -> AppContainer:
    """Create and initialize the application container."""
    # Initialize the database
    db = SQLiteDatabase(db_path)  # Use SQLiteDatabase instead of Database
    db.init_db()

    # Initialize repositories
    receipt_repository = SQLiteReceiptRepository(db)
    campaign_repository = SQLiteCampaignRepository(db)

    # Initialize services
    receipt_service = ReceiptService(
        receipt_repo=receipt_repository,
        campaign_service=CampaignService(repository=campaign_repository),
    )

    campaign_service = CampaignService(repository=campaign_repository)

    return AppContainer(
        db=db,
        receipt_repository=receipt_repository,
        receipt_service=receipt_service,
        campaign_repository=campaign_repository,
        campaign_service=campaign_service,
    )


def get_receipt_service(
    container: AppContainer = Depends(create_app_container),
) -> ReceiptService:
    """Dependency to get the ReceiptService instance."""
    return container.receipt_service


def get_campaign_repository(
    container: AppContainer = Depends(create_app_container),
) -> SQLiteCampaignRepository:
    """Dependency to get the CampaignRepository instance."""
    return container.campaign_repository


def get_campaign_service(
    container: AppContainer = Depends(create_app_container),
) -> CampaignService:
    """Dependency to get the CampaignService instance."""
    return container.campaign_service
