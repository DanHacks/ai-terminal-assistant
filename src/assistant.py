"""
ElectroPOS - POS Assistant
Quick-access helper functions for common POS operations.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from database import init_db, get_session, seed_database
from product_manager import ProductManager
from inventory_manager import InventoryManager
from customer_manager import CustomerManager
from sales_manager import SalesManager
from reports import ReportManager
from cart import Cart


class POSAssistant:
    """High-level API for POS operations, useful for scripting and testing."""

    def __init__(self, settings=None):
        self.settings = settings or {}
        init_db(settings)
        self.products = ProductManager()
        self.inventory = InventoryManager(settings)
        self.customers = CustomerManager(settings)
        self.sales = SalesManager(settings)
        self.reports = ReportManager(settings)

    def quick_sale(self, employee_id: int, items: list,
                   payment_method: str = "cash", cash_tendered: float = None,
                   customer_id: int = None) -> dict:
        """
        Process a quick sale programmatically.

        Args:
            employee_id: ID of the employee processing the sale
            items: List of dicts with 'product_id' and 'quantity'
            payment_method: 'cash', 'card', or 'split'
            cash_tendered: Amount of cash given (for cash payments)
            customer_id: Optional customer ID for loyalty

        Returns:
            Sale result dict
        """
        cart = Cart(self.settings)

        if customer_id:
            cust = self.customers.get_customer(customer_id=customer_id)
            if cust:
                cart.set_customer(cust["id"], cust["name"])

        for item in items:
            result = cart.add_item(
                product_id=item["product_id"],
                quantity=item.get("quantity", 1)
            )
            if not result["success"]:
                return {"success": False, "error": f"Failed to add item: {result['error']}"}

        if payment_method == "cash" and cash_tendered is None:
            cash_tendered = cart.total

        return self.sales.complete_sale(
            cart=cart,
            employee_id=employee_id,
            payment_method=payment_method,
            cash_tendered=cash_tendered or 0,
        )

    def get_dashboard(self) -> dict:
        """Get a quick dashboard summary."""
        today = self.reports.sales_summary("today")
        inv = self.inventory.get_inventory_summary()
        low_stock = self.inventory.get_low_stock_alerts()

        return {
            "sales_today": today,
            "inventory": inv,
            "low_stock_alerts": len(low_stock),
            "low_stock_items": low_stock[:5],
        }

    def seed_demo_data(self):
        """Seed the database with demo data."""
        session = get_session()
        result = seed_database(session)
        session.close()
        return result
