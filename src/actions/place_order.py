"""
Place Order action — order food, products, or services.
"""

import random
from datetime import datetime, timedelta
from actions.base import BaseAction


class PlaceOrderAction(BaseAction):

    def describe(self):
        return "Place an order for food, products, or services"

    def examples(self):
        return [
            "order a pizza",
            "buy groceries",
            "order coffee from Starbucks",
            "get me a burger",
            "purchase headphones",
        ]

    def get_required_fields(self):
        return [
            ("item", "What would you like to order?"),
            ("quantity", "How many? (default: 1)"),
        ]

    def execute(self, details):
        item = details.get("item", "Unknown item")
        quantity = details.get("quantity", "1")
        source = details.get("from", "nearest available store")

        try:
            qty = int(quantity)
        except (ValueError, TypeError):
            qty = 1

        summary = f"Order {qty}x {item} from {source}"
        if not self.confirm(summary):
            return False, "Order cancelled."

        order_id = f"ORD-{random.randint(10000, 99999)}"
        eta = datetime.now() + timedelta(minutes=random.randint(15, 45))
        price = round(random.uniform(5.99, 49.99) * qty, 2)

        result = (
            f"🛒 Order placed successfully!\n"
            f"   Order ID: {order_id}\n"
            f"   Item: {qty}x {item}\n"
            f"   From: {source}\n"
            f"   Total: ${price:.2f}\n"
            f"   ETA: {eta.strftime('%H:%M')}\n"
            f"   Status: Confirmed ✓"
        )
        return True, result
