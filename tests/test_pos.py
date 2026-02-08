"""
ElectroPOS - Comprehensive Test Suite
Tests for models, database, cart, payments, inventory, sales, reports, and more.
"""

import os
import sys
import pytest
import tempfile

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from models import (
    Base, Product, Category, Customer, Employee, Sale, SaleItem,
    Payment, Return, InventoryLog, EmployeeRole, PaymentMethod,
    TransactionStatus, ReturnStatus
)
from database import init_db, get_session, seed_database, hash_pin, verify_pin
from product_manager import ProductManager
from inventory_manager import InventoryManager
from customer_manager import CustomerManager
from cart import Cart, CartItem
from payment_processor import PaymentProcessor, PaymentResult
from receipt_generator import ReceiptGenerator
from sales_manager import SalesManager
from reports import ReportManager
from auth import AuthManager
from validator import (
    validate_email, validate_phone, validate_pin, validate_price,
    validate_quantity, validate_sku, validate_barcode,
    validate_discount_percent, validate_name
)
from command_parser import parse_pos_command, get_help_text
from command_executor import CommandExecutor


# ═══════════════════════════════════════════════════════════════════════════
#  FIXTURES
# ═══════════════════════════════════════════════════════════════════════════

@pytest.fixture(autouse=True)
def setup_test_db(tmp_path):
    """Create a fresh test database for each test."""
    db_path = str(tmp_path / "test_pos.db")
    settings = {
        "database": {"path": db_path, "echo": False},
        "tax": {"rate": 0.08, "enabled": True, "name": "Sales Tax"},
        "currency": {"symbol": "$", "code": "USD", "decimal_places": 2},
        "loyalty": {"enabled": True, "points_per_dollar": 10, "points_redemption_rate": 0.01},
        "inventory": {"low_stock_threshold": 10, "track_history": True},
        "security": {"max_login_attempts": 3},
        "store": {"name": "Test Store", "address": "123 Test St", "phone": "555-0000"},
        "receipt": {"width": 48, "footer_message": "Thanks!", "show_tax_breakdown": True, "show_savings": True},
    }
    init_db(settings, db_path)
    return settings


@pytest.fixture
def seeded_db(setup_test_db):
    """Database with seed data."""
    session = get_session()
    seed_database(session)
    session.close()
    return setup_test_db


@pytest.fixture
def settings(setup_test_db):
    return setup_test_db


# ═══════════════════════════════════════════════════════════════════════════
#  DATABASE & MODELS
# ═══════════════════════════════════════════════════════════════════════════

class TestDatabase:
    def test_init_creates_tables(self, settings):
        session = get_session()
        # Should not raise
        session.query(Product).all()
        session.query(Category).all()
        session.query(Customer).all()
        session.query(Employee).all()
        session.query(Sale).all()
        session.close()

    def test_seed_database(self, settings):
        session = get_session()
        result = seed_database(session)
        assert result is True

        categories = session.query(Category).all()
        assert len(categories) == 8

        products = session.query(Product).all()
        assert len(products) == 39

        customers = session.query(Customer).all()
        assert len(customers) == 8

        employees = session.query(Employee).all()
        assert len(employees) == 4

        sales = session.query(Sale).all()
        assert len(sales) > 0

        session.close()

    def test_seed_idempotent(self, seeded_db):
        session = get_session()
        result = seed_database(session)
        assert result is False  # Already seeded
        session.close()

    def test_hash_pin(self):
        pin = "1234"
        hashed = hash_pin(pin)
        assert hashed != pin
        assert verify_pin(pin, hashed)
        assert not verify_pin("wrong", hashed)


class TestModels:
    def test_product_profit_margin(self, settings):
        session = get_session()
        p = Product(name="Test", price=100.0, cost=60.0, sku="TEST01")
        session.add(p)
        session.commit()
        assert p.profit_margin == 40.0
        session.close()

    def test_product_zero_cost_margin(self, settings):
        p = Product(name="Test", price=50.0, cost=0.0, sku="TEST02")
        assert p.profit_margin == 0.0

    def test_customer_full_name(self, settings):
        c = Customer(first_name="John", last_name="Doe")
        assert c.full_name == "John Doe"

    def test_employee_full_name(self, settings):
        e = Employee(first_name="Jane", last_name="Smith", pin_hash="x")
        assert e.full_name == "Jane Smith"

    def test_employee_roles(self):
        assert EmployeeRole.ADMIN.value == "admin"
        assert EmployeeRole.MANAGER.value == "manager"
        assert EmployeeRole.CASHIER.value == "cashier"

    def test_payment_methods(self):
        assert PaymentMethod.CASH.value == "cash"
        assert PaymentMethod.CARD.value == "card"
        assert PaymentMethod.SPLIT.value == "split"


# ═══════════════════════════════════════════════════════════════════════════
#  PRODUCT MANAGER
# ═══════════════════════════════════════════════════════════════════════════

class TestProductManager:
    def test_create_category(self, settings):
        pm = ProductManager()
        result = pm.create_category("Test Category", "A test")
        assert result["success"]
        assert result["id"] > 0

    def test_duplicate_category(self, settings):
        pm = ProductManager()
        pm.create_category("Unique")
        result = pm.create_category("Unique")
        assert not result["success"]

    def test_list_categories(self, seeded_db):
        pm = ProductManager()
        cats = pm.list_categories()
        assert len(cats) == 8

    def test_create_product(self, settings):
        pm = ProductManager()
        result = pm.create_product("Widget", 9.99, cost=4.00, stock=50)
        assert result["success"]
        assert result["sku"]

    def test_create_product_negative_price(self, settings):
        pm = ProductManager()
        result = pm.create_product("Bad", -5.00)
        assert not result["success"]

    def test_get_product_by_sku(self, seeded_db):
        pm = ProductManager()
        product = pm.get_product(sku="USB6FT01")
        assert product is not None
        assert product["name"] == "USB-C Cable 6ft"

    def test_get_product_by_barcode(self, seeded_db):
        pm = ProductManager()
        product = pm.get_product(barcode="4901234567890")
        assert product is not None

    def test_search_products(self, seeded_db):
        pm = ProductManager()
        results = pm.search_products("cable")
        assert len(results) >= 1

    def test_update_product(self, seeded_db):
        pm = ProductManager()
        product = pm.get_product(sku="USB6FT01")
        result = pm.update_product(product["id"], price=14.99)
        assert result["success"]
        updated = pm.get_product(product_id=product["id"])
        assert updated["price"] == 14.99

    def test_soft_delete_product(self, seeded_db):
        pm = ProductManager()
        product = pm.get_product(sku="USB6FT01")
        result = pm.delete_product(product["id"], soft=True)
        assert result["success"]

    def test_low_stock_products(self, seeded_db):
        pm = ProductManager()
        low = pm.get_low_stock_products(threshold=50)
        assert isinstance(low, list)

    def test_list_products_with_filter(self, seeded_db):
        pm = ProductManager()
        all_prods = pm.list_products()
        assert len(all_prods) == 39


# ═══════════════════════════════════════════════════════════════════════════
#  INVENTORY MANAGER
# ═══════════════════════════════════════════════════════════════════════════

class TestInventoryManager:
    def test_restock(self, seeded_db):
        inv = InventoryManager(seeded_db)
        pm = ProductManager()
        product = pm.get_product(sku="USB6FT01")
        original_stock = product["stock"]

        result = inv.restock(product["id"], 50, "PO-001")
        assert result["success"]
        assert result["after"] == original_stock + 50

    def test_restock_negative(self, seeded_db):
        inv = InventoryManager(seeded_db)
        result = inv.restock(1, -5)
        assert not result["success"]

    def test_deduct_stock(self, seeded_db):
        inv = InventoryManager(seeded_db)
        pm = ProductManager()
        product = pm.get_product(sku="USB6FT01")

        result = inv.deduct_stock(product["id"], 5, "SALE-001")
        assert result["success"]
        assert result["after"] == product["stock"] - 5

    def test_deduct_insufficient_stock(self, seeded_db):
        inv = InventoryManager(seeded_db)
        pm = ProductManager()
        product = pm.get_product(sku="USB6FT01")

        result = inv.deduct_stock(product["id"], 99999)
        assert not result["success"]

    def test_stock_history(self, seeded_db):
        inv = InventoryManager(seeded_db)
        pm = ProductManager()
        product = pm.get_product(sku="USB6FT01")

        inv.restock(product["id"], 10)
        history = inv.get_stock_history(product["id"])
        assert len(history) >= 1

    def test_inventory_summary(self, seeded_db):
        inv = InventoryManager(seeded_db)
        summary = inv.get_inventory_summary()
        assert summary["total_products"] == 39
        assert summary["total_items"] > 0
        assert summary["total_retail_value"] > 0

    def test_low_stock_alerts(self, seeded_db):
        inv = InventoryManager(seeded_db)
        alerts = inv.get_low_stock_alerts()
        assert isinstance(alerts, list)

    def test_get_stock_level(self, seeded_db):
        inv = InventoryManager(seeded_db)
        result = inv.get_stock_level(1)
        assert result["success"]
        assert "stock" in result

    def test_return_stock(self, seeded_db):
        inv = InventoryManager(seeded_db)
        pm = ProductManager()
        product = pm.get_product(sku="USB6FT01")
        before = product["stock"]

        result = inv.return_stock(product["id"], 3, "RET-001")
        assert result["success"]
        assert result["after"] == before + 3


# ═══════════════════════════════════════════════════════════════════════════
#  CUSTOMER MANAGER
# ═══════════════════════════════════════════════════════════════════════════

class TestCustomerManager:
    def test_create_customer(self, settings):
        cm = CustomerManager(settings)
        result = cm.create_customer("Test", "User", "test@test.com", "555-9999")
        assert result["success"]
        assert result["code"]

    def test_duplicate_email(self, seeded_db):
        cm = CustomerManager(seeded_db)
        result = cm.create_customer("Dup", "User", "alice@email.com")
        assert not result["success"]

    def test_list_customers(self, seeded_db):
        cm = CustomerManager(seeded_db)
        custs = cm.list_customers()
        assert len(custs) == 8

    def test_search_customers(self, seeded_db):
        cm = CustomerManager(seeded_db)
        results = cm.list_customers(search="Alice")
        assert len(results) >= 1

    def test_get_customer(self, seeded_db):
        cm = CustomerManager(seeded_db)
        custs = cm.list_customers()
        cust = cm.get_customer(customer_id=custs[0]["id"])
        assert cust is not None
        assert cust["name"]

    def test_add_loyalty_points(self, seeded_db):
        cm = CustomerManager(seeded_db)
        custs = cm.list_customers()
        cid = custs[0]["id"]
        before = cm.get_customer(customer_id=cid)["points"]

        result = cm.add_loyalty_points(cid, 100.0)
        assert result["success"]
        assert result["points_earned"] == 1000  # 100 * 10

        after = cm.get_customer(customer_id=cid)["points"]
        assert after == before + 1000

    def test_redeem_points(self, seeded_db):
        cm = CustomerManager(seeded_db)
        custs = cm.list_customers()
        cid = custs[0]["id"]
        cust = cm.get_customer(customer_id=cid)

        if cust["points"] > 0:
            result = cm.redeem_points(cid, 100)
            assert result["success"]
            assert result["discount_amount"] == 1.00  # 100 * 0.01

    def test_redeem_insufficient_points(self, seeded_db):
        cm = CustomerManager(seeded_db)
        custs = cm.list_customers()
        cid = custs[0]["id"]
        result = cm.redeem_points(cid, 999999)
        assert not result["success"]

    def test_top_customers(self, seeded_db):
        cm = CustomerManager(seeded_db)
        top = cm.get_top_customers()
        assert len(top) > 0
        # Should be sorted by total_spent descending
        for i in range(len(top) - 1):
            assert top[i]["total_spent"] >= top[i + 1]["total_spent"]

    def test_update_customer(self, seeded_db):
        cm = CustomerManager(seeded_db)
        custs = cm.list_customers()
        result = cm.update_customer(custs[0]["id"], phone="555-NEW")
        assert result["success"]


# ═══════════════════════════════════════════════════════════════════════════
#  CART
# ═══════════════════════════════════════════════════════════════════════════

class TestCart:
    def test_add_item(self, seeded_db):
        cart = Cart(seeded_db)
        result = cart.add_item(sku="USB6FT01")
        assert result["success"]
        assert cart.item_count == 1

    def test_add_item_by_barcode(self, seeded_db):
        cart = Cart(seeded_db)
        result = cart.add_item(barcode="4901234567890")
        assert result["success"]

    def test_add_item_by_id(self, seeded_db):
        cart = Cart(seeded_db)
        result = cart.add_item(product_id=1)
        assert result["success"]

    def test_add_duplicate_increases_qty(self, seeded_db):
        cart = Cart(seeded_db)
        cart.add_item(sku="USB6FT01")
        cart.add_item(sku="USB6FT01")
        assert cart.items[0].quantity == 2

    def test_add_multiple_items(self, seeded_db):
        cart = Cart(seeded_db)
        cart.add_item(sku="USB6FT01")
        cart.add_item(sku="WMOUSE01")
        assert len(cart.items) == 2

    def test_remove_item(self, seeded_db):
        cart = Cart(seeded_db)
        cart.add_item(product_id=1)
        result = cart.remove_item(1)
        assert result["success"]
        assert cart.is_empty

    def test_update_quantity(self, seeded_db):
        cart = Cart(seeded_db)
        cart.add_item(product_id=1)
        result = cart.update_quantity(1, 5)
        assert result["success"]
        assert cart.items[0].quantity == 5

    def test_update_quantity_zero_removes(self, seeded_db):
        cart = Cart(seeded_db)
        cart.add_item(product_id=1)
        cart.update_quantity(1, 0)
        assert cart.is_empty

    def test_item_discount_percent(self, seeded_db):
        cart = Cart(seeded_db)
        cart.add_item(product_id=1)
        result = cart.apply_item_discount(1, percent=10)
        assert result["success"]
        assert cart.items[0].discount_percent == 10

    def test_cart_discount(self, seeded_db):
        cart = Cart(seeded_db)
        cart.add_item(sku="USB6FT01")
        result = cart.apply_cart_discount(percent=5)
        assert result["success"]
        assert cart.cart_discount > 0

    def test_subtotal_calculation(self, seeded_db):
        cart = Cart(seeded_db)
        cart.add_item(sku="USB6FT01", quantity=2)  # 12.99 * 2
        assert cart.subtotal == 25.98

    def test_tax_calculation(self, seeded_db):
        cart = Cart(seeded_db)
        cart.add_item(sku="USB6FT01", quantity=1)  # 12.99
        assert cart.tax_amount == round(12.99 * 0.08, 2)

    def test_total_calculation(self, seeded_db):
        cart = Cart(seeded_db)
        cart.add_item(sku="USB6FT01", quantity=1)
        expected = round(12.99 + 12.99 * 0.08, 2)
        assert cart.total == expected

    def test_clear_cart(self, seeded_db):
        cart = Cart(seeded_db)
        cart.add_item(sku="USB6FT01")
        cart.add_item(sku="WMOUSE01")
        cart.set_customer(1, "Test")
        cart.clear()
        assert cart.is_empty
        assert cart.customer_id is None

    def test_set_customer(self, seeded_db):
        cart = Cart(seeded_db)
        cart.set_customer(1, "Alice Johnson")
        assert cart.customer_id == 1
        assert cart.customer_name == "Alice Johnson"

    def test_get_summary(self, seeded_db):
        cart = Cart(seeded_db)
        cart.add_item(sku="USB6FT01", quantity=2)
        summary = cart.get_summary()
        assert summary["item_count"] == 2
        assert summary["subtotal"] == 25.98
        assert summary["total"] > 0

    def test_loyalty_discount(self, seeded_db):
        cart = Cart(seeded_db)
        cart.add_item(sku="USB6FT01")
        cart.set_loyalty_discount(2.00)
        assert cart.loyalty_discount == 2.00
        assert cart.total_discounts >= 2.00

    def test_insufficient_stock(self, seeded_db):
        cart = Cart(seeded_db)
        result = cart.add_item(sku="USB6FT01", quantity=99999)
        assert not result["success"]


# ═══════════════════════════════════════════════════════════════════════════
#  PAYMENT PROCESSOR
# ═══════════════════════════════════════════════════════════════════════════

class TestPaymentProcessor:
    def test_cash_exact(self, settings):
        pp = PaymentProcessor(settings)
        result = pp.process_cash(25.00, 25.00)
        assert result.success
        assert result.change == 0.0

    def test_cash_with_change(self, settings):
        pp = PaymentProcessor(settings)
        result = pp.process_cash(17.50, 20.00)
        assert result.success
        assert result.change == 2.50

    def test_cash_insufficient(self, settings):
        pp = PaymentProcessor(settings)
        result = pp.process_cash(25.00, 10.00)
        assert not result.success

    def test_card_payment(self, settings):
        pp = PaymentProcessor(settings)
        result = pp.process_card(50.00, "1234")
        assert result.success
        assert result.card_last_four == "1234"

    def test_split_payment(self, settings):
        pp = PaymentProcessor(settings)
        result = pp.process_split(100.00, 60.00, 40.00, "5678")
        assert result["success"]
        assert result["cash"]["amount"] == 60.00
        assert result["card"]["amount"] == 40.00

    def test_split_insufficient(self, settings):
        pp = PaymentProcessor(settings)
        result = pp.process_split(100.00, 30.00, 30.00)
        assert not result["success"]

    def test_change_breakdown(self, settings):
        pp = PaymentProcessor(settings)
        breakdown = pp.calculate_change_breakdown(18.76)
        assert len(breakdown) > 0
        total = sum(
            float(d["denomination"].replace("$", "").replace("¢", "")) *
            (0.01 if "¢" in d["denomination"] else 1) * d["count"]
            for d in breakdown
        )
        assert abs(total - 18.76) < 0.02

    def test_format_amount(self, settings):
        pp = PaymentProcessor(settings)
        assert pp.format_amount(12.50) == "$12.50"


# ═══════════════════════════════════════════════════════════════════════════
#  RECEIPT GENERATOR
# ═══════════════════════════════════════════════════════════════════════════

class TestReceiptGenerator:
    def test_generate_receipt(self, settings):
        rg = ReceiptGenerator(settings)
        receipt = rg.generate({
            "transaction_id": "TEST001",
            "employee_name": "John",
            "items": [
                {"name": "Widget", "quantity": 2, "unit_price": 10.00, "line_total": 20.00},
            ],
            "subtotal": 20.00,
            "tax_amount": 1.60,
            "tax_rate": 0.08,
            "total": 21.60,
            "payment_method": "cash",
            "cash_tendered": 25.00,
            "change_due": 3.40,
        })
        assert "TEST001" in receipt
        assert "Widget" in receipt
        assert "21.60" in receipt
        assert "Test Store" in receipt

    def test_generate_return_receipt(self, settings):
        rg = ReceiptGenerator(settings)
        receipt = rg.generate_return_receipt({
            "return_id": "RET001",
            "original_transaction_id": "TXN001",
            "product_name": "Widget",
            "quantity": 1,
            "refund_amount": 10.00,
            "reason": "Defective",
            "employee_name": "Jane",
        })
        assert "RETURN" in receipt
        assert "RET001" in receipt
        assert "Widget" in receipt


# ═══════════════════════════════════════════════════════════════════════════
#  SALES MANAGER
# ═══════════════════════════════════════════════════════════════════════════

class TestSalesManager:
    def test_complete_cash_sale(self, seeded_db):
        sm = SalesManager(seeded_db)
        cart = Cart(seeded_db)
        cart.add_item(sku="USB6FT01", quantity=2)

        result = sm.complete_sale(cart, employee_id=1, payment_method="cash", cash_tendered=50.00)
        assert result["success"]
        assert result["transaction_id"]
        assert result["receipt"]

    def test_complete_card_sale(self, seeded_db):
        sm = SalesManager(seeded_db)
        cart = Cart(seeded_db)
        cart.add_item(sku="WMOUSE01")

        result = sm.complete_sale(cart, employee_id=1, payment_method="card", card_last_four="9999")
        assert result["success"]

    def test_complete_sale_empty_cart(self, seeded_db):
        sm = SalesManager(seeded_db)
        cart = Cart(seeded_db)
        result = sm.complete_sale(cart, employee_id=1, payment_method="cash", cash_tendered=0)
        assert not result["success"]

    def test_sale_deducts_stock(self, seeded_db):
        pm = ProductManager()
        before = pm.get_product(sku="USB6FT01")["stock"]

        sm = SalesManager(seeded_db)
        cart = Cart(seeded_db)
        cart.add_item(sku="USB6FT01", quantity=3)
        sm.complete_sale(cart, employee_id=1, payment_method="cash", cash_tendered=100)

        after = pm.get_product(sku="USB6FT01")["stock"]
        assert after == before - 3

    def test_sale_with_customer(self, seeded_db):
        sm = SalesManager(seeded_db)
        cart = Cart(seeded_db)
        cart.add_item(sku="USB6FT01")
        cart.set_customer(1, "Alice Johnson")

        result = sm.complete_sale(cart, employee_id=1, payment_method="cash", cash_tendered=50)
        assert result["success"]
        assert result["loyalty_earned"] > 0

    def test_get_recent_sales(self, seeded_db):
        sm = SalesManager(seeded_db)
        sales = sm.get_recent_sales()
        assert len(sales) > 0

    def test_get_sale(self, seeded_db):
        sm = SalesManager(seeded_db)
        sales = sm.get_recent_sales()
        if sales:
            sale = sm.get_sale(sales[0]["transaction_id"])
            assert sale is not None
            assert sale["items"]

    def test_void_sale(self, seeded_db):
        sm = SalesManager(seeded_db)
        cart = Cart(seeded_db)
        cart.add_item(sku="USB6FT01", quantity=2)
        sale_result = sm.complete_sale(cart, employee_id=1, payment_method="cash", cash_tendered=50)

        void_result = sm.void_sale(sale_result["transaction_id"], employee_id=1)
        assert void_result["success"]

    def test_process_return(self, seeded_db):
        sm = SalesManager(seeded_db)
        cart = Cart(seeded_db)
        cart.add_item(sku="USB6FT01", quantity=3)
        sale_result = sm.complete_sale(cart, employee_id=1, payment_method="cash", cash_tendered=100)

        pm = ProductManager()
        product = pm.get_product(sku="USB6FT01")

        return_result = sm.process_return(
            sale_result["transaction_id"],
            product["id"], 1, "Defective", employee_id=1
        )
        assert return_result["success"]
        assert return_result["refund_amount"] > 0

    def test_receipt_saved_to_file(self, seeded_db):
        sm = SalesManager(seeded_db)
        cart = Cart(seeded_db)
        cart.add_item(sku="USB6FT01")
        result = sm.complete_sale(cart, employee_id=1, payment_method="cash", cash_tendered=50)
        assert result["success"]
        assert os.path.exists(result["receipt_path"])


# ═══════════════════════════════════════════════════════════════════════════
#  AUTH
# ═══════════════════════════════════════════════════════════════════════════

class TestAuth:
    def test_login_success(self, seeded_db):
        auth = AuthManager(seeded_db)
        result = auth.login("Admin", "1234")
        assert result["success"]
        assert auth.is_logged_in()
        assert auth.is_admin()

    def test_login_wrong_pin(self, seeded_db):
        auth = AuthManager(seeded_db)
        result = auth.login("Admin", "9999")
        assert not result["success"]

    def test_login_nonexistent(self, seeded_db):
        auth = AuthManager(seeded_db)
        result = auth.login("Nobody", "1234")
        assert not result["success"]

    def test_logout(self, seeded_db):
        auth = AuthManager(seeded_db)
        auth.login("Admin", "1234")
        name = auth.logout()
        assert name == "Admin User"
        assert not auth.is_logged_in()

    def test_role_check(self, seeded_db):
        auth = AuthManager(seeded_db)
        auth.login("John", "1111")
        assert auth.has_role(EmployeeRole.CASHIER)
        assert not auth.is_admin()
        assert not auth.is_manager_or_above()

    def test_manager_role(self, seeded_db):
        auth = AuthManager(seeded_db)
        auth.login("Jane", "5678")
        assert auth.is_manager_or_above()

    def test_list_employees(self, seeded_db):
        auth = AuthManager(seeded_db)
        emps = auth.list_employees()
        assert len(emps) == 4

    def test_account_lockout(self, seeded_db):
        auth = AuthManager(seeded_db)
        for _ in range(3):
            auth.login("Admin", "wrong")
        result = auth.login("Admin", "1234")
        assert not result["success"]
        assert "locked" in result["error"].lower()

    def test_unlock_employee(self, seeded_db):
        auth = AuthManager(seeded_db)
        # Lock the account
        for _ in range(3):
            auth.login("John", "wrong")

        # Login as admin to unlock
        auth.login("Admin", "1234")
        emps = auth.list_employees()
        john = next(e for e in emps if "John" in e["name"])
        result = auth.unlock_employee(john["employee_id"])
        assert result["success"]


# ═══════════════════════════════════════════════════════════════════════════
#  REPORTS
# ═══════════════════════════════════════════════════════════════════════════

class TestReports:
    def test_sales_summary(self, seeded_db):
        rm = ReportManager(seeded_db)
        summary = rm.sales_summary("last30")
        assert summary["total_sales"] > 0
        assert summary["total_revenue"] > 0

    def test_top_products(self, seeded_db):
        rm = ReportManager(seeded_db)
        top = rm.top_products("last30")
        assert len(top) > 0

    def test_revenue_by_category(self, seeded_db):
        rm = ReportManager(seeded_db)
        cats = rm.revenue_by_category("last30")
        assert len(cats) > 0

    def test_daily_revenue(self, seeded_db):
        rm = ReportManager(seeded_db)
        daily = rm.daily_revenue(14)
        assert len(daily) == 14

    def test_payment_breakdown(self, seeded_db):
        rm = ReportManager(seeded_db)
        breakdown = rm.payment_method_breakdown("last30")
        assert len(breakdown) > 0

    def test_profit_report(self, seeded_db):
        rm = ReportManager(seeded_db)
        profit = rm.profit_report("last30")
        assert profit["total_revenue"] > 0

    def test_export_sales_csv(self, seeded_db, tmp_path):
        rm = ReportManager(seeded_db)
        filepath = str(tmp_path / "test_sales.csv")
        result = rm.export_sales_csv("last30", filepath)
        assert os.path.exists(result)

    def test_export_inventory_csv(self, seeded_db, tmp_path):
        rm = ReportManager(seeded_db)
        filepath = str(tmp_path / "test_inventory.csv")
        result = rm.export_inventory_csv(filepath)
        assert os.path.exists(result)

    def test_empty_period(self, seeded_db):
        rm = ReportManager(seeded_db)
        summary = rm.sales_summary("yesterday")
        assert isinstance(summary["total_sales"], int)


# ═══════════════════════════════════════════════════════════════════════════
#  VALIDATORS
# ═══════════════════════════════════════════════════════════════════════════

class TestValidators:
    def test_email_valid(self):
        assert validate_email("test@example.com")
        assert validate_email("user.name+tag@domain.co")
        assert validate_email("")  # Optional

    def test_email_invalid(self):
        assert not validate_email("notanemail")
        assert not validate_email("@domain.com")

    def test_phone_valid(self):
        assert validate_phone("555-1234")
        assert validate_phone("+1 (555) 123-4567")
        assert validate_phone("")  # Optional

    def test_phone_invalid(self):
        assert not validate_phone("abc")
        assert not validate_phone("12")

    def test_pin_valid(self):
        assert validate_pin("1234")
        assert validate_pin("123456")

    def test_pin_invalid(self):
        assert not validate_pin("123")
        assert not validate_pin("abcd")

    def test_price_valid(self):
        assert validate_price(9.99)
        assert validate_price(0)
        assert validate_price("10.50")

    def test_price_invalid(self):
        assert not validate_price(-1)
        assert not validate_price("abc")

    def test_quantity_valid(self):
        assert validate_quantity(1)
        assert validate_quantity("5")

    def test_quantity_invalid(self):
        assert not validate_quantity(0)
        assert not validate_quantity(-1)

    def test_sku_valid(self):
        assert validate_sku("USB6FT01")
        assert validate_sku("TEST-01")

    def test_sku_invalid(self):
        assert not validate_sku("")
        assert not validate_sku("ab")

    def test_barcode_valid(self):
        assert validate_barcode("12345678")
        assert validate_barcode("")  # Optional

    def test_barcode_invalid(self):
        assert not validate_barcode("abc")
        assert not validate_barcode("123")

    def test_discount_valid(self):
        assert validate_discount_percent(0)
        assert validate_discount_percent(50)
        assert validate_discount_percent(100)

    def test_discount_invalid(self):
        assert not validate_discount_percent(-1)
        assert not validate_discount_percent(101)


# ═══════════════════════════════════════════════════════════════════════════
#  COMMAND PARSER
# ═══════════════════════════════════════════════════════════════════════════

class TestCommandParser:
    def test_parse_add(self):
        cmd = parse_pos_command("add USB6FT01 2")
        assert cmd["action"] == "add_item"
        assert cmd["args"] == ["USB6FT01", "2"]

    def test_parse_shortcut(self):
        cmd = parse_pos_command("a USB6FT01")
        assert cmd["action"] == "add_item"

    def test_parse_delete(self):
        cmd = parse_pos_command("del 1")
        assert cmd["action"] == "remove_item"

    def test_parse_pay(self):
        cmd = parse_pos_command("pay")
        assert cmd["action"] == "payment"

    def test_parse_empty(self):
        cmd = parse_pos_command("")
        assert cmd["action"] is None

    def test_parse_search(self):
        cmd = parse_pos_command("search cable usb")
        assert cmd["action"] == "search"
        assert cmd["args"] == ["cable", "usb"]

    def test_help_text(self):
        text = get_help_text()
        assert "add" in text
        assert "pay" in text


# ═══════════════════════════════════════════════════════════════════════════
#  COMMAND EXECUTOR
# ═══════════════════════════════════════════════════════════════════════════

class TestCommandExecutor:
    def test_execute_add(self, seeded_db):
        cart = Cart(seeded_db)
        pm = ProductManager()
        cm = CustomerManager(seeded_db)
        ce = CommandExecutor(cart, pm, cm)

        result = ce.execute("add USB6FT01")
        assert result["success"]
        assert cart.item_count == 1

    def test_execute_remove(self, seeded_db):
        cart = Cart(seeded_db)
        pm = ProductManager()
        cm = CustomerManager(seeded_db)
        ce = CommandExecutor(cart, pm, cm)

        ce.execute("add USB6FT01")
        result = ce.execute("del 1")
        assert result["success"]
        assert cart.is_empty

    def test_execute_clear(self, seeded_db):
        cart = Cart(seeded_db)
        pm = ProductManager()
        cm = CustomerManager(seeded_db)
        ce = CommandExecutor(cart, pm, cm)

        ce.execute("add USB6FT01")
        result = ce.execute("clear")
        assert result["success"]
        assert cart.is_empty

    def test_execute_search(self, seeded_db):
        cart = Cart(seeded_db)
        pm = ProductManager()
        cm = CustomerManager(seeded_db)
        ce = CommandExecutor(cart, pm, cm)

        result = ce.execute("search cable")
        assert result["success"]
        assert "results" in result

    def test_execute_unknown(self, seeded_db):
        cart = Cart(seeded_db)
        pm = ProductManager()
        cm = CustomerManager(seeded_db)
        ce = CommandExecutor(cart, pm, cm)

        result = ce.execute("foobar")
        assert not result["success"]


# ═══════════════════════════════════════════════════════════════════════════
#  INTEGRATION: FULL SALE WORKFLOW
# ═══════════════════════════════════════════════════════════════════════════

class TestIntegration:
    def test_full_sale_workflow(self, seeded_db):
        """Test complete sale from login to receipt."""
        # 1. Login
        auth = AuthManager(seeded_db)
        login = auth.login("Admin", "1234")
        assert login["success"]

        # 2. Create cart and add items
        cart = Cart(seeded_db)
        cart.add_item(sku="USB6FT01", quantity=2)
        cart.add_item(sku="COLA5001", quantity=3)
        cart.add_item(sku="CHIPS001", quantity=1)
        assert cart.item_count == 6

        # 3. Apply discount
        cart.apply_item_discount(cart.items[0].product_id, percent=10)
        assert cart.total_discounts > 0

        # 4. Attach customer
        cm = CustomerManager(seeded_db)
        custs = cm.list_customers()
        cart.set_customer(custs[0]["id"], custs[0]["name"])

        # 5. Process payment
        sm = SalesManager(seeded_db)
        result = sm.complete_sale(
            cart, employee_id=auth.get_current_employee()["id"],
            payment_method="cash", cash_tendered=100.00
        )
        assert result["success"]
        assert result["receipt"]
        assert result["loyalty_earned"] > 0

        # 6. Verify sale in history
        sale = sm.get_sale(result["transaction_id"])
        assert sale is not None
        assert sale["status"] == "completed"

        # 7. Process return
        return_result = sm.process_return(
            result["transaction_id"],
            cart.items[0].product_id if not cart.is_empty else sale["items"][0]["product"],
            1, "Changed mind", auth.get_current_employee()["id"]
        )
        # Cart was cleared after sale, use product from sale data
        pm = ProductManager()
        product = pm.get_product(sku="USB6FT01")
        return_result = sm.process_return(
            result["transaction_id"],
            product["id"], 1, "Changed mind",
            auth.get_current_employee()["id"]
        )
        assert return_result["success"]

        # 8. Check reports
        rm = ReportManager(seeded_db)
        summary = rm.sales_summary("today")
        assert summary["total_sales"] >= 1

    def test_full_inventory_workflow(self, seeded_db):
        """Test inventory operations end-to-end."""
        inv = InventoryManager(seeded_db)
        pm = ProductManager()

        # Check initial stock
        product = pm.get_product(sku="USB6FT01")
        initial = product["stock"]

        # Restock
        inv.restock(product["id"], 100, "PO-TEST")
        assert pm.get_product(sku="USB6FT01")["stock"] == initial + 100

        # Sell some
        inv.deduct_stock(product["id"], 30, "SALE-TEST")
        assert pm.get_product(sku="USB6FT01")["stock"] == initial + 70

        # Return some
        inv.return_stock(product["id"], 5, "RET-TEST")
        assert pm.get_product(sku="USB6FT01")["stock"] == initial + 75

        # Check history
        history = inv.get_stock_history(product["id"])
        assert len(history) >= 3

    def test_assistant_quick_sale(self, seeded_db):
        """Test the POSAssistant quick sale API."""
        from assistant import POSAssistant
        pos = POSAssistant(seeded_db)

        result = pos.quick_sale(
            employee_id=1,
            items=[
                {"product_id": 1, "quantity": 2},
                {"product_id": 2, "quantity": 1},
            ],
            payment_method="cash",
            cash_tendered=100.00,
        )
        assert result["success"]

    def test_assistant_dashboard(self, seeded_db):
        """Test the dashboard summary."""
        from assistant import POSAssistant
        pos = POSAssistant(seeded_db)
        dashboard = pos.get_dashboard()
        assert "sales_today" in dashboard
        assert "inventory" in dashboard
