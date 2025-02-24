from typing import List, Protocol
from uuid import UUID

from core.models.campaign import Campaign


class CampaignRepository(Protocol):
    def create(self, campaign: Campaign) -> Campaign:
        """Create and store a new campaign."""
        pass

    def get_by_id(self, campaign_id: UUID) -> Campaign:
        """Retrieve a campaign by its unique identifier."""
        pass

    def deactivate(self, campaign_id: UUID) -> None:
        """Deactivate a campaign by its unique identifier."""
        pass

    def get_active_campaigns(self) -> List[Campaign]:
        """Retrieve all active campaigns."""
        pass
