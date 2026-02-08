"""
ElectroPOS - Product Manager
CRUD operations for products and categories.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from models import Product, Category
from database import get_session


class ProductManager:
    """Manages products and categories."""

    # ── Category Operations ──────────────────────────────────────────────

    def list_categories(self) -> list:
        session = get_session()
        try:
            cats = session.query(Category).order_by(Category.name).all()
            return [
                {
                    "id": c.id,
                    "name": c.name,
                    "description": c.description,
                    "product_count": len(c.products),
                }
                for c in cats
            ]
        finally:
            session.close()

    def create_category(self, name: str, description: str = "") -> dict:
        session = get_session()
        try:
            existing = session.query(Category).filter(Category.name == name).first()
            if existing:
                return {"success": False, "error": f"Category '{name}' already exists."}
            cat = Category(name=name, description=description)
            session.add(cat)
            session.commit()
            return {"success": True, "id": cat.id, "message": f"Category '{name}' created."}
        except Exception as e:
            session.rollback()
            return {"success": False, "error": str(e)}
        finally:
            session.close()

    def delete_category(self, category_id: int) -> dict:
        session = get_session()
        try:
            cat = session.query(Category).get(category_id)
            if not cat:
                return {"success": False, "error": "Category not found."}
            if cat.products:
                return {"success": False, "error": f"Category has {len(cat.products)} products. Remove them first."}
            session.delete(cat)
            session.commit()
            return {"success": True, "message": f"Category '{cat.name}' deleted."}
        except Exception as e:
            session.rollback()
            return {"success": False, "error": str(e)}
        finally:
            session.close()

    # ── Product Operations ───────────────────────────────────────────────

    def list_products(self, category_id: int = None, active_only: bool = True,
                      search: str = None) -> list:
        session = get_session()
        try:
            query = session.query(Product)
            if active_only:
                query = query.filter(Product.is_active == True)
            if category_id:
                query = query.filter(Product.category_id == category_id)
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    (Product.name.ilike(search_term)) |
                    (Product.sku.ilike(search_term)) |
                    (Product.barcode.ilike(search_term))
                )
            products = query.order_by(Product.name).all()
            return [
                {
                    "id": p.id,
                    "sku": p.sku,
                    "barcode": p.barcode,
                    "name": p.name,
                    "category": p.category.name if p.category else "Uncategorized",
                    "price": p.price,
                    "cost": p.cost,
                    "stock": p.stock_quantity,
                    "margin": round(p.profit_margin, 1),
                    "active": p.is_active,
                    "taxable": p.is_taxable,
                }
                for p in products
            ]
        finally:
            session.close()

    def get_product(self, product_id: int = None, sku: str = None, barcode: str = None) -> dict:
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
                return None

            if not product:
                return None

            return {
                "id": product.id,
                "sku": product.sku,
                "barcode": product.barcode,
                "name": product.name,
                "description": product.description,
                "category": product.category.name if product.category else "Uncategorized",
                "category_id": product.category_id,
                "price": product.price,
                "cost": product.cost,
                "stock": product.stock_quantity,
                "min_stock": product.min_stock_level,
                "margin": round(product.profit_margin, 1),
                "active": product.is_active,
                "taxable": product.is_taxable,
            }
        finally:
            session.close()

    def create_product(self, name: str, price: float, category_id: int = None,
                       cost: float = 0.0, stock: int = 0, barcode: str = None,
                       description: str = "", taxable: bool = True,
                       min_stock: int = 10) -> dict:
        session = get_session()
        try:
            if price < 0:
                return {"success": False, "error": "Price cannot be negative."}

            product = Product(
                name=name,
                price=price,
                cost=cost,
                category_id=category_id,
                stock_quantity=stock,
                barcode=barcode,
                description=description,
                is_taxable=taxable,
                min_stock_level=min_stock,
            )
            session.add(product)
            session.commit()
            return {
                "success": True,
                "id": product.id,
                "sku": product.sku,
                "message": f"Product '{name}' created (SKU: {product.sku})."
            }
        except Exception as e:
            session.rollback()
            return {"success": False, "error": str(e)}
        finally:
            session.close()

    def update_product(self, product_id: int, **kwargs) -> dict:
        session = get_session()
        try:
            product = session.query(Product).get(product_id)
            if not product:
                return {"success": False, "error": "Product not found."}

            allowed_fields = {
                "name", "price", "cost", "category_id", "barcode",
                "description", "is_taxable", "is_active", "min_stock_level"
            }
            for key, value in kwargs.items():
                if key in allowed_fields:
                    setattr(product, key, value)

            session.commit()
            return {"success": True, "message": f"Product '{product.name}' updated."}
        except Exception as e:
            session.rollback()
            return {"success": False, "error": str(e)}
        finally:
            session.close()

    def delete_product(self, product_id: int, soft: bool = True) -> dict:
        session = get_session()
        try:
            product = session.query(Product).get(product_id)
            if not product:
                return {"success": False, "error": "Product not found."}
            if soft:
                product.is_active = False
                msg = f"Product '{product.name}' deactivated."
            else:
                session.delete(product)
                msg = f"Product '{product.name}' permanently deleted."
            session.commit()
            return {"success": True, "message": msg}
        except Exception as e:
            session.rollback()
            return {"success": False, "error": str(e)}
        finally:
            session.close()

    def search_products(self, query: str) -> list:
        return self.list_products(search=query)

    def get_low_stock_products(self, threshold: int = None) -> list:
        session = get_session()
        try:
            query = session.query(Product).filter(
                Product.is_active == True,
                Product.stock_quantity <= Product.min_stock_level
            )
            if threshold is not None:
                query = session.query(Product).filter(
                    Product.is_active == True,
                    Product.stock_quantity <= threshold
                )
            products = query.order_by(Product.stock_quantity).all()
            return [
                {
                    "id": p.id,
                    "sku": p.sku,
                    "name": p.name,
                    "stock": p.stock_quantity,
                    "min_stock": p.min_stock_level,
                    "category": p.category.name if p.category else "N/A",
                }
                for p in products
            ]
        finally:
            session.close()
