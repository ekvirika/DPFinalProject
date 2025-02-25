from datetime import datetime
from typing import List, Dict
from uuid import UUID, uuid4

from core.models.campaign import Campaign, CampaignType
from core.models.errors import CampaignValidationError
from core.models.repositories.campaign_repository import CampaignRepository
from core.models.repositories.product_repository import ProductRepository


class CampaignService:
    def __init__(self, campaign_repository: CampaignRepository, product_repository: ProductRepository):
        self.campaign_repository = campaign_repository
        self.product_repository = product_repository

    def create_campaign(self, name: str, campaign_type: str, rules: Dict[str, int]) -> Campaign:
        self._validate_campaign_data(name, campaign_type, rules)
        campaign_type_enum = CampaignType(campaign_type)

        campaign = Campaign(
            id=uuid4(),
            name=name,
            type=campaign_type_enum,
            is_active=True,
            conditions=rules,
            created_at=datetime.now(),
        )

        return self.campaign_repository.create(campaign)

    def get_campaign(self, campaign_id: UUID) -> Campaign:
        campaign = self.campaign_repository.get_by_id(campaign_id)
        if not campaign:
            raise CampaignValidationError(f"Campaign with ID '{campaign_id}' not found")
        return campaign

    def get_all_campaigns(self) -> List[Campaign]:
        return self.campaign_repository.get_all()

    def deactivate_campaign(self, campaign_id: UUID) -> None:
        campaign = self.campaign_repository.get_by_id(campaign_id)
        if not campaign:
            raise CampaignValidationError(f"Campaign with ID '{campaign_id}' not found")
        self.campaign_repository.deactivate(campaign_id)

    def _validate_campaign_data(self, name: str, campaign_type: str, rules: Dict[str, int]) -> None:
        if not name:
            raise CampaignValidationError("Campaign name cannot be empty")

        if campaign_type not in CampaignType.__members__:
            raise CampaignValidationError(f"Invalid campaign type: {campaign_type}")

        self._validate_rules(campaign_type, rules)

    def _validate_rules(self, campaign_type: str, rules: Dict[str, int]) -> None:
        if campaign_type == CampaignType.BUY_N_GET_N.value:
            required_fields = ["buy_product_id", "get_product_id", "buy_quantity", "get_quantity"]
            self._validate_required_fields(rules, required_fields)
            self._validate_product_existence([rules["buy_product_id"], rules["get_product_id"]])
        elif campaign_type == CampaignType.DISCOUNT.value:
            required_fields = ["applies_to", "discount_percentage"]
            self._validate_required_fields(rules, required_fields)
            if rules["applies_to"] == "product" and "product_ids" in rules:
                self._validate_product_existence(rules["product_ids"])
        elif campaign_type == CampaignType.COMBO.value:
            required_fields = ["product_ids", "discount_percentage"]
            self._validate_required_fields(rules, required_fields)
            self._validate_product_existence(rules["product_ids"])

    def _validate_required_fields(self, rules: Dict[str, int], required_fields: List[str]) -> None:
        missing_fields = [field for field in required_fields if field not in rules]
        if missing_fields:
            raise CampaignValidationError(
                f"Missing required fields for {rules['campaign_type']} campaign: {', '.join(missing_fields)}"
            )

    def _validate_product_existence(self, product_ids: List[UUID]) -> None:
        for product_id in product_ids:
            if not self.product_repository.get_by_id(product_id):
                raise CampaignValidationError(f"Product with ID '{product_id}' not found")
