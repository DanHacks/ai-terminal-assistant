"""
ElectroPOS - Receipt Generator
Generates formatted text receipts for transactions.
"""

import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))


class ReceiptGenerator:
    """Generates formatted text receipts."""

    def __init__(self, settings=None):
        self.settings = settings or {}
        store = self.settings.get("store", {})
        self.store_name = store.get("name", "ElectroPOS Store")
        self.store_address = store.get("address", "")
        self.store_city = store.get("city", "")
        self.store_phone = store.get("phone", "")
        self.store_email = store.get("email", "")
        self.store_website = store.get("website", "")

        receipt = self.settings.get("receipt", {})
        self.width = receipt.get("width", 48)
        self.show_tax = receipt.get("show_tax_breakdown", True)
        self.show_savings = receipt.get("show_savings", True)
        self.footer_msg = receipt.get("footer_message", "Thank you for shopping with us!")

        currency = self.settings.get("currency", {})
        self.symbol = currency.get("symbol", "$")

    def _center(self, text: str) -> str:
        return text.center(self.width)

    def _line(self, char: str = "-") -> str:
        return char * self.width

    def _left_right(self, left: str, right: str) -> str:
        space = self.width - len(left) - len(right)
        if space < 1:
            space = 1
        return left + " " * space + right

    def _format_money(self, amount: float) -> str:
        return f"{self.symbol}{amount:.2f}"

    def generate(self, sale_data: dict) -> str:
        lines = []

        # ── Header ──
        lines.append("")
        lines.append(self._line("="))
        lines.append(self._center(self.store_name.upper()))
        lines.append(self._line("="))
        if self.store_address:
            lines.append(self._center(self.store_address))
        if self.store_city:
            lines.append(self._center(self.store_city))
        if self.store_phone:
            lines.append(self._center(f"Tel: {self.store_phone}"))
        if self.store_website:
            lines.append(self._center(self.store_website))
        lines.append(self._line("-"))

        # ── Transaction Info ──
        lines.append(self._left_right(
            f"TXN: {sale_data.get('transaction_id', 'N/A')}",
            sale_data.get("date", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"))
        ))
        lines.append(self._left_right(
            f"Cashier: {sale_data.get('employee_name', 'N/A')}",
            f"#{sale_data.get('sale_id', '')}"
        ))
        if sale_data.get("customer_name"):
            lines.append(f"Customer: {sale_data['customer_name']}")
        lines.append(self._line("-"))

        # ── Items ──
        lines.append(self._left_right("ITEM", "AMOUNT"))
        lines.append(self._line("-"))

        for item in sale_data.get("items", []):
            name = item["name"]
            if len(name) > 30:
                name = name[:27] + "..."
            qty = item["quantity"]
            price = item["unit_price"]
            total = item["line_total"]

            lines.append(name)
            qty_line = f"  {qty} x {self._format_money(price)}"
            lines.append(self._left_right(qty_line, self._format_money(total)))

            if item.get("discount_amount", 0) > 0:
                lines.append(self._left_right(
                    "    DISCOUNT",
                    f"-{self._format_money(item['discount_amount'])}"
                ))

        lines.append(self._line("-"))

        # ── Totals ──
        subtotal = sale_data.get("subtotal", 0)
        lines.append(self._left_right("Subtotal:", self._format_money(subtotal)))

        discount = sale_data.get("discount_amount", 0)
        if discount > 0 and self.show_savings:
            lines.append(self._left_right("Discount:", f"-{self._format_money(discount)}"))

        loyalty_discount = sale_data.get("loyalty_discount", 0)
        if loyalty_discount > 0:
            lines.append(self._left_right("Loyalty Discount:", f"-{self._format_money(loyalty_discount)}"))

        if self.show_tax:
            tax = sale_data.get("tax_amount", 0)
            tax_rate = sale_data.get("tax_rate", 0.08)
            lines.append(self._left_right(
                f"Tax ({tax_rate * 100:.1f}%):",
                self._format_money(tax)
            ))

        lines.append(self._line("="))
        total = sale_data.get("total", 0)
        lines.append(self._left_right("TOTAL:", self._format_money(total)))
        lines.append(self._line("="))

        # ── Payment ──
        payment_method = sale_data.get("payment_method", "cash")
        lines.append("")
        lines.append(self._left_right("Payment:", payment_method.upper()))

        if payment_method == "cash":
            tendered = sale_data.get("cash_tendered", 0)
            change = sale_data.get("change_due", 0)
            lines.append(self._left_right("Tendered:", self._format_money(tendered)))
            lines.append(self._left_right("Change:", self._format_money(change)))
        elif payment_method == "card":
            card = sale_data.get("card_last_four", "****")
            lines.append(self._left_right("Card:", f"**** **** **** {card}"))
        elif payment_method == "split":
            for p in sale_data.get("payments", []):
                lines.append(self._left_right(
                    f"  {p['method'].upper()}:",
                    self._format_money(p['amount'])
                ))

        # ── Loyalty ──
        if sale_data.get("loyalty_points_earned", 0) > 0:
            lines.append("")
            lines.append(self._line("-"))
            lines.append(self._center("LOYALTY REWARDS"))
            lines.append(self._left_right(
                "Points Earned:",
                str(sale_data["loyalty_points_earned"])
            ))
            if sale_data.get("loyalty_points_balance") is not None:
                lines.append(self._left_right(
                    "Points Balance:",
                    str(sale_data["loyalty_points_balance"])
                ))

        # ── Savings Summary ──
        total_savings = discount + loyalty_discount
        if total_savings > 0 and self.show_savings:
            lines.append("")
            lines.append(self._center(f"*** YOU SAVED {self._format_money(total_savings)} ***"))

        # ── Footer ──
        lines.append("")
        lines.append(self._line("-"))
        lines.append(self._center(self.footer_msg))
        lines.append(self._center(datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")))
        lines.append(self._line("="))
        lines.append("")

        return "\n".join(lines)

    def generate_return_receipt(self, return_data: dict) -> str:
        lines = []

        lines.append("")
        lines.append(self._line("="))
        lines.append(self._center(self.store_name.upper()))
        lines.append(self._center("*** RETURN / REFUND ***"))
        lines.append(self._line("="))
        lines.append(self._left_right(
            f"Return ID: {return_data.get('return_id', 'N/A')}",
            return_data.get("date", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"))
        ))
        lines.append(self._left_right(
            f"Original TXN: {return_data.get('original_transaction_id', 'N/A')}",
            ""
        ))
        lines.append(self._left_right(
            f"Cashier: {return_data.get('employee_name', 'N/A')}",
            ""
        ))
        lines.append(self._line("-"))

        lines.append(self._left_right("RETURNED ITEM", "REFUND"))
        lines.append(self._line("-"))

        product = return_data.get("product_name", "Unknown")
        qty = return_data.get("quantity", 0)
        refund = return_data.get("refund_amount", 0)

        lines.append(product)
        lines.append(self._left_right(f"  Qty: {qty}", self._format_money(refund)))
        lines.append(self._left_right("Reason:", return_data.get("reason", "N/A")))

        lines.append(self._line("="))
        lines.append(self._left_right("REFUND TOTAL:", self._format_money(refund)))
        lines.append(self._line("="))

        lines.append("")
        lines.append(self._line("-"))
        lines.append(self._center(self.footer_msg))
        lines.append(self._line("="))
        lines.append("")

        return "\n".join(lines)
