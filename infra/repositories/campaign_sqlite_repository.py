from typing import Dict, Any, Union, List, Optional
from uuid import UUID

from core.models.campaign import Campaign, DiscountRule, BuyNGetNRule, ComboRule, CampaignType
from core.models.errors import InvalidCampaignTypeException, CampaignDatabaseError, CampaignNotFoundException
from core.models.repositories.campaign_repository import CampaignRepository
from infra.db.database import Database, deserialize_json, serialize_json


class SQLiteCampaignRepository(CampaignRepository):
    def __init__(self, db: Database):
        self.db = db

    def create(self, name: str, campaign_type: str, rules: Dict[str, Any]) -> Campaign:
        try:
            # Define a Union type for rule_obj before assignment
            rule_obj: Union[DiscountRule, BuyNGetNRule, ComboRule]

            if campaign_type == CampaignType.DISCOUNT.value:
                rule_obj = DiscountRule(**rules)
            elif campaign_type == CampaignType.BUY_N_GET_N.value:
                rule_obj = BuyNGetNRule(**rules)
            elif campaign_type == CampaignType.COMBO.value:
                rule_obj = ComboRule(**rules)
            else:
                raise InvalidCampaignTypeException(f"Unknown campaign type: {campaign_type}")

            campaign = Campaign(
                name=name, campaign_type=CampaignType(campaign_type), rules=rule_obj
            )

            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO campaigns (id, name, campaign_type, "
                    "rules, is_active) VALUES (?, ?, ?, ?, ?)",
                    (
                        campaign.id,
                        campaign.name,
                        campaign.campaign_type.value,
                        serialize_json(rules),
                        1,
                    ),
                )
                conn.commit()

            return campaign
        except Exception as e:
            # Catch any other exceptions and wrap them
            raise CampaignDatabaseError(f"Failed to create campaign: {str(e)}") from e

    def get_by_id(self, campaign_id: UUID) -> Optional[Campaign]:
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM campaigns WHERE id = ?", (str(campaign_id),))
                row = cursor.fetchone()

                if not row:
                    raise CampaignNotFoundException(f"Campaign with ID '{campaign_id}' not found")

                rules_dict = deserialize_json(row["rules"])

                # Define rule_obj with a Union type
                rule_obj: Union[DiscountRule, BuyNGetNRule, ComboRule]

                if row["campaign_type"] == CampaignType.DISCOUNT.value:
                    rule_obj = DiscountRule(**rules_dict)
                elif row["campaign_type"] == CampaignType.BUY_N_GET_N.value:
                    rule_obj = BuyNGetNRule(**rules_dict)
                elif row["campaign_type"] == CampaignType.COMBO.value:
                    rule_obj = ComboRule(**rules_dict)
                else:
                    raise InvalidCampaignTypeException(f"Unknown campaign type: {row['campaign_type']}")

                return Campaign(
                    id=row["id"],
                    name=row["name"],
                    campaign_type=CampaignType(row["campaign_type"]),
                    rules=rule_obj,
                    is_active=bool(row["is_active"]),
                )
        except CampaignNotFoundException:
            # Re-raise campaign not found error
            raise
        except Exception as e:
            # Catch any other exceptions and wrap them
            raise CampaignDatabaseError(f"Failed to get campaign: {str(e)}") from e

    def get_all(self) -> List[Campaign]:
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM campaigns")
                rows = cursor.fetchall()

                campaigns = []
                for row in rows:
                    rules_dict = deserialize_json(row["rules"])

                    # Define rule_obj with a Union type
                    rule_obj: Union[DiscountRule, BuyNGetNRule, ComboRule]

                    if row["campaign_type"] == CampaignType.DISCOUNT.value:
                        rule_obj = DiscountRule(**rules_dict)
                    elif row["campaign_type"] == CampaignType.BUY_N_GET_N.value:
                        rule_obj = BuyNGetNRule(**rules_dict)
                    elif row["campaign_type"] == CampaignType.COMBO.value:
                        rule_obj = ComboRule(**rules_dict)
                    else:
                        raise InvalidCampaignTypeException(f"Unknown campaign type: {row['campaign_type']}")

                    campaigns.append(
                        Campaign(
                            id=row["id"],
                            name=row["name"],
                            campaign_type=CampaignType(row["campaign_type"]),
                            rules=rule_obj,
                            is_active=bool(row["is_active"]),
                        )
                    )

                return campaigns
        except Exception as e:
            # Catch any exceptions and wrap them
            raise CampaignDatabaseError(f"Failed to get campaigns: {str(e)}") from e

    def deactivate(self, campaign_id: UUID) -> bool:
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE campaigns SET is_active = 0 WHERE id = ?", (str(campaign_id),)
                )
                conn.commit()

                if cursor.rowcount == 0:
                    raise CampaignNotFoundException(f"Campaign with ID '{campaign_id}' not found")

                return True
        except CampaignNotFoundException:
            # Re-raise campaign not found error
            raise
        except Exception as e:
            # Catch any other exceptions and wrap them
            raise CampaignDatabaseError(f"Failed to deactivate campaign: {str(e)}") from e

    def get_active(self) -> List[Campaign]:
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM campaigns WHERE is_active = 1")
                rows = cursor.fetchall()

                campaigns = []
                for row in rows:
                    rules_dict = deserialize_json(row["rules"])

                    # Define rule_obj with a Union type
                    rule_obj: Union[DiscountRule, BuyNGetNRule, ComboRule]

                    if row["campaign_type"] == CampaignType.DISCOUNT.value:
                        rule_obj = DiscountRule(**rules_dict)
                    elif row["campaign_type"] == CampaignType.BUY_N_GET_N.value:
                        rule_obj = BuyNGetNRule(**rules_dict)
                    elif row["campaign_type"] == CampaignType.COMBO.value:
                        rule_obj = ComboRule(**rules_dict)
                    else:
                        raise InvalidCampaignTypeException(f"Unknown campaign type: {row['campaign_type']}")

                    campaigns.append(
                        Campaign(
                            id=row["id"],
                            name=row["name"],
                            campaign_type=CampaignType(row["campaign_type"]),
                            rules=rule_obj,
                            is_active=bool(row["is_active"]),
                        )
                    )

                return campaigns
        except Exception as e:
            # Catch any exceptions and wrap them
            raise CampaignDatabaseError(f"Failed to get active campaigns: {str(e)}") from e
