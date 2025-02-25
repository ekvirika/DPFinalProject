from typing import List, Protocol, Dict, Optional
from uuid import UUID

from core.models.campaign import Campaign


class CampaignRepository(Protocol):
    def create(self, name: str, campaign_type: str, rules: Dict) -> Campaign:
        ...

    def get_by_id(self, campaign_id: str) -> Optional[Campaign]:
        ...

    def get_all(self) -> List[Campaign]:
        ...

    def deactivate(self, campaign_id: str) -> bool:
        ...

    def get_active(self) -> List[Campaign]:
        ...
