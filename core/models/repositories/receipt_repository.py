from asyncio import Protocol
from typing import Optional, List
from uuid import UUID

from core.models.receipt import Receipt, ReceiptStatus, Payment


class ReceiptRepository(Protocol):
    def create(self, shift_id: UUID) -> Receipt:
        """Create a new receipt"""
        ...

    def get(self, receipt_id: UUID) -> Optional[Receipt]:
        """Get receipt by ID"""
        ...

    def add_item(self, receipt_id: UUID, product_id: UUID, quantity: int) -> Receipt:
        """Add item to receipt"""
        ...

    def update_status(self, receipt_id: UUID, status: ReceiptStatus) -> Receipt:
        """Update receipt status"""
        ...

    def add_payment(self, receipt_id: UUID, payment: Payment) -> Receipt:
        """Add payment to receipt"""
        ...

    def get_receipts_by_shift(self, shift_id: UUID) -> List[Receipt]:
        """Get all receipts for a shift"""
        ...