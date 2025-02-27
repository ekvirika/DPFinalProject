from typing import Dict, List, Protocol
from uuid import UUID

from core.models.receipt import Discount, Payment, Receipt, ReceiptStatus


class ReceiptRepository(Protocol):
    def create(self, shift_id: UUID) -> Receipt:
        """Create a new receipt"""
        pass

    def get(self, receipt_id: UUID) -> Receipt:
        """Get receipt by ID"""
        pass

    def add_product(
        self,
        receipt_id: UUID,
        product_id: UUID,
        quantity: int,
        unit_price: float,
        discounts: List[Dict[str, Discount]],  # Add type arguments
    ) -> Receipt:
        """Add item to receipt"""
        pass

    def update_status(self, receipt_id: UUID, status: ReceiptStatus) -> Receipt:
        """Update receipt status"""
        pass

    def add_payment(self, receipt_id: UUID, payment: Payment) -> Receipt:
        """Add payment to receipt"""
        pass

    def get_receipts_by_shift(self, shift_id: UUID) -> List[Receipt]:
        """Get all receipts for a shift"""
        pass
