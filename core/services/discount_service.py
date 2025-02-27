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
        print(active_campaigns)
        print(f"Number of active campaigns: {len(active_campaigns)}")

        # Clear existing discounts
        for item in receipt.products:
            item.discounts = []

        # Apply each campaign type
        for campaign in active_campaigns:
            print(f"Processing campaign: {campaign.name}, Type: {campaign.campaign_type}")
            print(f"Campaign type check: {campaign.campaign_type == CampaignType.DISCOUNT}")

            if campaign.campaign_type == CampaignType.DISCOUNT:
                print("About to apply discount rule...")
                self._apply_discount_rule(receipt, campaign)
                print("Discount rule applied")
            elif campaign.campaign_type == CampaignType.BUY_N_GET_N:
                self._apply_buy_n_get_n_rule(receipt, campaign)
            elif campaign.campaign_type == CampaignType.COMBO:
                self._apply_combo_rule(receipt, campaign)

        total_discount = sum(
            sum(discount.discount_amount for discount in item.discounts)
            for item in receipt.products
        )

        # Update receipt's discount_amount and total fields
        receipt.discount_amount = total_discount
        receipt.total = receipt.subtotal - total_discount

        return receipt

    def _apply_discount_rule(self, receipt: Receipt, campaign: Campaign) -> None:
        """Apply discount rule to the receipt."""
        print(f"Inside _apply_discount_rule for campaign: {campaign.name}")

        rule = campaign.rules
        print(f"Discount rule: {rule}")

        if rule.applies_to == 'receipt' and receipt.subtotal >= rule.min_amount:
            print(f"Applying receipt-level discount: {rule.discount_value}")
            # Calculate discount amount
            discount_amount = min(receipt.subtotal * (rule.discount_value / 100), receipt.subtotal)

            # Distribute discount proportionally across all items
            total_receipt_value = sum(item.total_price for item in receipt.products)

            if total_receipt_value > 0:
                for item in receipt.products:
                    # Calculate this item's share of the discount
                    item_ratio = item.total_price / total_receipt_value
                    item_discount = discount_amount * item_ratio

                    # Add discount to the item
                    item.discounts.append(Discount(
                        campaign_id=UUID(campaign.id),
                        campaign_name=campaign.name,
                        discount_amount=item_discount
                    ))
                    print(f"Added discount of {item_discount} to item with product ID {item.product_id}")

        elif rule.applies_to == 'products':
            print(f"Checking product-specific discounts for {len(rule.product_ids)} products")
            for item in receipt.products:
                if str(item.product_id) in rule.product_ids:
                    print(f"Applying product discount to {item.product_id}")
                    discount_amount = item.total_price * (rule.discount_value / 100)

                    item.discounts.append(Discount(
                        campaign_id=UUID(campaign.id),
                        campaign_name=campaign.name,
                        discount_amount=discount_amount
                    ))

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
                        campaign_id=UUID(campaign.id),
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
                            campaign_id=UUID(campaign.id),
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
                            campaign_id=UUID(campaign.id),
                            campaign_name=campaign.name,
                            discount_amount=round(item_discount, 2)
                        )
                    )