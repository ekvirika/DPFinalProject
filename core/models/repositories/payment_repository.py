from typing import Protocol, Optional, List

from core.models.receipt import Currency, Payment


class PaymentRepository(Protocol):
    def create(self, receipt_id: str, amount: float, currency: Currency,
              total_in_gel: float, exchange_rate: float) -> Payment:
        ...

    def update_status(self, payment_id: str, status: str) -> Optional[Payment]:
        ...

    def get_by_receipt(self, receipt_id: str) -> List[Payment]:
        ...