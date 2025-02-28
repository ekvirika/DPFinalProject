from typing import Any, Dict, List
from uuid import UUID

from core.models.campaign import Campaign
from core.models.repositories.campaign_repository import CampaignRepository
from core.models.repositories.product_repository import ProductRepository


class CampaignService:
    def __init__(
        self,
        campaign_repository: CampaignRepository,
        product_repository: ProductRepository,
    ):
        self.campaign_repository = campaign_repository
        self.product_repository = product_repository

    def create_campaign(
        self, name: str, campaign_type: str, rules: Dict[str, Any]
    ) -> Campaign:
        # No validation here, let repository handle errors
        return self.campaign_repository.create(name, campaign_type, rules)

    def get_campaign(self, campaign_id: UUID) -> Campaign:
        """Get a campaign by ID."""
        return self.campaign_repository.get_by_id(campaign_id)

    def get_all_campaigns(self) -> List[Campaign]:
        return self.campaign_repository.get_all()

    def deactivate_campaign(self, campaign_id: UUID) -> None:
        # No validation here, repository will raise appropriate exceptions
        self.campaign_repository.deactivate(campaign_id)
