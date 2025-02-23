# core/dependencies.py
from dataclasses import dataclass
from typing import Protocol

from core.models.repositories.receipt_repository import ReceiptRepository
from core.services.receipt_service import ReceiptService
from infra.db.database import SQLiteDatabase, Database
from infra.repositories.receipt_sqlite_repository import SQLiteReceiptRepository


class ExchangeService(Protocol):
    def get_rate(self, from_currency: str, to_currency: str) -> float:
        ...


class CampaignService(Protocol):
    def apply_campaigns(self, receipt_id: int) -> None:
        ...


@dataclass
class AppContainer:
    db: Database
    receipt_repository: ReceiptRepository
    receipt_service: ReceiptService
    exchange_service: ExchangeService
    campaign_service: CampaignService


def create_app_container(db_path: str) -> AppContainer:
    # Initialize database
    database = SQLiteDatabase(db_path)
    database.init_db()

    # Initialize repositories
    receipt_repository = SQLiteReceiptRepository(database)

    # Initialize services
    # exchange_service = DummyExchangeService()  # TODO: Replace with real implementation
    # campaign_service = DummyCampaignService()  # TODO: Replace with real implementation
    #
    # receipt_service = ReceiptService(
    #     receipt_repo=receipt_repository,
    #     exchange_service=exchange_service,
    #     campaign_service=campaign_service
    # )
    #
    # return AppContainer(
    #     db=database,
    #     receipt_repository=receipt_repository,
    #     receipt_service=receipt_service,
    #     exchange_service=exchange_service,
    #     campaign_service=campaign_service
    # )