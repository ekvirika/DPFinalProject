from typing import Dict, List, Optional, Protocol
from uuid import UUID

from core.models.campaign import Campaign, CampaignType


class CampaignRepository(Protocol):
    def create(
        self, name: str, campaign_type: CampaignType, rules: Dict
    ) -> Campaign: ...

    def get_by_id(self, campaign_id: UUID) -> Optional[Campaign]: ...

    def get_all(self) -> List[Campaign]: ...

    def deactivate(self, campaign_id: UUID) -> bool: ...

    def get_active(self) -> List[Campaign]: ...
