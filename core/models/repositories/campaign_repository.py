from typing import Any, Dict, List, Optional, Protocol
from uuid import UUID

from core.models.campaign import Campaign


class CampaignRepository(Protocol):
    def create(
        self, name: str, campaign_type: str, rules: Dict[str, Any]
    ) -> Campaign: ...

    def get_by_id(self, campaign_id: UUID) -> Campaign: ...

    def get_all(self) -> List[Campaign]: ...

    def deactivate(self, campaign_id: UUID) -> bool: ...

    def get_active(self) -> List[Campaign]: ...
