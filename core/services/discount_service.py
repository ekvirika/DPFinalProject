import logging
from typing import Dict, List, cast
from uuid import UUID

from core.models.campaign import (
    BuyNGetNRule,
    Campaign,
    CampaignType,
    ComboRule,
    DiscountRule,
)
from core.models.receipt import Discount, Receipt, ReceiptItem
from core.models.repositories.campaign_repository import CampaignRepository
from core.models.repositories.product_repository import ProductRepository

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)


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
        logging.debug(f"Active campaigns: {active_campaigns}")
        logging.info(f"Number of active campaigns: {len(active_campaigns)}")

        # Clear existing discounts
        for item in receipt.products:
            item.discounts = []

        # Clear receipt-level discounts
        receipt.discounts = []

        # Store potential discounts for each item to later select the best one
        potential_discounts: Dict[UUID, List[Discount]] = {
            item.product_id: [] for item in receipt.products
        }

        # Store potential receipt-level discounts
        potential_receipt_discounts: List[Discount] = []

        # Apply each campaign type
        for campaign in active_campaigns:
            logging.info(
                f"Processing campaign: {campaign.name}, Type: {campaign.campaign_type}"
            )
            logging.debug(
                f"Campaign type check: {
                    campaign.campaign_type == CampaignType.DISCOUNT
                }"
            )

            if campaign.campaign_type == CampaignType.DISCOUNT:
                logging.info("Applying discount rule...")
                self._apply_discount_rule(
                    receipt, campaign, potential_discounts, potential_receipt_discounts
                )
                logging.info("Discount rule applied")
            elif campaign.campaign_type == CampaignType.BUY_N_GET_N:
                self._apply_buy_n_get_n_rule(receipt, campaign, potential_discounts)
            elif campaign.campaign_type == CampaignType.COMBO:
                self._apply_combo_rule(receipt, campaign, potential_discounts)

        # For each item, apply only the discount with the largest amount
        for item in receipt.products:
            if (
                item.product_id in potential_discounts
                and potential_discounts[item.product_id]
            ):
                best_discount = max(
                    potential_discounts[item.product_id],
                    key=lambda d: d.discount_amount,
                )
                item.discounts = [best_discount]
                logging.info(
                    f"Applied best discount of "
                    f"{best_discount.discount_amount} to"
                    f" product {item.product_id} "
                    f"from campaign {best_discount.campaign_name}"
                )

        # Apply the best receipt-level discount if any exist
        if potential_receipt_discounts:
            best_receipt_discount = max(
                potential_receipt_discounts,
                key=lambda d: d.discount_amount,
            )
            receipt.discounts = [best_receipt_discount]
            logging.info(
                f"Applied best receipt discount of "
                f"{best_receipt_discount.discount_amount} "
                f"from campaign {best_receipt_discount.campaign_name}"
            )

        # Calculate total discount and update receipt
        total_discount = sum(
            sum(discount.discount_amount for discount in item.discounts)
            for item in receipt.products
        ) + sum(d.discount_amount for d in receipt.discounts)

        # Update receipt's discount_amount and total fields
        receipt.discount_amount = total_discount
        receipt.total = receipt.subtotal - total_discount
        logging.info(
            f"Total discount applied: {total_discount}, New total: {receipt.total}"
        )

        return receipt

    def _apply_discount_rule(
        self,
        receipt: Receipt,
        campaign: Campaign,
        potential_discounts: Dict[UUID, List[Discount]],
        potential_receipt_discounts: List[Discount],
    ) -> None:
        """Apply discount rule to the receipt and store in potential discounts."""
        logging.debug(f"Inside _apply_discount_rule for campaign: {campaign.name}")

        # Ensure we're working with a DiscountRule by using type cast
        if campaign.campaign_type != CampaignType.DISCOUNT:
            return

        rule = cast(DiscountRule, campaign.rules)
        logging.debug(f"Discount rule: {rule}")
        logging.info(receipt)

        if (
            rule.applies_to == "receipt"
            and rule.min_amount is not None
            and receipt.subtotal >= rule.min_amount
        ):
            logging.info(f"Applying receipt-level discount: {rule.discount_value}%")

            # Calculate discount amount
            discount_amount = min(
                receipt.subtotal * (rule.discount_value / 100), receipt.subtotal
            )
            logging.debug(f"Total discount calculated: {discount_amount}")

            # Store the receipt-level discount as a potential discount
            potential_receipt_discounts.append(
                Discount(UUID(campaign.id), campaign.name, discount_amount)
            )

        elif rule.applies_to == "product":
            logging.info(
                f"Checking product-specific discounts for"
                f" {len(rule.product_ids)} products"
            )
            for item in receipt.products:
                if str(item.product_id) in rule.product_ids:
                    logging.info(f"Applying product discount to {item.product_id}")
                    discount_amount = item.total_price * (rule.discount_value / 100)

                    discount = Discount(
                        campaign_id=UUID(campaign.id),
                        campaign_name=campaign.name,
                        discount_amount=discount_amount,
                    )

                    # Add to potential discounts
                    potential_discounts[item.product_id].append(discount)

    def _apply_buy_n_get_n_rule(
        self,
        receipt: Receipt,
        campaign: Campaign,
        potential_discounts: Dict[UUID, List[Discount]],
    ) -> None:
        """Apply a Buy N Get N rule to the receipt."""
        # Type check to ensure we're using the correct rule type
        if campaign.campaign_type != CampaignType.BUY_N_GET_N:
            return

        rule = cast(BuyNGetNRule, campaign.rules)
        logging.debug(f"Applying Buy N Get N Rule: {rule}")

        # Find the buy product in the receipt
        buy_item = None
        get_item = None

        for item in receipt.products:
            if item.product_id == UUID(rule.buy_product_id):
                buy_item = item
            if item.product_id == UUID(rule.get_product_id):
                get_item = item

        if not buy_item:
            # If the buy product isn't in the receipt, no discount applies
            logging.debug(f"Buy product {rule.buy_product_id} is not in the receipt.")
            return

        # Calculate how many "get" items should be given for free
        promotion_count = buy_item.quantity // rule.buy_quantity
        free_quantity = promotion_count * rule.get_quantity

        if promotion_count <= 0:
            logging.debug("Not enough items to apply the promotion.")
            return

        logging.debug(
            f"Promotion applies {promotion_count} times, "
            f"giving {free_quantity} free items."
        )

        if get_item:
            # If the "get" item is already in the receipt, increase its quantity
            get_item.quantity += free_quantity
            get_item.total_price += (
                get_item.unit_price * free_quantity
            )  # Update total price
        else:
            # If the "get" item is not in the receipt, fetch it from the repository
            get_product = self.product_repository.get_by_id(UUID(rule.get_product_id))
            if not get_product:
                logging.warning(
                    f"Get product {rule.get_product_id} not found in repository."
                )
                return

            # Create a new receipt item for the free product
            get_item = ReceiptItem(
                product_id=get_product.id,
                quantity=free_quantity,
                unit_price=get_product.price,  # Normal price
                discounts=[],
            )
            receipt.products.append(get_item)

            # Initialize potential discounts for this new item
            potential_discounts[get_item.product_id] = []

        # Calculate discount for the free items
        discount_amount = get_item.unit_price * free_quantity
        discount = Discount(
            campaign_id=UUID(campaign.id),
            campaign_name=campaign.name,
            discount_amount=round(discount_amount, 2),
        )

        # Add to potential discounts
        potential_discounts[get_item.product_id].append(discount)

        # Update receipt totals correctly
        receipt.subtotal = sum(
            item.total_price for item in receipt.products
        )  # Include all products

    def _apply_combo_rule(
        self,
        receipt: Receipt,
        campaign: Campaign,
        potential_discounts: Dict[UUID, List[Discount]],
    ) -> None:
        """Apply a combo rule to the receipt."""
        # Type check to ensure we're using the correct rule type
        if campaign.campaign_type != CampaignType.COMBO:
            return

        rule = cast(ComboRule, campaign.rules)
        logging.debug(f"Applying Combo Rule: {rule}")

        # Check if all products in the combo are in the receipt
        combo_products = set(rule.product_ids)
        receipt_product_ids = {str(item.product_id) for item in receipt.products}

        logging.info(combo_products)
        logging.info(receipt_product_ids)
        if combo_products.issubset(receipt_product_ids):
            logging.info(f"All combo products present in receipt: {combo_products}")

            combo_items = [
                item
                for item in receipt.products
                if str(item.product_id) in combo_products
            ]

            # Calculate the discount
            if rule.discount_type == "percentage":
                for item in combo_items:
                    discount_amount = item.total_price * (rule.discount_value / 100)
                    discount = Discount(
                        campaign_id=UUID(campaign.id),
                        campaign_name=campaign.name,
                        discount_amount=round(discount_amount, 2),
                    )

                    # Add to potential discounts
                    potential_discounts[item.product_id].append(discount)
                    logging.info(
                        f"Added potential {rule.discount_value}%"
                        f" discount to {item.product_id}"
                    )

            elif rule.discount_type == "fixed":
                combo_total = sum(item.total_price for item in combo_items)
                for item in combo_items:
                    item_discount = (
                        item.total_price / combo_total
                    ) * rule.discount_value
                    discount = Discount(
                        campaign_id=UUID(campaign.id),
                        campaign_name=campaign.name,
                        discount_amount=round(item_discount, 2),
                    )

                    # Add to potential discounts
                    potential_discounts[item.product_id].append(discount)
                    logging.info(
                        f"Added potential fixed discount of {item_discount}"
                        f" to {item.product_id}"
                    )
