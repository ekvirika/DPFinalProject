from asyncio import Protocol
from typing import Optional, List

from core.models.receipt import Receipt, ReceiptStatus, Payment


class ReceiptRepository(Protocol):
    def create(self, shift_id: int) -> Receipt:
        """Create a new receipt"""
        ...

    def get(self, receipt_id: int) -> Optional[Receipt]:
        """Get receipt by ID"""
        ...

    def add_item(self, receipt_id: int, product_id: int, quantity: int) -> Receipt:
        """Add item to receipt"""
        ...

    def update_status(self, receipt_id: int, status: ReceiptStatus) -> Receipt:
        """Update receipt status"""
        ...

    def add_payment(self, receipt_id: int, payment: Payment) -> Receipt:
        """Add payment to receipt"""
        ...

    def get_receipts_by_shift(self, shift_id: int) -> List[Receipt]:
        """Get all receipts for a shift"""
        ...