from typing import Dict, List, Optional
from uuid import UUID

from core.models.campaign import (
    BuyNGetNRule,
    Campaign,
    CampaignType,
    ComboRule,
    DiscountRule,
)
from infra.db.database import Database, deserialize_json, serialize_json


class SQLiteCampaignRepository:
    def __init__(self, db: Database):
        self.db = db

    def create(self, name: str, campaign_type: str, rules: Dict) -> Campaign:
        if campaign_type == CampaignType.DISCOUNT.value:
            rule_obj = DiscountRule(**rules)
        elif campaign_type == CampaignType.BUY_N_GET_N.value:
            rule_obj = BuyNGetNRule(**rules)
        elif campaign_type == CampaignType.COMBO.value:
            rule_obj = ComboRule(**rules)
        else:
            raise ValueError(f"Unknown campaign type: {campaign_type}")

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

    def get_by_id(self, campaign_id: UUID) -> Optional[Campaign]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM campaigns WHERE id = ?", (campaign_id,))
            row = cursor.fetchone()

            if row:
                rules_dict = deserialize_json(row["rules"])

                if row["campaign_type"] == CampaignType.DISCOUNT.value:
                    rule_obj = DiscountRule(**rules_dict)
                elif row["campaign_type"] == CampaignType.BUY_N_GET_N.value:
                    rule_obj = BuyNGetNRule(**rules_dict)
                elif row["campaign_type"] == CampaignType.COMBO.value:
                    rule_obj = ComboRule(**rules_dict)
                else:
                    raise ValueError(f"Unknown campaign type: {row['campaign_type']}")

                return Campaign(
                    id=row["id"],
                    name=row["name"],
                    campaign_type=CampaignType(row["campaign_type"]),
                    rules=rule_obj,
                    is_active=bool(row["is_active"]),
                )

            return None

    def get_all(self) -> List[Campaign]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM campaigns")
            rows = cursor.fetchall()

            campaigns = []
            for row in rows:
                rules_dict = deserialize_json(row["rules"])

                if row["campaign_type"] == CampaignType.DISCOUNT.value:
                    rule_obj = DiscountRule(**rules_dict)
                elif row["campaign_type"] == CampaignType.BUY_N_GET_N.value:
                    rule_obj = BuyNGetNRule(**rules_dict)
                elif row["campaign_type"] == CampaignType.COMBO.value:
                    rule_obj = ComboRule(**rules_dict)
                else:
                    raise ValueError(f"Unknown campaign type: {row['campaign_type']}")

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

    def deactivate(self, campaign_id: UUID) -> bool:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE campaigns SET is_active = 0 WHERE id = ?", (campaign_id,)
            )
            conn.commit()

            return cursor.rowcount > 0

    def get_active(self) -> List[Campaign]:
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM campaigns WHERE is_active = 1")
            rows = cursor.fetchall()

            campaigns = []
            for row in rows:
                rules_dict = deserialize_json(row["rules"])

                if row["campaign_type"] == CampaignType.DISCOUNT.value:
                    rule_obj = DiscountRule(**rules_dict)
                elif row["campaign_type"] == CampaignType.BUY_N_GET_N.value:
                    rule_obj = BuyNGetNRule(**rules_dict)
                elif row["campaign_type"] == CampaignType.COMBO.value:
                    rule_obj = ComboRule(**rules_dict)
                else:
                    raise ValueError(f"Unknown campaign type: {row['campaign_type']}")

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
