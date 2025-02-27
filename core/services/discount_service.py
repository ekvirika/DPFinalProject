from typing import Dict, List, Optional, Tuple
from uuid import UUID

from core.models.campaign import Campaign, CampaignType, DiscountRule, BuyNGetNRule, ComboRule
from core.models.receipt import Receipt, ReceiptItem, Discount
from core.models.repositories.campaign_repository import CampaignRepository
from core.models.repositories.product_repository import ProductRepository


class DiscountService:
    def __init__(
            self,
            campaign_repository: CampaignRepository,
            product_repository: ProductRepository,
    ):
        self.campaign_repository = campaign_repository
        self.product_repository = product_repository

    def apply_discounts(self, receipt: Receipt) -> Receipt:
        """Apply all applicable discounts to the receipt items."""
        # Get all active campaigns
        active_campaigns = self.campaign_repository.get_active()

        # Clear existing discounts
        for item in receipt.products:
            item.discounts = []

        # Apply each campaign type
        for campaign in active_campaigns:
            if campaign.campaign_type == CampaignType.DISCOUNT:
                self._apply_discount_rule(receipt, campaign)
            elif campaign.campaign_type == CampaignType.BUY_N_GET_N:
                self._apply_buy_n_get_n_rule(receipt, campaign)
            elif campaign.campaign_type == CampaignType.COMBO:
                self._apply_combo_rule(receipt, campaign)

        # Recalculate receipt totals after applying all discounts
        receipt.recalculate_totals()

        return receipt

    def _apply_discount_rule(self, receipt: Receipt, campaign: Campaign) -> None:
        """Apply a discount rule to the receipt."""
        rule: DiscountRule = campaign.rules

        # Different logic based on what the discount applies to
        if rule.applies_to == "total":
            # Discount applies to total if it meets minimum amount
            if receipt.subtotal >= rule.min_amount:
                discount_amount = receipt.subtotal * (rule.discount_value / 100)

                # Distribute discount proportionally across all items
                total_item_price = sum(item.total_price for item in receipt.products)
                for item in receipt.products:
                    item_discount = (item.total_price / total_item_price) * discount_amount
                    item.discounts.append(
                        Discount(
                            campaign_id=campaign.id,
                            campaign_name=campaign.name,
                            discount_amount=round(item_discount, 2)
                        )
                    )

        elif rule.applies_to == "products":
            # Discount applies to specific products
            for item in receipt.products:
                if str(item.product_id) in rule.product_ids:
                    # Calculate discount
                    discount_amount = item.total_price * (rule.discount_value / 100)
                    item.discounts.append(
                        Discount(
                            campaign_id=campaign.id,
                            campaign_name=campaign.name,
                            discount_amount=round(discount_amount, 2)
                        )
                    )

    def _apply_buy_n_get_n_rule(self, receipt: Receipt, campaign: Campaign) -> None:
        """Apply a buy N get N rule to the receipt."""
        rule: BuyNGetNRule = campaign.rules

        # Find the buy product and get product in the receipt
        buy_item = None
        get_item = None

        for item in receipt.products:
            if str(item.product_id) == rule.buy_product_id:
                buy_item = item
            if str(item.product_id) == rule.get_product_id:
                get_item = item

        # If both products are in the receipt, apply the discount
        if buy_item and get_item:
            # Calculate how many times the promotion applies
            promotion_count = buy_item.quantity // rule.buy_quantity

            if promotion_count > 0:
                # Calculate discount amount (unit_price * quantity that gets discounted)
                free_quantity = min(promotion_count * rule.get_quantity, get_item.quantity)
                discount_amount = get_item.unit_price * free_quantity

                get_item.discounts.append(
                    Discount(
                        campaign_id=campaign.id,
                        campaign_name=campaign.name,
                        discount_amount=round(discount_amount, 2)
                    )
                )

    def _apply_combo_rule(self, receipt: Receipt, campaign: Campaign) -> None:
        """Apply a combo rule to the receipt."""
        rule: ComboRule = campaign.rules

        # Check if all products in the combo are in the receipt
        combo_products = set(rule.product_ids)
        receipt_product_ids = {str(item.product_id) for item in receipt.products}

        if combo_products.issubset(receipt_product_ids):
            # All combo products are in the receipt
            combo_items = [item for item in receipt.products if str(item.product_id) in combo_products]

            # Calculate the discount
            if rule.discount_type == "percentage":
                # Apply percentage discount to each combo item
                for item in combo_items:
                    discount_amount = item.total_price * (rule.discount_value / 100)
                    item.discounts.append(
                        Discount(
                            campaign_id=campaign.id,
                            campaign_name=campaign.name,
                            discount_amount=round(discount_amount, 2)
                        )
                    )
            elif rule.discount_type == "fixed":
                # Fixed amount discount divided proportionally
                combo_total = sum(item.total_price for item in combo_items)
                for item in combo_items:
                    item_discount = (item.total_price / combo_total) * rule.discount_value
                    item.discounts.append(
                        Discount(
                            campaign_id=campaign.id,
                            campaign_name=campaign.name,
                            discount_amount=round(item_discount, 2)
                        )
                    )