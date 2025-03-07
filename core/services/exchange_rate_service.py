from datetime import datetime
from typing import Dict, Optional

import requests

from core.models.receipt import Currency, Quote, Receipt


class ExchangeRateService:
    """Service for handling currency exchange rates and conversions."""

    def __init__(self) -> None:
        self.base_url = "https://api.exchangerate-api.com/v4/latest/GEL"
        self.rates_cache: Dict[str, float] = {}
        self.last_update: Optional[datetime] = None

    def _update_rates(self) -> None:
        """Update the exchange rates if needed (once per day)"""
        current_time = datetime.now()

        # If we haven't updated today or don't have rates yet
        if (
            not self.last_update
            or current_time.date() != self.last_update.date()
            or not self.rates_cache
        ):
            try:
                response = requests.get(self.base_url, timeout=10)
                data = response.json()

                if "rates" in data:
                    self.rates_cache = data["rates"]
                    self.last_update = current_time
                    print(self.rates_cache)
            except Exception:
                # If API call fails, use hardcoded rates as fallback
                self.rates_cache = {
                    "GEL": 1.0,
                    "USD": 0.37,
                    "EUR": 0.34,
                }
                self.last_update = current_time

    def get_exchange_rate(
        self, from_currency: Currency, to_currency: Currency
    ) -> float:
        """Get the exchange rate between two currencies"""
        self._update_rates()

        # Same currency, no conversion needed
        if from_currency == to_currency:
            return 1.0

        # GEL to X rate
        if from_currency == Currency.GEL:
            return float(self.rates_cache.get(to_currency.value, 1.0))

        # X to GEL rate
        if to_currency == Currency.GEL:
            from_rate = float(self.rates_cache.get(from_currency.value, 1.0))
            return 1.0 / from_rate if from_rate != 0 else 1.0

        # X to Y rate (convert via GEL)
        from_rate = float(self.rates_cache.get(from_currency.value, 1.0))
        to_rate = float(self.rates_cache.get(to_currency.value, 1.0))

        return to_rate / from_rate if from_rate != 0 else to_rate

    def convert(
        self, amount: float, from_currency: Currency, to_currency: Currency
    ) -> float:
        """Convert an amount from one currency to another"""
        rate = self.get_exchange_rate(from_currency, to_currency)
        return amount * rate

    def calculate_quote(self, receipt: Receipt, currency: Currency) -> Quote:
        """Calculate a payment quote for a receipt in the requested currency"""
        base_currency = Currency.GEL
        exchange_rate = self.get_exchange_rate(base_currency, currency)

        return Quote(
            receipt_id=receipt.id,
            base_currency=base_currency,
            requested_currency=currency,
            exchange_rate=exchange_rate,
            total_in_base_currency=receipt.total,
            total_in_requested_currency=receipt.total * exchange_rate,
        )
