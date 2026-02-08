"""
ElectroPOS - Database Management
Handles database initialization, sessions, and seed data.
"""

import os
import sys
import hashlib
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session

sys.path.insert(0, os.path.dirname(__file__))

from models import (
    Base, Category, Product, Customer, Employee, EmployeeRole,
    Sale, SaleItem, Payment, InventoryLog, PaymentMethod, TransactionStatus
)

_engine = None
_SessionFactory = None


def get_db_path(settings=None):
    if settings and "database" in settings:
        db_file = settings["database"].get("path", "pos_database.db")
    else:
        db_file = "pos_database.db"
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(project_root, db_file)


def hash_pin(pin: str) -> str:
    return hashlib.sha256(pin.encode()).hexdigest()


def verify_pin(pin: str, pin_hash: str) -> bool:
    return hashlib.sha256(pin.encode()).hexdigest() == pin_hash


def init_db(settings=None, db_path=None):
    global _engine, _SessionFactory

    if db_path is None:
        db_path = get_db_path(settings)

    echo = False
    if settings and "database" in settings:
        echo = settings["database"].get("echo", False)

    _engine = create_engine(f"sqlite:///{db_path}", echo=echo)

    @event.listens_for(_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(_engine)
    _SessionFactory = sessionmaker(bind=_engine)
    return _engine


def get_session() -> Session:
    if _SessionFactory is None:
        init_db()
    return _SessionFactory()


def seed_database(session: Session):
    """Populate the database with demo data for immediate use."""

    existing = session.query(Category).first()
    if existing:
        return False

    # ── Categories ──
    categories_data = [
        ("Electronics", "Electronic devices and accessories"),
        ("Beverages", "Drinks and refreshments"),
        ("Snacks", "Chips, candy, and quick bites"),
        ("Groceries", "Everyday grocery items"),
        ("Personal Care", "Health and beauty products"),
        ("Office Supplies", "Stationery and office items"),
        ("Clothing", "Apparel and accessories"),
        ("Home & Kitchen", "Household and kitchen items"),
    ]
    categories = {}
    for name, desc in categories_data:
        cat = Category(name=name, description=desc)
        session.add(cat)
        session.flush()
        categories[name] = cat

    # ── Products ──
    products_data = [
        ("USB-C Cable 6ft", "Electronics", 12.99, 5.50, 150, "USB6FT01", "4901234567890"),
        ("Wireless Mouse", "Electronics", 24.99, 10.00, 75, "WMOUSE01", "4901234567891"),
        ("Bluetooth Speaker", "Electronics", 49.99, 22.00, 40, "BTSPK001", "4901234567892"),
        ("Phone Case Universal", "Electronics", 15.99, 4.00, 200, "PCASE001", "4901234567893"),
        ("Screen Protector", "Electronics", 9.99, 2.00, 300, "SCRPRT01", "4901234567894"),
        ("Earbuds Wired", "Electronics", 14.99, 5.00, 120, "EARBD001", "4901234567895"),
        ("Power Bank 10000mAh", "Electronics", 29.99, 12.00, 60, "PWRBK001", "4901234567896"),
        ("HDMI Cable 3ft", "Electronics", 8.99, 3.00, 180, "HDMI3F01", "4901234567897"),
        ("Cola 500ml", "Beverages", 1.99, 0.60, 500, "COLA5001", "5901234567890"),
        ("Water Bottle 1L", "Beverages", 1.49, 0.30, 600, "WATER101", "5901234567891"),
        ("Orange Juice 1L", "Beverages", 3.99, 1.50, 200, "OJ1L0001", "5901234567892"),
        ("Energy Drink 250ml", "Beverages", 2.99, 1.00, 350, "ENRGY001", "5901234567893"),
        ("Coffee Beans 500g", "Beverages", 12.99, 6.00, 80, "COFBN001", "5901234567894"),
        ("Green Tea Box", "Beverages", 5.99, 2.50, 150, "GRTEA001", "5901234567895"),
        ("Potato Chips Large", "Snacks", 4.49, 1.50, 250, "CHIPS001", "6901234567890"),
        ("Chocolate Bar", "Snacks", 2.49, 0.80, 400, "CHOCO001", "6901234567891"),
        ("Mixed Nuts 200g", "Snacks", 6.99, 3.00, 120, "MNUTS001", "6901234567892"),
        ("Granola Bar 6pk", "Snacks", 5.49, 2.20, 180, "GRNLA001", "6901234567893"),
        ("Popcorn Microwave", "Snacks", 3.99, 1.20, 200, "POPCN001", "6901234567894"),
        ("Rice 5kg", "Groceries", 8.99, 4.50, 100, "RICE5K01", "7901234567890"),
        ("Pasta 500g", "Groceries", 2.49, 0.90, 300, "PASTA001", "7901234567891"),
        ("Olive Oil 500ml", "Groceries", 7.99, 4.00, 90, "OLVOL001", "7901234567892"),
        ("Canned Tomatoes", "Groceries", 1.99, 0.70, 250, "CNTOM001", "7901234567893"),
        ("Bread Whole Wheat", "Groceries", 3.49, 1.50, 80, "BREAD001", "7901234567894"),
        ("Shampoo 400ml", "Personal Care", 6.99, 2.50, 150, "SHAMP001", "8901234567890"),
        ("Toothpaste 150g", "Personal Care", 3.99, 1.20, 200, "TOOTH001", "8901234567891"),
        ("Hand Sanitizer", "Personal Care", 4.49, 1.50, 180, "HSANI001", "8901234567892"),
        ("Sunscreen SPF50", "Personal Care", 11.99, 5.00, 100, "SUNSC001", "8901234567893"),
        ("Notebook A5", "Office Supplies", 3.99, 1.00, 250, "NOTBK001", "9901234567890"),
        ("Pen Pack 10pc", "Office Supplies", 5.99, 1.80, 200, "PENPC001", "9901234567891"),
        ("Sticky Notes 3x3", "Office Supplies", 2.99, 0.80, 300, "STNOT001", "9901234567892"),
        ("Stapler", "Office Supplies", 7.99, 3.00, 80, "STPLR001", "9901234567893"),
        ("T-Shirt Basic", "Clothing", 14.99, 5.00, 100, "TSHRT001", "1091234567890"),
        ("Baseball Cap", "Clothing", 12.99, 4.00, 80, "BSCAP001", "1091234567891"),
        ("Socks 3-Pack", "Clothing", 8.99, 3.00, 150, "SOCKS001", "1091234567892"),
        ("Kitchen Towel Roll", "Home & Kitchen", 4.99, 1.50, 200, "KTWEL001", "1191234567890"),
        ("Dish Soap 500ml", "Home & Kitchen", 3.49, 1.00, 180, "DSOAP001", "1191234567891"),
        ("Food Container Set", "Home & Kitchen", 9.99, 4.00, 60, "FCONT001", "1191234567892"),
        ("LED Bulb 10W", "Home & Kitchen", 5.99, 2.00, 250, "LEDBR001", "1191234567893"),
    ]

    products = []
    for name, cat_name, price, cost, stock, sku, barcode in products_data:
        p = Product(
            name=name,
            category_id=categories[cat_name].id,
            price=price,
            cost=cost,
            stock_quantity=stock,
            sku=sku,
            barcode=barcode,
            description=f"Quality {name.lower()}"
        )
        session.add(p)
        products.append(p)
    session.flush()

    # ── Customers ──
    customers_data = [
        ("Alice", "Johnson", "alice@email.com", "555-0101", 250, 1250.00),
        ("Bob", "Smith", "bob@email.com", "555-0102", 180, 890.00),
        ("Carol", "Williams", "carol@email.com", "555-0103", 420, 2100.00),
        ("David", "Brown", "david@email.com", "555-0104", 90, 450.00),
        ("Emma", "Davis", "emma@email.com", "555-0105", 310, 1550.00),
        ("Frank", "Miller", "frank@email.com", "555-0106", 50, 250.00),
        ("Grace", "Wilson", "grace@email.com", "555-0107", 600, 3000.00),
        ("Henry", "Moore", "henry@email.com", "555-0108", 150, 750.00),
    ]
    customers = []
    for fn, ln, email, phone, points, spent in customers_data:
        c = Customer(
            first_name=fn, last_name=ln, email=email, phone=phone,
            loyalty_points=points, total_spent=spent, visit_count=points // 25
        )
        session.add(c)
        customers.append(c)
    session.flush()

    # ── Employees ──
    employees_data = [
        ("Admin", "User", "admin@store.com", "1234", EmployeeRole.ADMIN),
        ("Jane", "Manager", "jane@store.com", "5678", EmployeeRole.MANAGER),
        ("John", "Cashier", "john@store.com", "1111", EmployeeRole.CASHIER),
        ("Sarah", "Cashier", "sarah@store.com", "2222", EmployeeRole.CASHIER),
    ]
    employees = []
    for fn, ln, email, pin, role in employees_data:
        e = Employee(
            first_name=fn, last_name=ln, email=email,
            pin_hash=hash_pin(pin), role=role
        )
        session.add(e)
        employees.append(e)
    session.flush()

    # ── Sample Sales History ──
    now = datetime.now(timezone.utc)
    for day_offset in range(14):
        sale_date = now - timedelta(days=day_offset)
        num_sales = 3 if day_offset < 7 else 2
        for s_idx in range(num_sales):
            emp = employees[s_idx % len(employees)]
            cust = customers[s_idx % len(customers)] if s_idx % 2 == 0 else None

            sale = Sale(
                employee_id=emp.id,
                customer_id=cust.id if cust else None,
                payment_method=PaymentMethod.CASH if s_idx % 2 == 0 else PaymentMethod.CARD,
                status=TransactionStatus.COMPLETED,
                created_at=sale_date,
            )
            session.add(sale)
            session.flush()

            subtotal = 0.0
            num_items = 2 + (s_idx % 3)
            for i_idx in range(num_items):
                prod = products[(day_offset * 3 + s_idx + i_idx) % len(products)]
                qty = 1 + (i_idx % 3)
                line_total = round(prod.price * qty, 2)
                tax = round(line_total * 0.08, 2)
                subtotal += line_total

                item = SaleItem(
                    sale_id=sale.id,
                    product_id=prod.id,
                    product_name=prod.name,
                    quantity=qty,
                    unit_price=prod.price,
                    tax_amount=tax,
                    line_total=line_total,
                )
                session.add(item)

            tax_total = round(subtotal * 0.08, 2)
            total = round(subtotal + tax_total, 2)
            sale.subtotal = subtotal
            sale.tax_amount = tax_total
            sale.total = total
            if sale.payment_method == PaymentMethod.CASH:
                sale.cash_tendered = float(int(total / 10) * 10 + 10)
                sale.change_due = round(sale.cash_tendered - total, 2)
            if cust:
                points = int(total * 10)
                sale.loyalty_points_earned = points

    session.commit()
    return True


def reset_database(settings=None):
    db_path = get_db_path(settings)
    if os.path.exists(db_path):
        os.remove(db_path)
    return init_db(settings, db_path)
