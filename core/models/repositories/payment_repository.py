from typing import List, Protocol
from uuid import UUID

from core.models.receipt import Currency, Payment


class PaymentRepository(Protocol):
    def create(
        self,
        receipt_id: UUID,
        amount: float,
        currency: Currency,
        total_in_gel: float,
        exchange_rate: float,
    ) -> Payment: ...

    def update_status(self, payment_id: UUID, status: str) -> Payment: ...

    def get_by_receipt(self, receipt_id: UUID) -> List[Payment]: ...
