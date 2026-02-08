"""
ElectroPOS - Customer Manager
Customer profiles, loyalty points, and purchase history.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from models import Customer, Sale
from database import get_session


class CustomerManager:
    """Manages customer profiles and loyalty program."""

    def __init__(self, settings=None):
        self.settings = settings or {}
        loyalty = self.settings.get("loyalty", {})
        self.points_per_dollar = loyalty.get("points_per_dollar", 10)
        self.redemption_rate = loyalty.get("points_redemption_rate", 0.01)
        self.loyalty_enabled = loyalty.get("enabled", True)

    def list_customers(self, search: str = None, active_only: bool = True) -> list:
        session = get_session()
        try:
            query = session.query(Customer)
            if active_only:
                query = query.filter(Customer.is_active == True)
            if search:
                term = f"%{search}%"
                query = query.filter(
                    (Customer.first_name.ilike(term)) |
                    (Customer.last_name.ilike(term)) |
                    (Customer.email.ilike(term)) |
                    (Customer.phone.ilike(term)) |
                    (Customer.code.ilike(term))
                )
            customers = query.order_by(Customer.last_name).all()
            return [
                {
                    "id": c.id,
                    "code": c.code,
                    "name": c.full_name,
                    "email": c.email or "",
                    "phone": c.phone or "",
                    "points": c.loyalty_points,
                    "total_spent": round(c.total_spent, 2),
                    "visits": c.visit_count,
                }
                for c in customers
            ]
        finally:
            session.close()

    def get_customer(self, customer_id: int = None, code: str = None,
                     email: str = None) -> dict:
        session = get_session()
        try:
            query = session.query(Customer)
            if customer_id:
                customer = query.get(customer_id)
            elif code:
                customer = query.filter(Customer.code == code).first()
            elif email:
                customer = query.filter(Customer.email == email).first()
            else:
                return None

            if not customer:
                return None

            return {
                "id": customer.id,
                "code": customer.code,
                "name": customer.full_name,
                "first_name": customer.first_name,
                "last_name": customer.last_name,
                "email": customer.email or "",
                "phone": customer.phone or "",
                "address": customer.address or "",
                "points": customer.loyalty_points,
                "total_spent": round(customer.total_spent, 2),
                "visits": customer.visit_count,
                "points_value": round(customer.loyalty_points * self.redemption_rate, 2),
            }
        finally:
            session.close()

    def create_customer(self, first_name: str, last_name: str,
                        email: str = None, phone: str = None,
                        address: str = "") -> dict:
        session = get_session()
        try:
            if email:
                existing = session.query(Customer).filter(Customer.email == email).first()
                if existing:
                    return {"success": False, "error": f"Email '{email}' already registered."}

            customer = Customer(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                address=address,
            )
            session.add(customer)
            session.commit()
            return {
                "success": True,
                "id": customer.id,
                "code": customer.code,
                "message": f"Customer '{customer.full_name}' created (Code: {customer.code})."
            }
        except Exception as e:
            session.rollback()
            return {"success": False, "error": str(e)}
        finally:
            session.close()

    def update_customer(self, customer_id: int, **kwargs) -> dict:
        session = get_session()
        try:
            customer = session.query(Customer).get(customer_id)
            if not customer:
                return {"success": False, "error": "Customer not found."}

            allowed = {"first_name", "last_name", "email", "phone", "address", "is_active"}
            for key, value in kwargs.items():
                if key in allowed:
                    setattr(customer, key, value)

            session.commit()
            return {"success": True, "message": f"Customer '{customer.full_name}' updated."}
        except Exception as e:
            session.rollback()
            return {"success": False, "error": str(e)}
        finally:
            session.close()

    def add_loyalty_points(self, customer_id: int, amount_spent: float) -> dict:
        if not self.loyalty_enabled:
            return {"success": True, "points_earned": 0}

        session = get_session()
        try:
            customer = session.query(Customer).get(customer_id)
            if not customer:
                return {"success": False, "error": "Customer not found."}

            points = int(amount_spent * self.points_per_dollar)
            customer.loyalty_points += points
            customer.total_spent += amount_spent
            customer.visit_count += 1
            session.commit()

            return {
                "success": True,
                "points_earned": points,
                "total_points": customer.loyalty_points,
                "total_spent": round(customer.total_spent, 2),
            }
        except Exception as e:
            session.rollback()
            return {"success": False, "error": str(e)}
        finally:
            session.close()

    def redeem_points(self, customer_id: int, points: int) -> dict:
        if not self.loyalty_enabled:
            return {"success": False, "error": "Loyalty program is disabled."}

        session = get_session()
        try:
            customer = session.query(Customer).get(customer_id)
            if not customer:
                return {"success": False, "error": "Customer not found."}
            if customer.loyalty_points < points:
                return {
                    "success": False,
                    "error": f"Insufficient points. Available: {customer.loyalty_points}"
                }

            discount = round(points * self.redemption_rate, 2)
            customer.loyalty_points -= points
            session.commit()

            return {
                "success": True,
                "points_redeemed": points,
                "discount_amount": discount,
                "remaining_points": customer.loyalty_points,
            }
        except Exception as e:
            session.rollback()
            return {"success": False, "error": str(e)}
        finally:
            session.close()

    def get_purchase_history(self, customer_id: int, limit: int = 20) -> list:
        session = get_session()
        try:
            sales = (
                session.query(Sale)
                .filter(Sale.customer_id == customer_id)
                .order_by(Sale.created_at.desc())
                .limit(limit)
                .all()
            )
            return [
                {
                    "transaction_id": s.transaction_id,
                    "date": s.created_at.strftime("%Y-%m-%d %H:%M"),
                    "items": s.item_count,
                    "total": round(s.total, 2),
                    "payment": s.payment_method.value,
                    "status": s.status.value,
                    "points_earned": s.loyalty_points_earned,
                }
                for s in sales
            ]
        finally:
            session.close()

    def get_top_customers(self, limit: int = 10) -> list:
        session = get_session()
        try:
            customers = (
                session.query(Customer)
                .filter(Customer.is_active == True)
                .order_by(Customer.total_spent.desc())
                .limit(limit)
                .all()
            )
            return [
                {
                    "id": c.id,
                    "code": c.code,
                    "name": c.full_name,
                    "total_spent": round(c.total_spent, 2),
                    "points": c.loyalty_points,
                    "visits": c.visit_count,
                }
                for c in customers
            ]
        finally:
            session.close()
