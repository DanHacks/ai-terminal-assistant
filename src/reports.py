"""
ElectroPOS - Reports & Analytics
Sales reports, revenue analytics, and CSV export.
"""

import os
import sys
import csv
from datetime import datetime, timezone, timedelta
from collections import defaultdict

sys.path.insert(0, os.path.dirname(__file__))

from models import Sale, SaleItem, Product, Category, Customer, TransactionStatus
from database import get_session


class ReportManager:
    """Generates sales reports and analytics."""

    def __init__(self, settings=None):
        self.settings = settings or {}
        currency = self.settings.get("currency", {})
        self.symbol = currency.get("symbol", "$")

    def _get_date_range(self, period: str):
        now = datetime.now(timezone.utc)
        if period == "today":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "yesterday":
            start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            now = start + timedelta(days=1)
        elif period == "week":
            start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "month":
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif period == "year":
            start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        elif period == "last7":
            start = (now - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "last30":
            start = (now - timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            start = (now - timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0)
        return start, now

    def sales_summary(self, period: str = "today") -> dict:
        start, end = self._get_date_range(period)
        session = get_session()
        try:
            sales = (
                session.query(Sale)
                .filter(
                    Sale.created_at >= start,
                    Sale.created_at <= end,
                    Sale.status == TransactionStatus.COMPLETED
                )
                .all()
            )

            if not sales:
                return {
                    "period": period,
                    "start": start.strftime("%Y-%m-%d"),
                    "end": end.strftime("%Y-%m-%d"),
                    "total_sales": 0,
                    "total_revenue": 0,
                    "total_tax": 0,
                    "total_discounts": 0,
                    "average_sale": 0,
                    "total_items": 0,
                    "cash_sales": 0,
                    "card_sales": 0,
                }

            total_revenue = sum(s.total for s in sales)
            total_tax = sum(s.tax_amount for s in sales)
            total_discounts = sum(s.discount_amount for s in sales)
            total_items = sum(s.item_count for s in sales)
            cash_sales = sum(1 for s in sales if s.payment_method.value == "cash")
            card_sales = sum(1 for s in sales if s.payment_method.value == "card")

            return {
                "period": period,
                "start": start.strftime("%Y-%m-%d"),
                "end": end.strftime("%Y-%m-%d"),
                "total_sales": len(sales),
                "total_revenue": round(total_revenue, 2),
                "total_tax": round(total_tax, 2),
                "total_discounts": round(total_discounts, 2),
                "average_sale": round(total_revenue / len(sales), 2),
                "total_items": total_items,
                "cash_sales": cash_sales,
                "card_sales": card_sales,
            }
        finally:
            session.close()

    def top_products(self, period: str = "last30", limit: int = 10) -> list:
        start, end = self._get_date_range(period)
        session = get_session()
        try:
            sales = (
                session.query(Sale)
                .filter(
                    Sale.created_at >= start,
                    Sale.created_at <= end,
                    Sale.status == TransactionStatus.COMPLETED
                )
                .all()
            )

            product_stats = defaultdict(lambda: {"name": "", "quantity": 0, "revenue": 0.0})
            for sale in sales:
                for item in sale.items:
                    stats = product_stats[item.product_id]
                    stats["name"] = item.product_name
                    stats["quantity"] += item.quantity
                    stats["revenue"] += item.line_total

            sorted_products = sorted(
                product_stats.items(),
                key=lambda x: x[1]["revenue"],
                reverse=True
            )[:limit]

            return [
                {
                    "rank": i + 1,
                    "product_id": pid,
                    "name": stats["name"],
                    "quantity_sold": stats["quantity"],
                    "revenue": round(stats["revenue"], 2),
                }
                for i, (pid, stats) in enumerate(sorted_products)
            ]
        finally:
            session.close()

    def revenue_by_category(self, period: str = "last30") -> list:
        start, end = self._get_date_range(period)
        session = get_session()
        try:
            sales = (
                session.query(Sale)
                .filter(
                    Sale.created_at >= start,
                    Sale.created_at <= end,
                    Sale.status == TransactionStatus.COMPLETED
                )
                .all()
            )

            cat_revenue = defaultdict(lambda: {"revenue": 0.0, "items": 0})
            for sale in sales:
                for item in sale.items:
                    product = session.query(Product).get(item.product_id)
                    cat_name = product.category.name if product and product.category else "Uncategorized"
                    cat_revenue[cat_name]["revenue"] += item.line_total
                    cat_revenue[cat_name]["items"] += item.quantity

            total_rev = sum(v["revenue"] for v in cat_revenue.values())
            result = []
            for cat, data in sorted(cat_revenue.items(), key=lambda x: x[1]["revenue"], reverse=True):
                pct = (data["revenue"] / total_rev * 100) if total_rev > 0 else 0
                result.append({
                    "category": cat,
                    "revenue": round(data["revenue"], 2),
                    "items_sold": data["items"],
                    "percentage": round(pct, 1),
                })
            return result
        finally:
            session.close()

    def daily_revenue(self, days: int = 14) -> list:
        session = get_session()
        try:
            now = datetime.now(timezone.utc)
            start = (now - timedelta(days=days)).replace(hour=0, minute=0, second=0, microsecond=0)

            sales = (
                session.query(Sale)
                .filter(
                    Sale.created_at >= start,
                    Sale.status == TransactionStatus.COMPLETED
                )
                .all()
            )

            daily = defaultdict(lambda: {"revenue": 0.0, "count": 0, "items": 0})
            for sale in sales:
                day_key = sale.created_at.strftime("%Y-%m-%d")
                daily[day_key]["revenue"] += sale.total
                daily[day_key]["count"] += 1
                daily[day_key]["items"] += sale.item_count

            result = []
            for i in range(days):
                day = (now - timedelta(days=days - 1 - i)).strftime("%Y-%m-%d")
                data = daily.get(day, {"revenue": 0.0, "count": 0, "items": 0})
                result.append({
                    "date": day,
                    "revenue": round(data["revenue"], 2),
                    "transactions": data["count"],
                    "items_sold": data["items"],
                })
            return result
        finally:
            session.close()

    def hourly_sales(self, date_str: str = None) -> list:
        session = get_session()
        try:
            if date_str:
                target = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            else:
                target = datetime.now(timezone.utc)

            start = target.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)

            sales = (
                session.query(Sale)
                .filter(
                    Sale.created_at >= start,
                    Sale.created_at < end,
                    Sale.status == TransactionStatus.COMPLETED
                )
                .all()
            )

            hourly = defaultdict(lambda: {"revenue": 0.0, "count": 0})
            for sale in sales:
                hour = sale.created_at.hour
                hourly[hour]["revenue"] += sale.total
                hourly[hour]["count"] += 1

            return [
                {
                    "hour": f"{h:02d}:00",
                    "revenue": round(hourly[h]["revenue"], 2),
                    "transactions": hourly[h]["count"],
                }
                for h in range(24)
            ]
        finally:
            session.close()

    def payment_method_breakdown(self, period: str = "last30") -> list:
        start, end = self._get_date_range(period)
        session = get_session()
        try:
            sales = (
                session.query(Sale)
                .filter(
                    Sale.created_at >= start,
                    Sale.created_at <= end,
                    Sale.status == TransactionStatus.COMPLETED
                )
                .all()
            )

            methods = defaultdict(lambda: {"count": 0, "total": 0.0})
            for sale in sales:
                m = sale.payment_method.value
                methods[m]["count"] += 1
                methods[m]["total"] += sale.total

            grand_total = sum(v["total"] for v in methods.values())
            return [
                {
                    "method": method.upper(),
                    "transactions": data["count"],
                    "total": round(data["total"], 2),
                    "percentage": round((data["total"] / grand_total * 100) if grand_total > 0 else 0, 1),
                }
                for method, data in sorted(methods.items(), key=lambda x: x[1]["total"], reverse=True)
            ]
        finally:
            session.close()

    def profit_report(self, period: str = "last30") -> dict:
        start, end = self._get_date_range(period)
        session = get_session()
        try:
            sales = (
                session.query(Sale)
                .filter(
                    Sale.created_at >= start,
                    Sale.created_at <= end,
                    Sale.status == TransactionStatus.COMPLETED
                )
                .all()
            )

            total_revenue = 0.0
            total_cost = 0.0
            for sale in sales:
                total_revenue += sale.total
                for item in sale.items:
                    product = session.query(Product).get(item.product_id)
                    if product:
                        total_cost += product.cost * item.quantity

            gross_profit = total_revenue - total_cost
            margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0

            return {
                "period": period,
                "total_revenue": round(total_revenue, 2),
                "total_cost": round(total_cost, 2),
                "gross_profit": round(gross_profit, 2),
                "profit_margin": round(margin, 1),
                "total_transactions": len(sales),
            }
        finally:
            session.close()

    def export_sales_csv(self, period: str = "last30", filepath: str = None) -> str:
        start, end = self._get_date_range(period)
        session = get_session()
        try:
            sales = (
                session.query(Sale)
                .filter(Sale.created_at >= start, Sale.created_at <= end)
                .order_by(Sale.created_at.desc())
                .all()
            )

            if not filepath:
                export_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "exports")
                os.makedirs(export_dir, exist_ok=True)
                filepath = os.path.join(
                    export_dir,
                    f"sales_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                )

            with open(filepath, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Transaction ID", "Date", "Employee ID", "Customer ID",
                    "Subtotal", "Tax", "Discount", "Total",
                    "Payment Method", "Status", "Items Count"
                ])
                for sale in sales:
                    writer.writerow([
                        sale.transaction_id,
                        sale.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                        sale.employee_id,
                        sale.customer_id or "",
                        round(sale.subtotal, 2),
                        round(sale.tax_amount, 2),
                        round(sale.discount_amount, 2),
                        round(sale.total, 2),
                        sale.payment_method.value,
                        sale.status.value,
                        sale.item_count,
                    ])

            return filepath
        finally:
            session.close()

    def export_inventory_csv(self, filepath: str = None) -> str:
        session = get_session()
        try:
            products = session.query(Product).filter(Product.is_active == True).order_by(Product.name).all()

            if not filepath:
                export_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "exports")
                os.makedirs(export_dir, exist_ok=True)
                filepath = os.path.join(
                    export_dir,
                    f"inventory_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                )

            with open(filepath, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "SKU", "Barcode", "Name", "Category", "Price", "Cost",
                    "Stock", "Min Stock", "Margin %", "Active", "Taxable"
                ])
                for p in products:
                    writer.writerow([
                        p.sku, p.barcode or "", p.name,
                        p.category.name if p.category else "N/A",
                        p.price, p.cost, p.stock_quantity, p.min_stock_level,
                        round(p.profit_margin, 1), p.is_active, p.is_taxable,
                    ])

            return filepath
        finally:
            session.close()
