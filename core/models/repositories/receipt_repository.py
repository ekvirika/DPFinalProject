from typing import List, Protocol
from uuid import UUID

from core.models.receipt import Payment, Receipt, ReceiptStatus


class ReceiptRepository(Protocol):
    def create(self, shift_id: UUID) -> Receipt:
        """Create a new receipt"""
        pass

    def get(self, receipt_id: UUID) -> Receipt:
        """Get receipt by ID"""
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

    def update(self, receipt_id: UUID, updated_receipt: Receipt) -> Receipt:
        pass
