"""
ElectroPOS - Inventory Manager
Stock tracking, adjustments, alerts, and history.
"""

import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))

from models import Product, InventoryLog
from database import get_session


class InventoryManager:
    """Manages inventory stock levels and tracking."""

    def __init__(self, settings=None):
        self.settings = settings or {}
        inv_settings = self.settings.get("inventory", {})
        self.low_stock_threshold = inv_settings.get("low_stock_threshold", 10)
        self.track_history = inv_settings.get("track_history", True)

    def _log_change(self, session, product_id: int, change_type: str,
                    qty_change: int, qty_before: int, qty_after: int,
                    reference: str = "", notes: str = ""):
        if not self.track_history:
            return
        log = InventoryLog(
            product_id=product_id,
            change_type=change_type,
            quantity_change=qty_change,
            quantity_before=qty_before,
            quantity_after=qty_after,
            reference=reference,
            notes=notes,
        )
        session.add(log)

    def adjust_stock(self, product_id: int, quantity: int, reason: str = "manual_adjustment",
                     reference: str = "", notes: str = "") -> dict:
        session = get_session()
        try:
            product = session.query(Product).get(product_id)
            if not product:
                return {"success": False, "error": "Product not found."}

            qty_before = product.stock_quantity
            product.stock_quantity += quantity
            if product.stock_quantity < 0:
                product.stock_quantity = 0
            qty_after = product.stock_quantity

            self._log_change(session, product_id, reason, quantity, qty_before, qty_after, reference, notes)
            session.commit()

            return {
                "success": True,
                "product": product.name,
                "before": qty_before,
                "after": qty_after,
                "change": quantity,
            }
        except Exception as e:
            session.rollback()
            return {"success": False, "error": str(e)}
        finally:
            session.close()

    def restock(self, product_id: int, quantity: int, reference: str = "") -> dict:
        if quantity <= 0:
            return {"success": False, "error": "Restock quantity must be positive."}
        return self.adjust_stock(product_id, quantity, "restock", reference, f"Restocked {quantity} units")

    def deduct_stock(self, product_id: int, quantity: int, reference: str = "") -> dict:
        if quantity <= 0:
            return {"success": False, "error": "Deduction quantity must be positive."}

        session = get_session()
        try:
            product = session.query(Product).get(product_id)
            if not product:
                return {"success": False, "error": "Product not found."}
            if product.stock_quantity < quantity:
                return {
                    "success": False,
                    "error": f"Insufficient stock. Available: {product.stock_quantity}, Requested: {quantity}"
                }
            session.close()
            return self.adjust_stock(product_id, -quantity, "sale", reference, f"Sold {quantity} units")
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            if session.is_active:
                session.close()

    def return_stock(self, product_id: int, quantity: int, reference: str = "") -> dict:
        if quantity <= 0:
            return {"success": False, "error": "Return quantity must be positive."}
        return self.adjust_stock(product_id, quantity, "return", reference, f"Returned {quantity} units")

    def get_stock_level(self, product_id: int) -> dict:
        session = get_session()
        try:
            product = session.query(Product).get(product_id)
            if not product:
                return {"success": False, "error": "Product not found."}
            return {
                "success": True,
                "product": product.name,
                "sku": product.sku,
                "stock": product.stock_quantity,
                "min_stock": product.min_stock_level,
                "is_low": product.stock_quantity <= product.min_stock_level,
            }
        finally:
            session.close()

    def get_low_stock_alerts(self) -> list:
        session = get_session()
        try:
            products = (
                session.query(Product)
                .filter(
                    Product.is_active == True,
                    Product.stock_quantity <= Product.min_stock_level
                )
                .order_by(Product.stock_quantity)
                .all()
            )
            return [
                {
                    "id": p.id,
                    "sku": p.sku,
                    "name": p.name,
                    "stock": p.stock_quantity,
                    "min_stock": p.min_stock_level,
                    "deficit": p.min_stock_level - p.stock_quantity,
                    "category": p.category.name if p.category else "N/A",
                }
                for p in products
            ]
        finally:
            session.close()

    def get_stock_history(self, product_id: int = None, limit: int = 50) -> list:
        session = get_session()
        try:
            query = session.query(InventoryLog)
            if product_id:
                query = query.filter(InventoryLog.product_id == product_id)
            logs = query.order_by(InventoryLog.created_at.desc()).limit(limit).all()
            return [
                {
                    "id": log.id,
                    "product_id": log.product_id,
                    "product": log.product.name if log.product else "Unknown",
                    "type": log.change_type,
                    "change": log.quantity_change,
                    "before": log.quantity_before,
                    "after": log.quantity_after,
                    "reference": log.reference,
                    "notes": log.notes,
                    "date": log.created_at.strftime("%Y-%m-%d %H:%M"),
                }
                for log in logs
            ]
        finally:
            session.close()

    def get_inventory_summary(self) -> dict:
        session = get_session()
        try:
            products = session.query(Product).filter(Product.is_active == True).all()
            total_items = sum(p.stock_quantity for p in products)
            total_value = sum(p.stock_quantity * p.cost for p in products)
            total_retail = sum(p.stock_quantity * p.price for p in products)
            low_stock = sum(1 for p in products if p.stock_quantity <= p.min_stock_level)
            out_of_stock = sum(1 for p in products if p.stock_quantity == 0)

            return {
                "total_products": len(products),
                "total_items": total_items,
                "total_cost_value": round(total_value, 2),
                "total_retail_value": round(total_retail, 2),
                "potential_profit": round(total_retail - total_value, 2),
                "low_stock_count": low_stock,
                "out_of_stock_count": out_of_stock,
            }
        finally:
            session.close()

    def bulk_restock(self, items: list) -> list:
        results = []
        for item in items:
            result = self.restock(item["product_id"], item["quantity"], item.get("reference", ""))
            results.append(result)
        return results
