from datetime import datetime
from typing import List
from uuid import UUID, uuid4

from core.models.campaign import Campaign, CampaignType
from core.models.errors import CampaignValidationError
from core.models.repositories.campaign_repository import CampaignRepository


class CampaignService:
    def __init__(self, campaign_repository: CampaignRepository):
        self.campaign_repository = campaign_repository

    def create_campaign(
        self,
        name: str,
        campaign_type: str,
        start_date: datetime,
        end_date: datetime,
        rules: dict[str, int],
    ) -> Campaign:
        self._validate_campaign_data(name, campaign_type, start_date, end_date, rules)

        try:
            campaign_type_enum = CampaignType(campaign_type)
        except ValueError:
            raise CampaignValidationError(f"Invalid campaign type: {campaign_type}")

        campaign = Campaign(
            id=uuid4(),
            name=name,
            type=campaign_type_enum,
            start_date=start_date,
            end_date=end_date,
            is_active=True,
            conditions=rules,
            created_at=datetime.now(),
        )

        return self.campaign_repository.create(campaign)

    def get_campaign(self, campaign_id: UUID) -> Campaign:
        return self.campaign_repository.get_by_id(campaign_id)

    def get_active_campaigns(self) -> List[Campaign]:
        return self.campaign_repository.get_active_campaigns()

    def deactivate_campaign(self, campaign_id: UUID) -> None:
        self.campaign_repository.deactivate(campaign_id)

    def _validate_campaign_data(
        self,
        name: str,
        campaign_type: str,
        start_date: datetime,
        end_date: datetime,
        rules: dict[str, int],
    ) -> None:
        if not name:
            raise CampaignValidationError("Campaign name cannot be empty")

        if start_date >= end_date:
            raise CampaignValidationError("End date must be after start date")

        if end_date < datetime.now():
            raise CampaignValidationError("End date cannot be in the past")

        self._validate_rules(campaign_type, rules)

    def _validate_rules(self, campaign_type: str, rules: dict[str, int]) -> None:
        if campaign_type == CampaignType.BUY_N_GET_N.value:
            required_fields = ["product_id", "buy_quantity", "get_quantity"]
            if not all(field in rules for field in required_fields):
                raise CampaignValidationError(
                    f"Buy N Get N campaign requires fields: "
                    f"{', '.join(required_fields)}"
                )
        elif campaign_type == CampaignType.DISCOUNT.value:
            if "discount_percentage" not in rules:
                raise CampaignValidationError(
                    "Discount campaign requires discount_percentage"
                )
            if not 0 <= rules["discount_percentage"] <= 100:
                raise CampaignValidationError(
                    "Discount percentage must be between 0 and 100"
                )
        elif campaign_type == CampaignType.COMBO.value:
            required_fields = ["product_ids", "discount_percentage"]
            if not all(field in rules for field in required_fields):
                raise CampaignValidationError(
                    f"Combo campaign requires fields: {', '.join(required_fields)}"
                )
