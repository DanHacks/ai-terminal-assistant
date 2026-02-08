"""
ElectroPOS - Sales Manager
Handles complete sale transactions, returns, and sale history.
"""

import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))

from models import (
    Sale, SaleItem, Payment, Return, Product,
    PaymentMethod, TransactionStatus, ReturnStatus
)
from database import get_session
from cart import Cart
from inventory_manager import InventoryManager
from customer_manager import CustomerManager
from payment_processor import PaymentProcessor, PaymentResult
from receipt_generator import ReceiptGenerator


class SalesManager:
    """Orchestrates the complete sale lifecycle."""

    def __init__(self, settings=None):
        self.settings = settings or {}
        self.inventory = InventoryManager(settings)
        self.customers = CustomerManager(settings)
        self.payments = PaymentProcessor(settings)
        self.receipts = ReceiptGenerator(settings)

    def complete_sale(self, cart: Cart, employee_id: int,
                      payment_method: str, cash_tendered: float = 0.0,
                      card_last_four: str = "****",
                      cash_amount: float = 0.0, card_amount: float = 0.0) -> dict:
        """Process a complete sale from cart to receipt."""

        if cart.is_empty:
            return {"success": False, "error": "Cart is empty."}

        total = cart.total

        # ── Process Payment ──
        if payment_method == "cash":
            pay_result = self.payments.process_cash(total, cash_tendered)
            if not pay_result.success:
                return {"success": False, "error": pay_result.error}
        elif payment_method == "card":
            pay_result = self.payments.process_card(total, card_last_four)
        elif payment_method == "split":
            split_result = self.payments.process_split(total, cash_amount, card_amount, card_last_four)
            if not split_result["success"]:
                return {"success": False, "error": split_result["error"]}
            pay_result = None
        else:
            return {"success": False, "error": f"Unknown payment method: {payment_method}"}

        # ── Create Sale Record ──
        session = get_session()
        try:
            sale = Sale(
                employee_id=employee_id,
                customer_id=cart.customer_id,
                subtotal=cart.subtotal,
                tax_amount=cart.tax_amount,
                discount_amount=cart.cart_discount + cart.loyalty_discount,
                discount_percent=cart.cart_discount_percent,
                total=total,
                payment_method=PaymentMethod(payment_method),
                status=TransactionStatus.COMPLETED,
            )

            if payment_method == "cash":
                sale.cash_tendered = cash_tendered
                sale.change_due = pay_result.change
            elif payment_method == "card":
                sale.card_last_four = card_last_four
            elif payment_method == "split":
                sale.cash_tendered = cash_amount
                sale.change_due = split_result.get("change", 0)
                sale.card_last_four = card_last_four

            session.add(sale)
            session.flush()

            # ── Create Sale Items & Deduct Stock ──
            for cart_item in cart.items:
                sale_item = SaleItem(
                    sale_id=sale.id,
                    product_id=cart_item.product_id,
                    product_name=cart_item.name,
                    quantity=cart_item.quantity,
                    unit_price=cart_item.price,
                    discount_amount=cart_item.discount_total,
                    tax_amount=round(cart_item.taxable_amount * cart.tax_rate, 2) if cart_item.taxable else 0,
                    line_total=cart_item.line_total,
                )
                session.add(sale_item)

                # Deduct stock
                product = session.query(Product).get(cart_item.product_id)
                if product:
                    product.stock_quantity = max(0, product.stock_quantity - cart_item.quantity)

            # ── Create Payment Records ──
            if payment_method == "split":
                session.add(Payment(
                    sale_id=sale.id,
                    method=PaymentMethod.CASH,
                    amount=cash_amount,
                ))
                session.add(Payment(
                    sale_id=sale.id,
                    method=PaymentMethod.CARD,
                    amount=card_amount,
                    reference=f"CARD-{card_last_four}",
                ))
            else:
                pm = PaymentMethod(payment_method)
                session.add(Payment(
                    sale_id=sale.id,
                    method=pm,
                    amount=total,
                    reference=pay_result.reference if pay_result else "",
                ))

            # ── Loyalty Points ──
            loyalty_earned = 0
            loyalty_balance = None
            if cart.customer_id:
                loyalty_result = self.customers.add_loyalty_points(cart.customer_id, total)
                if loyalty_result.get("success"):
                    loyalty_earned = loyalty_result.get("points_earned", 0)
                    loyalty_balance = loyalty_result.get("total_points", 0)
                    sale.loyalty_points_earned = loyalty_earned

            session.commit()

            # ── Generate Receipt ──
            receipt_data = {
                "sale_id": sale.id,
                "transaction_id": sale.transaction_id,
                "date": sale.created_at.strftime("%Y-%m-%d %H:%M"),
                "employee_name": f"Employee #{employee_id}",
                "customer_name": cart.customer_name,
                "items": [
                    {
                        "name": ci.name,
                        "quantity": ci.quantity,
                        "unit_price": ci.price,
                        "line_total": ci.line_total,
                        "discount_amount": ci.discount_total,
                    }
                    for ci in cart.items
                ],
                "subtotal": cart.subtotal,
                "discount_amount": cart.cart_discount,
                "loyalty_discount": cart.loyalty_discount,
                "tax_amount": cart.tax_amount,
                "tax_rate": cart.tax_rate,
                "total": total,
                "payment_method": payment_method,
                "cash_tendered": cash_tendered,
                "change_due": pay_result.change if pay_result and payment_method == "cash" else 0,
                "card_last_four": card_last_four if payment_method in ("card", "split") else None,
                "loyalty_points_earned": loyalty_earned,
                "loyalty_points_balance": loyalty_balance,
            }

            if payment_method == "split":
                receipt_data["payments"] = [
                    {"method": "cash", "amount": cash_amount},
                    {"method": "card", "amount": card_amount},
                ]
                receipt_data["change_due"] = split_result.get("change", 0)

            receipt_text = self.receipts.generate(receipt_data)

            # Save receipt
            receipts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "receipts")
            os.makedirs(receipts_dir, exist_ok=True)
            receipt_path = os.path.join(receipts_dir, f"receipt_{sale.transaction_id}.txt")
            with open(receipt_path, "w") as f:
                f.write(receipt_text)

            return {
                "success": True,
                "sale_id": sale.id,
                "transaction_id": sale.transaction_id,
                "total": total,
                "payment_method": payment_method,
                "change": pay_result.change if pay_result and payment_method == "cash" else 0,
                "receipt": receipt_text,
                "receipt_path": receipt_path,
                "loyalty_earned": loyalty_earned,
            }

        except Exception as e:
            session.rollback()
            return {"success": False, "error": str(e)}
        finally:
            session.close()

    def process_return(self, transaction_id: str, product_id: int,
                       quantity: int, reason: str, employee_id: int,
                       restock: bool = True) -> dict:
        """Process a return/refund for a sale item."""

        session = get_session()
        try:
            sale = session.query(Sale).filter(Sale.transaction_id == transaction_id).first()
            if not sale:
                return {"success": False, "error": f"Transaction '{transaction_id}' not found."}

            sale_item = None
            for item in sale.items:
                if item.product_id == product_id:
                    sale_item = item
                    break

            if not sale_item:
                return {"success": False, "error": "Product not found in this transaction."}

            if quantity > sale_item.quantity:
                return {"success": False, "error": f"Cannot return more than purchased ({sale_item.quantity})."}

            refund_amount = round((sale_item.line_total / sale_item.quantity) * quantity, 2)

            ret = Return(
                sale_id=sale.id,
                employee_id=employee_id,
                product_id=product_id,
                quantity=quantity,
                refund_amount=refund_amount,
                reason=reason,
                status=ReturnStatus.APPROVED,
                restock=restock,
            )
            session.add(ret)

            if restock:
                product = session.query(Product).get(product_id)
                if product:
                    product.stock_quantity += quantity

            if refund_amount >= sale.total:
                sale.status = TransactionStatus.REFUNDED
            else:
                sale.status = TransactionStatus.PARTIALLY_REFUNDED

            session.commit()

            return_data = {
                "return_id": ret.return_id,
                "original_transaction_id": transaction_id,
                "product_name": sale_item.product_name,
                "quantity": quantity,
                "refund_amount": refund_amount,
                "reason": reason,
                "employee_name": f"Employee #{employee_id}",
                "date": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
            }

            receipt_text = self.receipts.generate_return_receipt(return_data)

            return {
                "success": True,
                "return_id": ret.return_id,
                "refund_amount": refund_amount,
                "receipt": receipt_text,
            }

        except Exception as e:
            session.rollback()
            return {"success": False, "error": str(e)}
        finally:
            session.close()

    def void_sale(self, transaction_id: str, employee_id: int) -> dict:
        session = get_session()
        try:
            sale = session.query(Sale).filter(Sale.transaction_id == transaction_id).first()
            if not sale:
                return {"success": False, "error": "Transaction not found."}
            if sale.status != TransactionStatus.COMPLETED:
                return {"success": False, "error": f"Cannot void. Status: {sale.status.value}"}

            for item in sale.items:
                product = session.query(Product).get(item.product_id)
                if product:
                    product.stock_quantity += item.quantity

            sale.status = TransactionStatus.VOIDED
            session.commit()

            return {
                "success": True,
                "message": f"Sale {transaction_id} voided. Stock restored.",
                "refund_amount": sale.total,
            }
        except Exception as e:
            session.rollback()
            return {"success": False, "error": str(e)}
        finally:
            session.close()

    def get_sale(self, transaction_id: str) -> dict:
        session = get_session()
        try:
            sale = session.query(Sale).filter(Sale.transaction_id == transaction_id).first()
            if not sale:
                return None

            return {
                "id": sale.id,
                "transaction_id": sale.transaction_id,
                "date": sale.created_at.strftime("%Y-%m-%d %H:%M"),
                "employee_id": sale.employee_id,
                "customer_id": sale.customer_id,
                "subtotal": sale.subtotal,
                "tax": sale.tax_amount,
                "discount": sale.discount_amount,
                "total": sale.total,
                "payment_method": sale.payment_method.value,
                "status": sale.status.value,
                "items": [
                    {
                        "product": item.product_name,
                        "quantity": item.quantity,
                        "price": item.unit_price,
                        "total": item.line_total,
                    }
                    for item in sale.items
                ],
            }
        finally:
            session.close()

    def get_recent_sales(self, limit: int = 20) -> list:
        session = get_session()
        try:
            sales = (
                session.query(Sale)
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
                }
                for s in sales
            ]
        finally:
            session.close()
