# ElectroPOS - Electronic Point of Sale System

A comprehensive, feature-rich Point of Sale (POS) system built in Python with a beautiful terminal interface.

---

## Features

### Core POS Operations
- **New Sale**: Full shopping cart workflow with barcode/SKU scanning
- **Multiple Payment Methods**: Cash (with change calculation), Card, Split payments
- **Discounts**: Per-item percentage/flat discounts, cart-wide discounts
- **Tax Calculation**: Configurable tax rates with automatic calculation
- **Receipt Generation**: Formatted text receipts saved to file

### Product Management
- Add, edit, search, and deactivate products
- SKU and barcode support
- Category organization
- Profit margin tracking

### Inventory Management
- Real-time stock tracking
- Low stock alerts with configurable thresholds
- Stock adjustment history
- Restock and bulk operations
- Inventory valuation summary

### Customer & Loyalty
- Customer profiles with contact info
- Loyalty points system (earn & redeem)
- Purchase history tracking
- Top customer rankings

### Employee Management
- PIN-based authentication
- Role-based access control (Admin / Manager / Cashier)
- Account locking after failed attempts
- Session management

### Sales & Returns
- Complete transaction history
- Transaction lookup by ID
- Return/refund processing with restocking
- Sale voiding (manager+ only)

### Reports & Analytics
- Daily/weekly/monthly/yearly sales summaries
- Top selling products
- Revenue by category
- Daily revenue trends with ASCII bar charts
- Payment method breakdown
- Profit reports with margin analysis
- CSV export for sales and inventory

---

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run the POS system
cd src
python main.py
```

### Default Login Credentials

| Employee | Role    | PIN  |
|----------|---------|------|
| Admin    | Admin   | 1234 |
| Jane     | Manager | 5678 |
| John     | Cashier | 1111 |
| Sarah    | Cashier | 2222 |

### First Run
On first launch, the system automatically:
1. Creates the SQLite database
2. Seeds demo data (8 categories, 39 products, 8 customers, 4 employees, 14 days of sales history)

---

## Project Structure

```
electropos/
├── config/
│   ├── pos_settings.yaml      # Store, tax, currency, loyalty settings
│   ├── command_blacklist.json  # Safety: blocked commands
│   └── command_whitelist.json  # Safety: allowed commands
├── src/
│   ├── main.py                # Main application entry point (CLI/TUI)
│   ├── models.py              # SQLAlchemy ORM models
│   ├── database.py            # Database initialization & seeding
│   ├── auth.py                # Employee authentication
│   ├── product_manager.py     # Product & category CRUD
│   ├── inventory_manager.py   # Stock tracking & alerts
│   ├── customer_manager.py    # Customer profiles & loyalty
│   ├── cart.py                # Shopping cart with discounts/tax
│   ├── payment_processor.py   # Cash, card, split payments
│   ├── receipt_generator.py   # Text receipt formatting
│   ├── sales_manager.py       # Sale lifecycle & returns
│   ├── reports.py             # Analytics & CSV export
│   ├── command_parser.py      # POS command parsing
│   ├── command_executor.py    # Command execution engine
│   ├── validator.py           # Input validation
│   ├── logger.py              # Application logging
│   ├── assistant.py           # High-level API for scripting
│   └── platform_utils.py      # Platform detection
├── tests/
│   └── test_pos.py            # Comprehensive test suite
├── receipts/                  # Generated receipts (auto-created)
├── exports/                   # CSV exports (auto-created)
├── logs/                      # Application logs
└── requirements.txt
```

---

## Configuration

Edit `config/pos_settings.yaml` to customize:

- **Store Info**: Name, address, phone, email
- **Tax**: Rate, enable/disable
- **Currency**: Symbol, code, decimal places
- **Receipt**: Width, footer message, tax breakdown
- **Loyalty**: Points per dollar, redemption rate
- **Inventory**: Low stock threshold, history tracking
- **Security**: Max login attempts, session timeout, manager requirements

---

## POS Sale Commands

During a sale, use these commands:

| Command | Description |
|---------|-------------|
| `add <sku/barcode/id> [qty]` | Add item to cart |
| `qty <#> <quantity>` | Update item quantity |
| `del <#>` | Remove item from cart |
| `disc <#> <percent>` | Apply item discount |
| `cartdisc <percent>` | Cart-wide discount |
| `customer` | Attach customer |
| `loyalty` | Redeem loyalty points |
| `search <query>` | Search products |
| `pay` | Proceed to payment |
| `clear` | Clear cart |
| `cancel` | Cancel sale |

---

## Technology Stack

- **Python 3.8+**
- **SQLAlchemy** - ORM and database management
- **SQLite** - Embedded database (zero configuration)
- **Rich** - Beautiful terminal UI (tables, panels, prompts)
- **PyYAML** - Configuration management

---

## Running Tests

```bash
cd /path/to/project
python -m pytest tests/ -v
```

---

## License

MIT License
