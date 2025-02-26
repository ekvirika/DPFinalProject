from typing import Dict, List, Any
from uuid import UUID

from core.models.campaign import CampaignType, Campaign, DiscountRule, BuyNGetNRule, ComboRule
from core.models.receipt import Discount, Receipt
from core.models.repositories.campaign_repository import CampaignRepository
from core.models.repositories.product_repository import ProductRepository


class DiscountService:

    def __init__(self, campaign_repository: CampaignRepository, product_repository: ProductRepository):
        self.campaign_repository = campaign_repository
        self.product_repository = product_repository


    def apply_discounts(self, receipt: Receipt) -> Receipt:
        """Apply all available discounts to a receipt and return the updated receipt."""
        active_campaigns = self.campaign_repository.get_active()
        product_discounts: dict[str, list[Any]] = {}

        # Initialize empty discount lists for each product
        for product_item in receipt.products:
            product_discounts[str(product_item.product_id)] = []

        # Apply product-specific discounts
        for campaign in active_campaigns:
            if campaign.campaign_type == CampaignType.DISCOUNT:
                self._apply_discount_campaign(campaign, receipt, product_discounts)
            elif campaign.campaign_type == CampaignType.BUY_N_GET_N:
                self._apply_buy_n_get_n_campaign(campaign, receipt, product_discounts)
            elif campaign.campaign_type == CampaignType.COMBO:
                self._apply_combo_campaign(campaign, receipt, product_discounts)

        # Update receipt items with the calculated discounts
        for item in receipt.products:
            item.discounts = product_discounts[str(item.product_id)]
            item.final_price = item.total_price - sum(d.discount_amount for d in item.discounts)

        # Recalculate receipt totals
        receipt.recalculate_totals()

        return receipt


    def _apply_discount_campaign(self, campaign: Campaign,
                                 receipt: Receipt,
                                 product_discounts: Dict[str, List[Discount]])\
            -> None:
        """Apply discount campaign to a receipt."""
        rules = campaign
        if isinstance(rules, DiscountRule):
            if rules.applies_to == "product":
                # Apply discount to specific products
                for product_id in rules.product_ids:
                    for item in receipt.products:
                        if item.product_id == product_id:
                            discount_amount = (item.unit_price * item.quantity) * (rules.discount_value / 100)
                            discount = Discount(
                                campaign_id=UUID(campaign.id),
                                campaign_name=campaign.name,
                                discount_amount=discount_amount
                            )
                            product_discounts[product_id].append(discount)

            elif rules.applies_to == "receipt" and rules.min_amount is not None:
                # Apply discount to entire receipt if it meets the minimum amount
                subtotal = sum(item.unit_price * item.quantity for item in receipt.products)
                if subtotal >= rules.min_amount:
                    # Distribute discount proportionally to each item
                    total_discount = subtotal * (rules.discount_value / 100)
                    for item in receipt.products:
                        item_subtotal = item.unit_price * item.quantity
                        item_proportion = item_subtotal / subtotal if subtotal > 0 else 0
                        item_discount = total_discount * item_proportion

                        discount = Discount(
                            campaign_id=UUID(campaign.id),
                            campaign_name=campaign.name,
                            discount_amount=item_discount
                        )
                        product_discounts[str(item.product_id)].append(discount)


    def _apply_buy_n_get_n_campaign(self, campaign: Campaign, receipt: Receipt,
                                    product_discounts: Dict[str, List[Discount]]) -> None:
        """Apply buy N get N campaign to a receipt."""
        rules = campaign.rules
        if isinstance(rules, BuyNGetNRule):
            # Count how many of the "buy" product are in the receipt
            buy_quantity = 0
            for item in receipt.products:
                if item.product_id == rules.buy_product_id:
                    buy_quantity += item.quantity

            # Calculate how many free items the customer should get
            if buy_quantity >= rules.buy_quantity:
                multiple = buy_quantity // rules.buy_quantity
                free_quantity = multiple * rules.get_quantity

                # If the "get" product is the same as the "buy" product, apply discount to that item
                if rules.get_product_id == rules.buy_product_id:
                    for item in receipt.products:
                        if item.product_id == rules.get_product_id:
                            # Calculate discount for free items
                            # Limit free items to actual quantity minus already paid items
                            actual_free = min(free_quantity, item.quantity - buy_quantity)
                            if actual_free > 0:
                                discount_amount = item.unit_price * actual_free
                                discount = Discount(
                                    campaign_id=UUID(campaign.id),
                                    campaign_name=campaign.name,
                                    discount_amount=discount_amount
                                )
                                product_discounts[str(item.product_id)].append(discount)
                            break
                else:
                    # Look for the "get" product in the receipt
                    for item in receipt.products:
                        if item.product_id == rules.get_product_id:
                            # Calculate discount for free items
                            actual_free = min(free_quantity, item.quantity)
                            if actual_free > 0:
                                discount_amount = item.unit_price * actual_free
                                discount = Discount(
                                    campaign_id=UUID(campaign.id),
                                    campaign_name=campaign.name,
                                    discount_amount=discount_amount
                                )
                                product_discounts[str(item.product_id)].append(discount)
                            break


    def _apply_combo_campaign(self, campaign: Campaign,
                              receipt: Receipt,
                              product_discounts: Dict[str, List[Discount]]):
        """Apply combo campaign to a receipt."""
        rules = campaign.rules
        if isinstance(rules, ComboRule):
            # Check if all required products are in the receipt
            all_products_present = True
            for product_id in rules.product_ids:
                product_present = False
                for item in receipt.products:
                    if item.product_id == product_id:
                        product_present = True
                        break

                if not product_present:
                    all_products_present = False
                    break

            if all_products_present:
                # Apply discount to each product in the combo
                for product_id in rules.product_ids:
                    for item in receipt.products:
                        if item.product_id == product_id:
                            if rules.discount_type == "percentage":
                                discount_amount = (item.unit_price * item.quantity) * (rules.discount_value / 100)
                            else:  # fixed amount
                                # Distribute fixed discount amount proportionally
                                discount_amount = rules.discount_value / len(rules.product_ids)

                            discount = Discount(
                                campaign_id=UUID(campaign.id),
                                campaign_name=campaign.name,
                                discount_amount=discount_amount
                            )
                            product_discounts[product_id].append(discount)

