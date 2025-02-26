from typing import List, Optional, Tuple
from uuid import UUID

from core.models.receipt import (
    Currency,
    Payment,
    Quote,
    Receipt,
    ReceiptStatus,
)
from core.models.repositories.payment_repository import PaymentRepository
from core.models.repositories.product_repository import ProductRepository
from core.models.repositories.receipt_repository import ReceiptRepository
from core.models.repositories.shift_repository import ShiftRepository
from core.models.shift import ShiftStatus
from core.services.discount_service import DiscountService
from core.services.exchange_rate_service import ExchangeRateService


class ReceiptService:
    def __init__(
        self,
        receipt_repository: ReceiptRepository,
        product_repository: ProductRepository,
        shift_repository: ShiftRepository,
        discount_service: DiscountService,
        exchange_service: ExchangeRateService,
        payment_repository: PaymentRepository,
    ):
        self.receipt_repository = receipt_repository
        self.product_repository = product_repository
        self.shift_repository = shift_repository
        self.discount_service = discount_service
        self.exchange_service = exchange_service
        self.payment_repository = payment_repository

    def create_receipt(self, shift_id: UUID) -> Optional[Receipt]:
        """Create a new receipt for a shift."""
        shift = self.shift_repository.get_by_id(shift_id)
        if not shift or shift.status == ShiftStatus.CLOSED:
            return None

        return self.receipt_repository.create(shift_id)

    def get_receipt(self, receipt_id: UUID) -> Optional[Receipt]:
        """Get a receipt by ID."""
        return self.receipt_repository.get(receipt_id)

    def add_product(
        self, receipt_id: UUID, product_id: UUID, quantity: int
    ) -> Optional[Receipt]:
        """Add a product to a receipt with automatic discount application."""
        receipt = self.receipt_repository.get(receipt_id)
        if not receipt or receipt.status == ReceiptStatus.CLOSED:
            return None

        product = self.product_repository.get_by_id(str(product_id))
        if not product:
            return None

        # Add product (initially without discounts)
        updated_receipt = self.receipt_repository.add_product(
            receipt_id, product_id, quantity, product.price, []
        )

        if updated_receipt:
            # Apply discounts
            updated_receipt = self.discount_service.apply_discounts(updated_receipt)

            # Save the updated receipt (with discounts)
            # In a real implementation, you'd update the database with discount info
            return updated_receipt

        return None

    def calculate_payment_quote(
        self, receipt_id: UUID, currency: Currency
    ) -> Optional[Quote]:
        """Calculate payment quote for a receipt in a specific currency."""
        receipt = self.receipt_repository.get(receipt_id)
        if not receipt:
            return None

        quote = self.exchange_service.calculate_quote(receipt.id, currency)
        if quote:
            quote.receipt_id = receipt_id

        return quote

    def add_payment(
        self, receipt_id: UUID, amount: float, currency_name: str
    ) -> Optional[Tuple[Payment, Receipt]]:
        """Add a payment to a receipt and close it if fully paid."""
        receipt = self.receipt_repository.get(receipt_id)
        if not receipt or receipt.status == ReceiptStatus.CLOSED:
            return None

        # Calculate the payment in GEL
        rate = self.exchange_service.get_exchange_rate(
            Currency.value(currency_name), Currency.GEL
        )

        # Create a payment
        payment = self.payment_repository.create(
            str(receipt_id), amount, currency_name, receipt.total, rate
        )

        # Add payment to receipt
        updated_receipt = self.receipt_repository.add_payment(receipt_id, payment)

        # Check if receipt is fully paid
        if updated_receipt:
            total_paid = sum(
                p.payment_amount
                * self.exchange_service.get_exchange_rate(p.currency, Currency.GEL)
                for p in updated_receipt.payments
            )

            if total_paid >= updated_receipt.total:
                # Close the receipt
                updated_receipt = self.receipt_repository.update_status(
                    receipt_id, ReceiptStatus.CLOSED
                )

        return payment, updated_receipt

    def get_receipts_by_shift(self, shift_id: UUID) -> List[Receipt]:
        """Get all receipts for a shift."""
        return self.receipt_repository.get_receipts_by_shift(shift_id)
