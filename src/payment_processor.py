"""
ElectroPOS - Payment Processor
Handles cash, card, and split payment processing.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from models import PaymentMethod


class PaymentResult:
    """Result of a payment processing attempt."""

    def __init__(self, success: bool, method: PaymentMethod, amount: float,
                 change: float = 0.0, reference: str = "",
                 card_last_four: str = None, error: str = ""):
        self.success = success
        self.method = method
        self.amount = amount
        self.change = change
        self.reference = reference
        self.card_last_four = card_last_four
        self.error = error

    def to_dict(self):
        return {
            "success": self.success,
            "method": self.method.value,
            "amount": self.amount,
            "change": self.change,
            "reference": self.reference,
            "card_last_four": self.card_last_four,
            "error": self.error,
        }


class PaymentProcessor:
    """Processes payments for POS transactions."""

    def __init__(self, settings=None):
        self.settings = settings or {}
        currency = self.settings.get("currency", {})
        self.currency_symbol = currency.get("symbol", "$")

    def process_cash(self, total: float, tendered: float) -> PaymentResult:
        if tendered < total:
            return PaymentResult(
                success=False,
                method=PaymentMethod.CASH,
                amount=tendered,
                error=f"Insufficient cash. Need {self.currency_symbol}{total:.2f}, received {self.currency_symbol}{tendered:.2f}"
            )

        change = round(tendered - total, 2)
        return PaymentResult(
            success=True,
            method=PaymentMethod.CASH,
            amount=total,
            change=change,
        )

    def process_card(self, total: float, card_last_four: str = "****") -> PaymentResult:
        if len(card_last_four) != 4:
            card_last_four = card_last_four[-4:] if len(card_last_four) >= 4 else "****"

        return PaymentResult(
            success=True,
            method=PaymentMethod.CARD,
            amount=total,
            card_last_four=card_last_four,
            reference=f"CARD-{card_last_four}",
        )

    def process_split(self, total: float, cash_amount: float,
                      card_amount: float = None, card_last_four: str = "****") -> dict:
        if card_amount is None:
            card_amount = round(total - cash_amount, 2)

        if cash_amount < 0 or card_amount < 0:
            return {
                "success": False,
                "error": "Payment amounts cannot be negative."
            }

        total_payment = round(cash_amount + card_amount, 2)
        if total_payment < total:
            return {
                "success": False,
                "error": f"Total payment ({self.currency_symbol}{total_payment:.2f}) is less than amount due ({self.currency_symbol}{total:.2f})."
            }

        change = round(total_payment - total, 2)

        cash_result = PaymentResult(
            success=True,
            method=PaymentMethod.CASH,
            amount=cash_amount,
            change=change,
        )

        card_result = PaymentResult(
            success=True,
            method=PaymentMethod.CARD,
            amount=card_amount,
            card_last_four=card_last_four,
            reference=f"CARD-{card_last_four}",
        )

        return {
            "success": True,
            "method": PaymentMethod.SPLIT,
            "cash": cash_result.to_dict(),
            "card": card_result.to_dict(),
            "total_paid": total_payment,
            "change": change,
        }

    def calculate_change_breakdown(self, change: float) -> list:
        """Break down change into denominations."""
        denominations = [100, 50, 20, 10, 5, 1, 0.25, 0.10, 0.05, 0.01]
        labels = ["$100", "$50", "$20", "$10", "$5", "$1", "25¢", "10¢", "5¢", "1¢"]
        breakdown = []
        remaining = round(change * 100)  # Work in cents

        for denom, label in zip(denominations, labels):
            cents = round(denom * 100)
            count = int(remaining // cents)
            if count > 0:
                breakdown.append({"denomination": label, "count": count})
                remaining -= count * cents

        return breakdown

    def format_amount(self, amount: float) -> str:
        return f"{self.currency_symbol}{amount:.2f}"
