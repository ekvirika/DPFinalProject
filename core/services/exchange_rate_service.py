from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import requests

from core.models.receipt import Currency, Quote


class ExchangeRateService:

    def __init__(self, receipt_repository) -> None:
        self.receipt_repository = receipt_repository
        self.base_url = "https://api.exchangerate-api.com/v4/latest/GEL"
        self.rates_cache = {}
        self.last_update = None


    def _update_rates(self) -> None:
        """Update the exchange rates if needed (once per day)"""
        current_time = datetime.now()

        # If we haven't updated today or don't have rates yet
        if (not self.last_update or
                current_time.date() != self.last_update.date() or
                not self.rates_cache):

            try:
                response = requests.get(self.base_url)
                data = response.json()

                if "rates" in data:
                    self.rates_cache = data["rates"]
                    self.last_update = current_time
            except Exception as e:
                # If API call fails, use hardcoded rates as fallback
                self.rates_cache = {
                    "GEL": 1.0,
                    "USD": 0.37,  # Example rate
                    "EUR": 0.34  # Example rate
                }
                self.last_update = current_time


    def get_exchange_rate(self, from_currency: Currency, to_currency: Currency) -> float:
        """Get the exchange rate between two currencies"""
        self._update_rates()

        # GEL to X rate
        if from_currency == Currency.GEL:
            return self.rates_cache.get(to_currency.value, 1.0)

        # X to GEL rate
        if to_currency == Currency.GEL:
            return 1.0 / self.rates_cache.get(from_currency.value, 1.0)

        # X to Y rate (convert via GEL)
        from_rate = self.rates_cache.get(from_currency.value, 1.0)
        to_rate = self.rates_cache.get(to_currency.value, 1.0)

        return to_rate / from_rate


    def convert(self, amount: float, from_currency: Currency, to_currency: Currency) -> float:
        """Convert an amount from one currency to another"""
        rate = self.get_exchange_rate(from_currency, to_currency)
        return amount * rate


    def calculate_quote(self, receipt_id: UUID, currency: Currency) -> Optional[Quote]:
        """Calculate a payment quote for a receipt in the requested currency"""
        receipt = self.receipt_repository.get_by_id(receipt_id)

        if not receipt:
            return None

        base_currency = Currency.GEL
        exchange_rate = self.get_exchange_rate(base_currency, currency)

        return Quote(
            receipt_id=receipt_id,
            base_currency=base_currency,
            requested_currency=currency,
            exchange_rate=exchange_rate,
            total_in_base_currency=receipt.total,
            total_in_requested_currency=receipt.total * exchange_rate
        )