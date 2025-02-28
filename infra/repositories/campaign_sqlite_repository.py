from typing import Any, Dict, List, Union, cast
from uuid import UUID, uuid4

from core.models.campaign import (
    BuyNGetNRule,
    Campaign,
    CampaignType,
    ComboRule,
    DiscountRule,
)
from core.models.errors import (
    CampaignDatabaseError,
    CampaignNotFoundException,
    InvalidCampaignTypeException,
)
from core.models.repositories.campaign_repository import CampaignRepository
from infra.db.database import Database


class SQLiteCampaignRepository(CampaignRepository):
    def __init__(self, db: Database):
        self.db = db

    def create(self, name: str, campaign_type: str, rules: Dict[str, Any]) -> Campaign:
        try:
            # Create rule object based on campaign type
            rule_obj: Union[DiscountRule, BuyNGetNRule, ComboRule]

            if campaign_type == CampaignType.DISCOUNT.value:
                rule_obj = DiscountRule(**rules)
            elif campaign_type == CampaignType.BUY_N_GET_N.value:
                rule_obj = BuyNGetNRule(**rules)
            elif campaign_type == CampaignType.COMBO.value:
                rule_obj = ComboRule(**rules)
            else:
                raise InvalidCampaignTypeException(
                    f"Unknown campaign type: {campaign_type}"
                )

            # Create campaign object
            campaign = Campaign(
                name=name, campaign_type=CampaignType(campaign_type), rules=rule_obj
            )

            with (self.db.get_connection() as conn):
                # Start a transaction
                conn.execute("BEGIN TRANSACTION")
                cursor = conn.cursor()

                # Insert campaign
                cursor.execute(
                    "INSERT INTO campaigns (id, name, campaign_type, is_active)"
                    " VALUES (?, ?, ?, ?)",
                    (campaign.id, campaign.name, campaign.campaign_type.value, 1),
                )

                # Insert rule based on campaign type
                rule_id = str(uuid4())

                if campaign_type == CampaignType.DISCOUNT.value:
                    discount_rule = cast(DiscountRule, rule_obj)
                    cursor.execute(
                        "INSERT INTO discount_rules (id, campaign_id, discount_value,"
                        " applies_to, min_amount) "
                        "VALUES (?, ?, ?, ?, ?)",
                        (
                            rule_id,
                            campaign.id,
                            discount_rule.discount_value,
                            discount_rule.applies_to,
                            discount_rule.min_amount,
                        ),
                    )

                    print(discount_rule.applies_to)
                    if (
                            discount_rule.applies_to == "product" and
                            discount_rule.product_ids
                    ):
                        for product_id in discount_rule.product_ids:
                            cursor.execute(
                                "INSERT INTO discount_rule_products"
                                " (discount_rule_id,"
                                " product_id) VALUES (?, ?)",
                                (rule_id, product_id),
                            )

                elif campaign_type == CampaignType.BUY_N_GET_N.value:
                    buy_n_get_n_rule = cast(BuyNGetNRule, rule_obj)
                    cursor.execute(
                        "INSERT INTO buy_n_get_n_rules (id, campaign_id,"
                        " buy_product_id,"
                        " buy_quantity, get_product_id, get_quantity) "
                        "VALUES (?, ?, ?, ?, ?, ?)",
                        (
                            rule_id,
                            campaign.id,
                            buy_n_get_n_rule.buy_product_id,
                            buy_n_get_n_rule.buy_quantity,
                            buy_n_get_n_rule.get_product_id,
                            buy_n_get_n_rule.get_quantity,
                        ),
                    )

                elif campaign_type == CampaignType.COMBO.value:
                    # Use cast to tell mypy that rule_obj is a ComboRule in this block
                    combo_rule = cast(ComboRule, rule_obj)
                    cursor.execute(
                        "INSERT INTO combo_rules (id, campaign_id, discount_type,"
                        " discount_value) VALUES (?, ?, ?, ?)",
                        (
                            rule_id,
                            campaign.id,
                            combo_rule.discount_type,
                            combo_rule.discount_value,
                        ),
                    )

                    # Insert product IDs for combo
                    for product_id in combo_rule.product_ids:
                        cursor.execute(
                            "INSERT INTO combo_rule_products"
                            " (combo_rule_id, product_id)"
                            " VALUES (?, ?)",
                            (rule_id, product_id),
                        )

                # Commit transaction
                conn.execute("COMMIT")

            return campaign

        except Exception as e:
            # Catch any exceptions and wrap them
            raise CampaignDatabaseError(f"Failed to create campaign: {str(e)}") from e

    def get_by_id(self, campaign_id: UUID) -> Campaign:
        try:
            print("campaign id: ", campaign_id)
            with self.db.get_connection() as conn:
                cursor = conn.cursor()

                # Get campaign
                cursor.execute(
                    "SELECT * FROM campaigns WHERE id = ?", (str(campaign_id),)
                )
                campaign_row = cursor.fetchone()

                if not campaign_row:
                    raise CampaignNotFoundException(
                        f"Campaign with ID '{campaign_id}' not found"
                    )

                # Get rule based on campaign type
                campaign_type = campaign_row["campaign_type"]
                rule_obj: Union[DiscountRule, BuyNGetNRule, ComboRule]

                if campaign_type == CampaignType.DISCOUNT.value:
                    cursor.execute(
                        "SELECT * FROM discount_rules WHERE campaign_id = ?",
                        (str(campaign_id),),
                    )
                    rule_row = cursor.fetchone()

                    if not rule_row:
                        raise CampaignNotFoundException(
                            f"Discount rule for campaign ID '{campaign_id}' not found"
                        )

                    # Get product IDs if applies_to is 'products'
                    product_ids = []
                    if rule_row["applies_to"] == "product":
                        cursor.execute(
                            "SELECT product_id FROM discount_rule_products WHERE"
                            " discount_rule_id = ?",
                            (rule_row["id"],),
                        )
                        product_ids = [row["product_id"] for row in cursor.fetchall()]

                    rule_obj = DiscountRule(
                        discount_value=rule_row["discount_value"],
                        applies_to=rule_row["applies_to"],
                        min_amount=rule_row["min_amount"],
                        product_ids=product_ids,
                    )

                elif campaign_type == CampaignType.BUY_N_GET_N.value:
                    cursor.execute(
                        "SELECT * FROM buy_n_get_n_rules WHERE campaign_id = ?",
                        (str(campaign_id),),
                    )
                    rule_row = cursor.fetchone()

                    if not rule_row:
                        raise CampaignNotFoundException(
                            f"Buy N Get N rule for campaign ID "
                            f"'{campaign_id}' not found"
                        )

                    rule_obj = BuyNGetNRule(
                        buy_product_id=rule_row["buy_product_id"],
                        buy_quantity=rule_row["buy_quantity"],
                        get_product_id=rule_row["get_product_id"],
                        get_quantity=rule_row["get_quantity"],
                    )

                elif campaign_type == CampaignType.COMBO.value:
                    cursor.execute(
                        "SELECT * FROM combo_rules WHERE campaign_id = ?",
                        (str(campaign_id),),
                    )
                    rule_row = cursor.fetchone()

                    if not rule_row:
                        raise CampaignNotFoundException(
                            f"Combo rule for campaign ID '{campaign_id}' not found"
                        )

                    # Get product IDs for combo
                    cursor.execute(
                        "SELECT product_id FROM combo_rule_products WHERE "
                        "combo_rule_id = ?",
                        (rule_row["id"],),
                    )
                    product_ids = [row["product_id"] for row in cursor.fetchall()]

                    rule_obj = ComboRule(
                        product_ids=product_ids,
                        discount_type=rule_row["discount_type"],
                        discount_value=rule_row["discount_value"],
                    )

                else:
                    raise InvalidCampaignTypeException(
                        f"Unknown campaign type: {campaign_type}"
                    )

                # Create and return Campaign object
                return Campaign(
                    id=campaign_row["id"],
                    name=campaign_row["name"],
                    campaign_type=CampaignType(campaign_row["campaign_type"]),
                    rules=rule_obj,
                    is_active=bool(campaign_row["is_active"]),
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
                campaign_rows = cursor.fetchall()

                campaigns: List[Campaign] = []
                for campaign_row in campaign_rows:
                    # Get the campaign by ID (reuse existing method)
                    campaign = self.get_by_id(UUID(campaign_row["id"]))
                    campaigns.append(campaign)

                return campaigns

        except Exception as e:
            # Catch any exceptions and wrap them
            raise CampaignDatabaseError(f"Failed to get campaigns: {str(e)}") from e

    def deactivate(self, campaign_id: UUID) -> bool:
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE campaigns SET is_active = 0 WHERE id = ?",
                    (str(campaign_id),),
                )
                conn.commit()

                if cursor.rowcount == 0:
                    raise CampaignNotFoundException(
                        f"Campaign with ID '{campaign_id}' not found"
                    )

                return True

        except CampaignNotFoundException:
            # Re-raise campaign not found error
            raise
        except Exception as e:
            # Catch any other exceptions and wrap them
            raise CampaignDatabaseError(
                f"Failed to deactivate campaign: {str(e)}"
            ) from e

    def get_active(self) -> List[Campaign]:
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM campaigns WHERE is_active = 1")
                campaign_rows = cursor.fetchall()

                campaigns: List[Campaign] = []
                for campaign_row in campaign_rows:
                    # Get the campaign by ID (reuse existing method)
                    campaign = self.get_by_id(UUID(campaign_row["id"]))
                    campaigns.append(campaign)

                return campaigns

        except Exception as e:
            # Catch any exceptions and wrap them
            raise CampaignDatabaseError(
                f"Failed to get active campaigns: {str(e)}"
            ) from e