"""
ElectroPOS - Shopping Cart
Cart management with discount and tax calculation.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from models import Product
from database import get_session


class CartItem:
    """Represents a single item in the cart."""

    def __init__(self, product_id: int, name: str, sku: str, price: float,
                 quantity: int = 1, taxable: bool = True, cost: float = 0.0):
        self.product_id = product_id
        self.name = name
        self.sku = sku
        self.price = price
        self.cost = cost
        self.quantity = quantity
        self.taxable = taxable
        self.discount_amount = 0.0
        self.discount_percent = 0.0

    @property
    def subtotal(self):
        return round(self.price * self.quantity, 2)

    @property
    def discount_total(self):
        if self.discount_percent > 0:
            return round(self.subtotal * (self.discount_percent / 100), 2)
        return round(self.discount_amount * self.quantity, 2)

    @property
    def taxable_amount(self):
        return round(self.subtotal - self.discount_total, 2)

    @property
    def line_total(self):
        return round(self.subtotal - self.discount_total, 2)

    def to_dict(self):
        return {
            "product_id": self.product_id,
            "name": self.name,
            "sku": self.sku,
            "price": self.price,
            "quantity": self.quantity,
            "subtotal": self.subtotal,
            "discount": self.discount_total,
            "line_total": self.line_total,
            "taxable": self.taxable,
        }


class Cart:
    """Shopping cart with full discount and tax support."""

    def __init__(self, settings=None):
        self.settings = settings or {}
        self.items: list[CartItem] = []
        self.customer_id = None
        self.customer_name = None
        self.cart_discount_percent = 0.0
        self.cart_discount_amount = 0.0
        self.loyalty_discount = 0.0

        tax_settings = self.settings.get("tax", {})
        self.tax_rate = tax_settings.get("rate", 0.08)
        self.tax_enabled = tax_settings.get("enabled", True)

    def add_item(self, product_id: int = None, sku: str = None,
                 barcode: str = None, quantity: int = 1) -> dict:
        session = get_session()
        try:
            query = session.query(Product)
            if product_id:
                product = query.get(product_id)
            elif sku:
                product = query.filter(Product.sku == sku).first()
            elif barcode:
                product = query.filter(Product.barcode == barcode).first()
            else:
                return {"success": False, "error": "Provide product_id, sku, or barcode."}

            if not product:
                return {"success": False, "error": "Product not found."}
            if not product.is_active:
                return {"success": False, "error": f"Product '{product.name}' is inactive."}
            if product.stock_quantity < quantity:
                return {
                    "success": False,
                    "error": f"Insufficient stock for '{product.name}'. Available: {product.stock_quantity}"
                }

            # Check if already in cart
            for item in self.items:
                if item.product_id == product.id:
                    new_qty = item.quantity + quantity
                    if product.stock_quantity < new_qty:
                        return {
                            "success": False,
                            "error": f"Insufficient stock. Available: {product.stock_quantity}, In cart: {item.quantity}"
                        }
                    item.quantity = new_qty
                    return {
                        "success": True,
                        "message": f"Updated '{product.name}' quantity to {new_qty}.",
                        "item": item.to_dict(),
                    }

            cart_item = CartItem(
                product_id=product.id,
                name=product.name,
                sku=product.sku,
                price=product.price,
                cost=product.cost,
                quantity=quantity,
                taxable=product.is_taxable,
            )
            self.items.append(cart_item)

            return {
                "success": True,
                "message": f"Added '{product.name}' x{quantity} to cart.",
                "item": cart_item.to_dict(),
            }
        finally:
            session.close()

    def remove_item(self, product_id: int) -> dict:
        for i, item in enumerate(self.items):
            if item.product_id == product_id:
                removed = self.items.pop(i)
                return {"success": True, "message": f"Removed '{removed.name}' from cart."}
        return {"success": False, "error": "Item not found in cart."}

    def update_quantity(self, product_id: int, quantity: int) -> dict:
        if quantity <= 0:
            return self.remove_item(product_id)

        session = get_session()
        try:
            for item in self.items:
                if item.product_id == product_id:
                    product = session.query(Product).get(product_id)
                    if product and product.stock_quantity < quantity:
                        return {
                            "success": False,
                            "error": f"Insufficient stock. Available: {product.stock_quantity}"
                        }
                    item.quantity = quantity
                    return {
                        "success": True,
                        "message": f"Updated '{item.name}' quantity to {quantity}.",
                        "item": item.to_dict(),
                    }
            return {"success": False, "error": "Item not found in cart."}
        finally:
            session.close()

    def apply_item_discount(self, product_id: int, percent: float = 0,
                            amount: float = 0) -> dict:
        for item in self.items:
            if item.product_id == product_id:
                if percent > 0:
                    item.discount_percent = min(percent, 100)
                    item.discount_amount = 0
                    return {"success": True, "message": f"{percent}% discount applied to '{item.name}'."}
                elif amount > 0:
                    item.discount_amount = min(amount, item.price)
                    item.discount_percent = 0
                    return {"success": True, "message": f"${amount:.2f} discount applied to '{item.name}'."}
        return {"success": False, "error": "Item not found in cart."}

    def apply_cart_discount(self, percent: float = 0, amount: float = 0) -> dict:
        if percent > 0:
            self.cart_discount_percent = min(percent, 100)
            self.cart_discount_amount = 0
            return {"success": True, "message": f"{percent}% cart discount applied."}
        elif amount > 0:
            self.cart_discount_amount = amount
            self.cart_discount_percent = 0
            return {"success": True, "message": f"${amount:.2f} cart discount applied."}
        return {"success": False, "error": "Provide a discount percent or amount."}

    def set_customer(self, customer_id: int, customer_name: str):
        self.customer_id = customer_id
        self.customer_name = customer_name

    def clear_customer(self):
        self.customer_id = None
        self.customer_name = None

    def set_loyalty_discount(self, amount: float):
        self.loyalty_discount = amount

    def clear(self):
        self.items.clear()
        self.customer_id = None
        self.customer_name = None
        self.cart_discount_percent = 0.0
        self.cart_discount_amount = 0.0
        self.loyalty_discount = 0.0

    @property
    def is_empty(self):
        return len(self.items) == 0

    @property
    def item_count(self):
        return sum(item.quantity for item in self.items)

    @property
    def subtotal(self):
        return round(sum(item.line_total for item in self.items), 2)

    @property
    def total_item_discounts(self):
        return round(sum(item.discount_total for item in self.items), 2)

    @property
    def cart_discount(self):
        sub = self.subtotal
        if self.cart_discount_percent > 0:
            return round(sub * (self.cart_discount_percent / 100), 2)
        return min(self.cart_discount_amount, sub)

    @property
    def total_discounts(self):
        return round(self.total_item_discounts + self.cart_discount + self.loyalty_discount, 2)

    @property
    def taxable_subtotal(self):
        taxable = sum(item.line_total for item in self.items if item.taxable)
        taxable -= self.cart_discount
        return max(round(taxable, 2), 0)

    @property
    def tax_amount(self):
        if not self.tax_enabled:
            return 0.0
        return round(self.taxable_subtotal * self.tax_rate, 2)

    @property
    def total(self):
        return round(self.subtotal - self.cart_discount - self.loyalty_discount + self.tax_amount, 2)

    def get_summary(self) -> dict:
        return {
            "items": [item.to_dict() for item in self.items],
            "item_count": self.item_count,
            "subtotal": self.subtotal,
            "item_discounts": self.total_item_discounts,
            "cart_discount": self.cart_discount,
            "loyalty_discount": self.loyalty_discount,
            "total_discounts": self.total_discounts,
            "tax_rate": self.tax_rate,
            "tax_amount": self.tax_amount,
            "total": self.total,
            "customer_id": self.customer_id,
            "customer_name": self.customer_name,
        }
