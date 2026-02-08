"""
ElectroPOS - Database Models
SQLAlchemy ORM models for the complete POS system.
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey,
    Text, Enum as SAEnum, UniqueConstraint, Index
)
from sqlalchemy.orm import declarative_base, relationship
import enum
import uuid

Base = declarative_base()


def generate_uuid():
    return str(uuid.uuid4())[:8].upper()


class EmployeeRole(enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    CASHIER = "cashier"


class PaymentMethod(enum.Enum):
    CASH = "cash"
    CARD = "card"
    SPLIT = "split"


class TransactionStatus(enum.Enum):
    COMPLETED = "completed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"
    VOIDED = "voided"


class ReturnStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


# ─── Category ───────────────────────────────────────────────────────────────

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    products = relationship("Product", back_populates="category", lazy="selectin")

    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}')>"


# ─── Product ────────────────────────────────────────────────────────────────

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sku = Column(String(20), unique=True, nullable=False, default=generate_uuid)
    barcode = Column(String(50), unique=True, nullable=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    price = Column(Float, nullable=False)
    cost = Column(Float, default=0.0)
    stock_quantity = Column(Integer, default=0)
    min_stock_level = Column(Integer, default=10)
    is_active = Column(Boolean, default=True)
    is_taxable = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    category = relationship("Category", back_populates="products")
    sale_items = relationship("SaleItem", back_populates="product", lazy="selectin")
    inventory_logs = relationship("InventoryLog", back_populates="product", lazy="selectin")

    __table_args__ = (
        Index("idx_product_sku", "sku"),
        Index("idx_product_barcode", "barcode"),
        Index("idx_product_name", "name"),
    )

    @property
    def profit_margin(self):
        if self.cost and self.cost > 0:
            return ((self.price - self.cost) / self.price) * 100
        return 0.0

    def __repr__(self):
        return f"<Product(id={self.id}, sku='{self.sku}', name='{self.name}', price={self.price})>"


# ─── Customer ───────────────────────────────────────────────────────────────

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), unique=True, nullable=False, default=generate_uuid)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(200), unique=True, nullable=True)
    phone = Column(String(20), nullable=True)
    address = Column(Text, default="")
    loyalty_points = Column(Integer, default=0)
    total_spent = Column(Float, default=0.0)
    visit_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    sales = relationship("Sale", back_populates="customer", lazy="selectin")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f"<Customer(id={self.id}, name='{self.full_name}', points={self.loyalty_points})>"


# ─── Employee ───────────────────────────────────────────────────────────────

class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(String(20), unique=True, nullable=False, default=generate_uuid)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(200), unique=True, nullable=True)
    phone = Column(String(20), nullable=True)
    pin_hash = Column(String(200), nullable=False)
    role = Column(SAEnum(EmployeeRole), default=EmployeeRole.CASHIER)
    is_active = Column(Boolean, default=True)
    login_attempts = Column(Integer, default=0)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    sales = relationship("Sale", back_populates="employee", lazy="selectin")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f"<Employee(id={self.id}, name='{self.full_name}', role={self.role.value})>"


# ─── Sale ────────────────────────────────────────────────────────────────────

class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(String(20), unique=True, nullable=False, default=generate_uuid)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    subtotal = Column(Float, default=0.0)
    tax_amount = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)
    discount_percent = Column(Float, default=0.0)
    total = Column(Float, default=0.0)
    payment_method = Column(SAEnum(PaymentMethod), default=PaymentMethod.CASH)
    cash_tendered = Column(Float, default=0.0)
    change_due = Column(Float, default=0.0)
    card_last_four = Column(String(4), nullable=True)
    status = Column(SAEnum(TransactionStatus), default=TransactionStatus.COMPLETED)
    loyalty_points_earned = Column(Integer, default=0)
    loyalty_points_redeemed = Column(Integer, default=0)
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    employee = relationship("Employee", back_populates="sales")
    customer = relationship("Customer", back_populates="sales")
    items = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan", lazy="selectin")
    payments = relationship("Payment", back_populates="sale", cascade="all, delete-orphan", lazy="selectin")
    returns = relationship("Return", back_populates="sale", lazy="selectin")

    __table_args__ = (
        Index("idx_sale_transaction_id", "transaction_id"),
        Index("idx_sale_created_at", "created_at"),
    )

    @property
    def item_count(self):
        return sum(item.quantity for item in self.items)

    def __repr__(self):
        return f"<Sale(id={self.id}, txn='{self.transaction_id}', total={self.total})>"


# ─── SaleItem ───────────────────────────────────────────────────────────────

class SaleItem(Base):
    __tablename__ = "sale_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product_name = Column(String(200), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Float, nullable=False)
    discount_amount = Column(Float, default=0.0)
    tax_amount = Column(Float, default=0.0)
    line_total = Column(Float, nullable=False)

    sale = relationship("Sale", back_populates="items")
    product = relationship("Product", back_populates="sale_items")

    def __repr__(self):
        return f"<SaleItem(product='{self.product_name}', qty={self.quantity}, total={self.line_total})>"


# ─── Payment ────────────────────────────────────────────────────────────────

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False)
    method = Column(SAEnum(PaymentMethod), nullable=False)
    amount = Column(Float, nullable=False)
    reference = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    sale = relationship("Sale", back_populates="payments")

    def __repr__(self):
        return f"<Payment(method={self.method.value}, amount={self.amount})>"


# ─── Return ──────────────────────────────────────────────────────────────────

class Return(Base):
    __tablename__ = "returns"

    id = Column(Integer, primary_key=True, autoincrement=True)
    return_id = Column(String(20), unique=True, nullable=False, default=generate_uuid)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    refund_amount = Column(Float, nullable=False)
    reason = Column(Text, default="")
    status = Column(SAEnum(ReturnStatus), default=ReturnStatus.APPROVED)
    restock = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    sale = relationship("Sale", back_populates="returns")

    def __repr__(self):
        return f"<Return(id='{self.return_id}', amount={self.refund_amount})>"


# ─── InventoryLog ────────────────────────────────────────────────────────────

class InventoryLog(Base):
    __tablename__ = "inventory_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    change_type = Column(String(50), nullable=False)  # sale, restock, adjustment, return
    quantity_change = Column(Integer, nullable=False)
    quantity_before = Column(Integer, nullable=False)
    quantity_after = Column(Integer, nullable=False)
    reference = Column(String(100), nullable=True)
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    product = relationship("Product", back_populates="inventory_logs")

    __table_args__ = (
        Index("idx_inventory_log_product", "product_id"),
        Index("idx_inventory_log_created", "created_at"),
    )

    def __repr__(self):
        return f"<InventoryLog(product={self.product_id}, change={self.quantity_change}, type='{self.change_type}')>"
