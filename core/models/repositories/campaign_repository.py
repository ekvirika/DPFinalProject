from typing import Protocol, List, Optional
from core.models.campaign import Campaign, CampaignCreate, CampaignUpdate


class CampaignRepository(Protocol):
    def create(self, campaign: CampaignCreate) -> Campaign:
        ...

    def get(self, campaign_id: int) -> Optional[Campaign]:
        ...

    def get_all(self) -> List[Campaign]:
        ...

    def update(self, campaign_id: int, campaign: CampaignUpdate) -> Optional[Campaign]:
        ...

    def delete(self, campaign_id: int) -> bool:
        ...
