from dataclasses import dataclass
from core.services.receipt_service import CampaignService, ReceiptService
from core.services.product_service import ProductService
from infra.db.database import Database, SQLiteDatabase
from infra.repositories.campaign_sqlite_repository import SQLiteCampaignRepository
from infra.repositories.receipt_sqlite_repository import SQLiteReceiptRepository
from infra.repositories.product_sqlite_repository import SQLiteProductRepository  # Fixed import

@dataclass
class AppContainer:
    db: Database
    receipt_repository: SQLiteReceiptRepository
    receipt_service: ReceiptService
    campaign_repository: SQLiteCampaignRepository
    campaign_service: CampaignService
    product_repository: SQLiteProductRepository
    product_service: ProductService

def create_app_container(db_path: str) -> AppContainer:
    """Create and initialize the application container."""
    # Initialize the database
    db = SQLiteDatabase(db_path)
    db.init_db()

    # Initialize repositories
    receipt_repository = SQLiteReceiptRepository(db)
    campaign_repository = SQLiteCampaignRepository(db)
    product_repository = SQLiteProductRepository(db)

    # Initialize services
    campaign_service = CampaignService(repository=campaign_repository)
    receipt_service = ReceiptService(
        receipt_repo=receipt_repository,
        campaign_service=campaign_service,
    )
    product_service = ProductService(product_repo=product_repository)

    return AppContainer(
        db=db,
        receipt_repository=receipt_repository,
        receipt_service=receipt_service,
        campaign_repository=campaign_repository,
        campaign_service=campaign_service,
        product_repository=product_repository,
        product_service=product_service,
    )

# Dependency injection functions
def get_receipt_service(container: AppContainer) -> ReceiptService:
    return container.receipt_service

def get_campaign_service(container: AppContainer) -> CampaignService:
    return container.campaign_service

def get_product_service(container: AppContainer) -> ProductService:
    return container.product_service
