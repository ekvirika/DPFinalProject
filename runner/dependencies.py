"""
Dependency injection container and provider functions.
"""

from dataclasses import dataclass
from functools import lru_cache

from core.models.repositories.campaign_repository import CampaignRepository
from core.models.repositories.product_repository import ProductRepository
from core.models.repositories.receipt_repository import ReceiptRepository
from core.models.repositories.shift_repository import ShiftRepository
from core.services.campaign_service import CampaignService
from core.services.discount_service import DiscountService
from core.services.exchange_rate_service import ExchangeRateService
from core.services.product_service import ProductService
from core.services.receipt_service import ReceiptService
from core.services.report_service import ReportService
from core.services.shift_service import ShiftService
from infra.db.database import Database
from infra.repositories.campaign_sqlite_repository import SQLiteCampaignRepository
from infra.repositories.payment_sqlite_repository import SQLitePaymentRepository
from infra.repositories.product_sqlite_repository import SQLiteProductRepository
from infra.repositories.receipt_sqlite_repository import SQLiteReceiptRepository
from infra.repositories.report_sqlite_repository import SQLiteReportRepository
from infra.repositories.shift_sqlite_repository import SQLiteShiftRepository


@dataclass
class AppContainer:
    """Container for all application dependencies."""

    db: Database

    # Repositories
    receipt_repository: ReceiptRepository
    product_repository: ProductRepository
    campaign_repository: CampaignRepository
    shift_repository: ShiftRepository

    # Services
    receipt_service: ReceiptService
    product_service: ProductService
    campaign_service: CampaignService
    exchange_service: ExchangeRateService
    report_service: ReportService
    shift_service: ShiftService


@lru_cache()
def get_app_container(db_path: str) -> AppContainer:
    """
    Creates and returns the application container.
    Uses lru_cache to ensure single instance.
    """
    # Initialize database
    database = Database(db_path)

    # Initialize repositories
    product_repository = SQLiteProductRepository(database)
    receipt_repository = SQLiteReceiptRepository(database)
    campaign_repository = SQLiteCampaignRepository(database)
    shift_repository = SQLiteShiftRepository(database)
    payment_repository = SQLitePaymentRepository(database)
    report_repository = SQLiteReportRepository(database, receipt_repository)  # Added receipt_repository argument

    # Initialize services
    exchange_service = ExchangeRateService()  # Removed receipt_repository argument

    product_service = ProductService(product_repository=product_repository)  # Changed product_repo to product_repository

    campaign_service = CampaignService(
        campaign_repository=campaign_repository,  # Changed campaign_repo to campaign_repository
        product_repository=product_repository  # Changed product_repo to product_repository
    )

    shift_service = ShiftService(shift_repository)

    discount_service = DiscountService(
        campaign_repository=campaign_repository,  # Added campaign_repository
        product_repository=product_repository  # Added product_repository
    )

    receipt_service = ReceiptService(receipt_repository,
                                     product_repository,
                                     shift_repository,
                                     discount_service,
                                     exchange_service,
                                     payment_repository
                                     )

    report_service = ReportService(report_repository, shift_repository)

    return AppContainer(
        db=database,
        receipt_repository=receipt_repository,
        product_repository=product_repository,
        campaign_repository=campaign_repository,
        shift_repository=shift_repository,
        receipt_service=receipt_service,
        product_service=product_service,
        campaign_service=campaign_service,
        exchange_service=exchange_service,
        report_service=report_service,
        shift_service=shift_service,
    )


# Convenience dependency provider functions
def get_receipt_service() -> ReceiptService:
    container = get_app_container()
    return container.receipt_service


def get_product_service() -> ProductService:
    container = get_app_container()
    return container.product_service


def get_campaign_service() -> CampaignService:
    container = get_app_container()
    return container.campaign_service


def get_report_service() -> ReportService:
    container = get_app_container()
    return container.report_service


def get_shift_service() -> ShiftService:
    container = get_app_container()
    return container.shift_service