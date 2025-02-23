from datetime import datetime
from typing import List
from uuid import UUID

from core.models.receipt import Receipt, ReceiptStatus, PaymentCurrency, Payment
from core.models.repositories.receipt_repository import ReceiptRepository


class ReceiptService:
    def __init__(
        self,
        receipt_repo: ReceiptRepository,
        exchange_service: "ExchangeService",
        campaign_service: "CampaignService"
    ):
        self._receipt_repo = receipt_repo
        self._exchange_service = exchange_service
        self._campaign_service = campaign_service

    def create_receipt(self, shift_id: UUID) -> Receipt:
        return self._receipt_repo.create(shift_id)

    def add_item(self, receipt_id: UUID, product_id: UUID, quantity: int) -> Receipt:
        receipt = self._receipt_repo.get(receipt_id)
        if not receipt:
            raise ValueError(f"Receipt {receipt_id} not found")

        if receipt.status != ReceiptStatus.OPEN:
            raise ValueError(f"Cannot add items to receipt in {receipt.status} status")

        return self._receipt_repo.add_item(receipt_id, product_id, quantity)

    def calculate_payment(self, receipt_id: UUID, currency: PaymentCurrency) -> float:
        receipt = self._receipt_repo.get(receipt_id)
        if not receipt:
            raise ValueError(f"Receipt {receipt_id} not found")

        if currency == PaymentCurrency.GEL:
            return round(receipt.total_amount, 2)

        exchange_rate = self._exchange_service.get_rate(PaymentCurrency.GEL, currency)
        return round(receipt.total_amount * exchange_rate, 2)

    def add_payment(
        self, receipt_id: UUID, amount: float, currency: PaymentCurrency
    ) -> Receipt:
        receipt = self._receipt_repo.get(receipt_id)
        if not receipt:
            raise ValueError(f"Receipt {receipt_id} not found")

        if receipt.status != ReceiptStatus.PENDING_PAYMENT:
            raise ValueError(f"Cannot add payment to receipt in {receipt.status} status")

        exchange_rate = (
            1.0 if currency == PaymentCurrency.GEL
            else self._exchange_service.get_rate(PaymentCurrency.GEL, currency)
        )

        payment = Payment(
            amount=amount,
            currency=currency,
            exchange_rate=exchange_rate,
            timestamp=datetime.now()
        )

        gel_amount = round(amount * exchange_rate, 2)
        if gel_amount < receipt.total_amount:
            raise ValueError("Payment amount is insufficient")

        return self._receipt_repo.add_payment(receipt_id, payment)

    def close_receipt(self, receipt_id: UUID) -> Receipt:
        receipt = self._receipt_repo.get(receipt_id)
        if not receipt:
            raise ValueError(f"Receipt {receipt_id} not found")

        if receipt.status != ReceiptStatus.PENDING_PAYMENT:
            raise ValueError(f"Cannot close receipt in {receipt.status} status")

        total_paid = round(
            sum(payment.amount * payment.exchange_rate for payment in receipt.payments),
            2
        )
        if total_paid < receipt.total_amount:
            raise ValueError("Total payment is insufficient")

        return self._receipt_repo.update_status(receipt_id, ReceiptStatus.PAID)

    def get_shift_receipts(self, shift_id: UUID) -> List[Receipt]:
        return self._receipt_repo.get_receipts_by_shift(shift_id)
