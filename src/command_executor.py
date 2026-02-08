"""
ElectroPOS - Command Executor
Executes parsed POS commands against the cart and system.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from command_parser import parse_pos_command


class CommandExecutor:
    """Executes POS commands on the cart."""

    def __init__(self, cart, product_manager, customer_manager):
        self.cart = cart
        self.products = product_manager
        self.customers = customer_manager

    def execute(self, raw_input: str) -> dict:
        cmd = parse_pos_command(raw_input)
        action = cmd["action"]
        args = cmd["args"]

        if action is None:
            return {"success": False, "message": "No command entered."}

        handler = getattr(self, f"_handle_{action}", None)
        if handler:
            return handler(args)

        return {"success": False, "message": f"Unknown command: {action}"}

    def _handle_add_item(self, args: list) -> dict:
        if not args:
            return {"success": False, "message": "Usage: add <sku/barcode/id> [quantity]"}

        lookup = args[0]
        qty = int(args[1]) if len(args) > 1 and args[1].isdigit() else 1

        result = None
        if lookup.isdigit():
            result = self.cart.add_item(product_id=int(lookup), quantity=qty)
        if not result or not result.get("success"):
            result = self.cart.add_item(sku=lookup, quantity=qty)
        if not result.get("success"):
            result = self.cart.add_item(barcode=lookup, quantity=qty)

        return result

    def _handle_remove_item(self, args: list) -> dict:
        if not args or not args[0].isdigit():
            return {"success": False, "message": "Usage: del <item#>"}
        idx = int(args[0]) - 1
        if 0 <= idx < len(self.cart.items):
            return self.cart.remove_item(self.cart.items[idx].product_id)
        return {"success": False, "message": "Invalid item number."}

    def _handle_update_quantity(self, args: list) -> dict:
        if len(args) < 2:
            return {"success": False, "message": "Usage: qty <item#> <quantity>"}
        try:
            idx = int(args[0]) - 1
            qty = int(args[1])
            if 0 <= idx < len(self.cart.items):
                return self.cart.update_quantity(self.cart.items[idx].product_id, qty)
            return {"success": False, "message": "Invalid item number."}
        except ValueError:
            return {"success": False, "message": "Invalid numbers."}

    def _handle_item_discount(self, args: list) -> dict:
        if len(args) < 2:
            return {"success": False, "message": "Usage: disc <item#> <percent>"}
        try:
            idx = int(args[0]) - 1
            pct = float(args[1])
            if 0 <= idx < len(self.cart.items):
                return self.cart.apply_item_discount(self.cart.items[idx].product_id, percent=pct)
            return {"success": False, "message": "Invalid item number."}
        except ValueError:
            return {"success": False, "message": "Invalid numbers."}

    def _handle_cart_discount(self, args: list) -> dict:
        if not args:
            return {"success": False, "message": "Usage: cartdisc <percent>"}
        try:
            pct = float(args[0])
            return self.cart.apply_cart_discount(percent=pct)
        except ValueError:
            return {"success": False, "message": "Invalid discount percent."}

    def _handle_search(self, args: list) -> dict:
        if not args:
            return {"success": False, "message": "Usage: search <query>"}
        query = " ".join(args)
        results = self.products.search_products(query)
        return {"success": True, "results": results, "message": f"Found {len(results)} products."}

    def _handle_clear_cart(self, args: list) -> dict:
        self.cart.clear()
        return {"success": True, "message": "Cart cleared."}

    def _handle_cancel(self, args: list) -> dict:
        self.cart.clear()
        return {"success": True, "message": "Sale cancelled.", "action": "cancel"}

    def _handle_payment(self, args: list) -> dict:
        if self.cart.is_empty:
            return {"success": False, "message": "Cart is empty."}
        return {"success": True, "message": "Proceeding to payment.", "action": "payment"}

    def _handle_help(self, args: list) -> dict:
        from command_parser import get_help_text
        return {"success": True, "message": get_help_text()}
