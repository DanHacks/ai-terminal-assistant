"""
ElectroPOS - Main Application
Interactive CLI/TUI Point of Sale System.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import yaml
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, IntPrompt, FloatPrompt, Confirm
from rich.columns import Columns
from rich import box

from database import init_db, get_session, seed_database
from auth import AuthManager
from product_manager import ProductManager
from inventory_manager import InventoryManager
from customer_manager import CustomerManager
from cart import Cart
from sales_manager import SalesManager
from reports import ReportManager
from models import EmployeeRole

console = Console()


def load_settings():
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "pos_settings.yaml")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    return {}


# ═══════════════════════════════════════════════════════════════════════════
#  UI HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def show_banner(settings):
    store_name = settings.get("store", {}).get("name", "ElectroPOS")
    banner = Text()
    banner.append("╔══════════════════════════════════════════════════╗\n", style="bold cyan")
    banner.append("║                                                  ║\n", style="bold cyan")
    banner.append(f"║  {store_name:^46}  ║\n", style="bold cyan")
    banner.append("║          Electronic Point of Sale System          ║\n", style="bold cyan")
    banner.append("║                                                  ║\n", style="bold cyan")
    banner.append("╚══════════════════════════════════════════════════╝", style="bold cyan")
    console.print(banner)


def show_menu(title: str, options: list, back_label: str = "Back"):
    console.print()
    console.print(Panel(f"[bold]{title}[/bold]", style="cyan", box=box.DOUBLE))
    for i, (label, _) in enumerate(options, 1):
        console.print(f"  [bold yellow]{i}[/bold yellow]. {label}")
    console.print(f"  [bold red]0[/bold red]. {back_label}")
    console.print()

    while True:
        try:
            choice = IntPrompt.ask("[bold green]Select option[/bold green]")
            if 0 <= choice <= len(options):
                return choice
            console.print("[red]Invalid option. Try again.[/red]")
        except (ValueError, KeyboardInterrupt):
            return 0


def show_table(title: str, columns: list, rows: list, show_index: bool = False):
    table = Table(title=title, box=box.ROUNDED, show_lines=True,
                  title_style="bold magenta", header_style="bold cyan")
    if show_index:
        table.add_column("#", style="dim", width=4)
    for col_name, col_style in columns:
        table.add_column(col_name, style=col_style)
    for i, row in enumerate(rows, 1):
        if show_index:
            table.add_row(str(i), *[str(v) for v in row])
        else:
            table.add_row(*[str(v) for v in row])
    console.print(table)


def pause():
    console.print()
    Prompt.ask("[dim]Press Enter to continue[/dim]", default="")


def format_money(amount, settings):
    symbol = settings.get("currency", {}).get("symbol", "$")
    return f"{symbol}{amount:.2f}"


# ═══════════════════════════════════════════════════════════════════════════
#  LOGIN SCREEN
# ═══════════════════════════════════════════════════════════════════════════

def login_screen(auth: AuthManager) -> bool:
    console.print()
    console.print(Panel("[bold]Employee Login[/bold]", style="cyan"))
    console.print("[dim]Default accounts: Admin(PIN:1234), Jane(PIN:5678), John(PIN:1111), Sarah(PIN:2222)[/dim]")
    console.print()

    name = Prompt.ask("[bold]Employee name or ID[/bold]")
    pin = Prompt.ask("[bold]PIN[/bold]", password=True)

    result = auth.login(name, pin)
    if result["success"]:
        emp = result["employee"]
        console.print(f"\n[bold green]Welcome, {emp['name']}![/bold green] Role: [cyan]{emp['role'].value}[/cyan]")
        return True
    else:
        console.print(f"\n[bold red]Login failed:[/bold red] {result['error']}")
        return False


# ═══════════════════════════════════════════════════════════════════════════
#  NEW SALE (MAIN POS WORKFLOW)
# ═══════════════════════════════════════════════════════════════════════════

def new_sale_screen(cart: Cart, sales: SalesManager, customers: CustomerManager,
                    products: ProductManager, auth: AuthManager, settings: dict):
    cart.clear()
    symbol = settings.get("currency", {}).get("symbol", "$")

    while True:
        clear_screen()
        console.print(Panel("[bold]NEW SALE[/bold]", style="green", box=box.DOUBLE))

        # Show cart
        if not cart.is_empty:
            cart_table = Table(title="Shopping Cart", box=box.SIMPLE_HEAVY,
                              title_style="bold green", header_style="bold")
            cart_table.add_column("#", style="dim", width=4)
            cart_table.add_column("Product", style="white", min_width=20)
            cart_table.add_column("SKU", style="dim")
            cart_table.add_column("Price", style="cyan", justify="right")
            cart_table.add_column("Qty", style="yellow", justify="center")
            cart_table.add_column("Discount", style="red", justify="right")
            cart_table.add_column("Total", style="bold green", justify="right")

            for i, item in enumerate(cart.items, 1):
                disc = f"-{symbol}{item.discount_total:.2f}" if item.discount_total > 0 else "-"
                cart_table.add_row(
                    str(i), item.name, item.sku,
                    f"{symbol}{item.price:.2f}", str(item.quantity),
                    disc, f"{symbol}{item.line_total:.2f}"
                )
            console.print(cart_table)

            # Summary
            summary = cart.get_summary()
            console.print()
            console.print(f"  Items: [bold]{summary['item_count']}[/bold]  |  "
                          f"Subtotal: [cyan]{symbol}{summary['subtotal']:.2f}[/cyan]  |  "
                          f"Tax: [yellow]{symbol}{summary['tax_amount']:.2f}[/yellow]  |  "
                          f"[bold green]Total: {symbol}{summary['total']:.2f}[/bold green]")
            if summary["total_discounts"] > 0:
                console.print(f"  [red]Savings: -{symbol}{summary['total_discounts']:.2f}[/red]")
            if cart.customer_name:
                console.print(f"  Customer: [cyan]{cart.customer_name}[/cyan]")
        else:
            console.print("[dim]Cart is empty. Add items to begin.[/dim]")

        console.print()
        console.print("[bold yellow]Commands:[/bold yellow]")
        console.print("  [green]add[/green] <sku/barcode/id>  - Add item to cart")
        console.print("  [green]qty[/green] <#> <quantity>     - Update item quantity")
        console.print("  [green]del[/green] <#>               - Remove item from cart")
        console.print("  [green]disc[/green] <#> <percent>    - Discount on item")
        console.print("  [green]cartdisc[/green] <percent>    - Discount on entire cart")
        console.print("  [green]customer[/green]              - Attach customer")
        console.print("  [green]search[/green] <query>        - Search products")
        console.print("  [green]pay[/green]                   - Proceed to payment")
        console.print("  [green]clear[/green]                 - Clear cart")
        console.print("  [green]cancel[/green]                - Cancel sale")
        console.print()

        cmd = Prompt.ask("[bold green]POS[/bold green]").strip()
        if not cmd:
            continue

        parts = cmd.split(maxsplit=1)
        action = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if action == "cancel":
            cart.clear()
            return

        elif action == "clear":
            cart.clear()
            console.print("[yellow]Cart cleared.[/yellow]")
            pause()

        elif action == "add":
            if not arg:
                arg = Prompt.ask("Enter SKU, barcode, or product ID")
            qty = 1
            arg_parts = arg.split()
            lookup = arg_parts[0]
            if len(arg_parts) > 1:
                try:
                    qty = int(arg_parts[1])
                except ValueError:
                    pass

            # Try by ID, SKU, then barcode
            result = None
            if lookup.isdigit():
                result = cart.add_item(product_id=int(lookup), quantity=qty)
            if not result or not result.get("success"):
                result = cart.add_item(sku=lookup, quantity=qty)
            if not result.get("success"):
                result = cart.add_item(barcode=lookup, quantity=qty)

            if result["success"]:
                console.print(f"[green]{result['message']}[/green]")
            else:
                console.print(f"[red]{result['error']}[/red]")
            pause()

        elif action == "qty":
            try:
                arg_parts = arg.split()
                idx = int(arg_parts[0]) - 1
                new_qty = int(arg_parts[1])
                item = cart.items[idx]
                result = cart.update_quantity(item.product_id, new_qty)
                console.print(f"[green]{result['message']}[/green]" if result["success"]
                              else f"[red]{result['error']}[/red]")
            except (IndexError, ValueError):
                console.print("[red]Usage: qty <item#> <quantity>[/red]")
            pause()

        elif action == "del":
            try:
                idx = int(arg) - 1
                item = cart.items[idx]
                result = cart.remove_item(item.product_id)
                console.print(f"[green]{result['message']}[/green]" if result["success"]
                              else f"[red]{result['error']}[/red]")
            except (IndexError, ValueError):
                console.print("[red]Usage: del <item#>[/red]")
            pause()

        elif action == "disc":
            try:
                arg_parts = arg.split()
                idx = int(arg_parts[0]) - 1
                pct = float(arg_parts[1])
                item = cart.items[idx]
                result = cart.apply_item_discount(item.product_id, percent=pct)
                console.print(f"[green]{result['message']}[/green]" if result["success"]
                              else f"[red]{result['error']}[/red]")
            except (IndexError, ValueError):
                console.print("[red]Usage: disc <item#> <percent>[/red]")
            pause()

        elif action == "cartdisc":
            try:
                pct = float(arg)
                result = cart.apply_cart_discount(percent=pct)
                console.print(f"[green]{result['message']}[/green]" if result["success"]
                              else f"[red]{result['error']}[/red]")
            except ValueError:
                console.print("[red]Usage: cartdisc <percent>[/red]")
            pause()

        elif action == "customer":
            cust_list = customers.list_customers()
            if cust_list:
                show_table("Customers", [
                    ("ID", "dim"), ("Code", "cyan"), ("Name", "white"),
                    ("Points", "yellow"), ("Spent", "green"),
                ], [(c["id"], c["code"], c["name"], c["points"],
                     format_money(c["total_spent"], settings)) for c in cust_list],
                    show_index=True)
            cid = Prompt.ask("Customer ID (or 'new' to create, empty to skip)", default="")
            if cid == "new":
                fn = Prompt.ask("First name")
                ln = Prompt.ask("Last name")
                email = Prompt.ask("Email (optional)", default="")
                phone = Prompt.ask("Phone (optional)", default="")
                result = customers.create_customer(fn, ln, email or None, phone or None)
                if result["success"]:
                    console.print(f"[green]{result['message']}[/green]")
                    cust = customers.get_customer(customer_id=result["id"])
                    if cust:
                        cart.set_customer(cust["id"], cust["name"])
                else:
                    console.print(f"[red]{result['error']}[/red]")
            elif cid.isdigit():
                cust = customers.get_customer(customer_id=int(cid))
                if cust:
                    cart.set_customer(cust["id"], cust["name"])
                    console.print(f"[green]Customer set: {cust['name']} ({cust['points']} points)[/green]")
                else:
                    console.print("[red]Customer not found.[/red]")
            pause()

        elif action == "search":
            if not arg:
                arg = Prompt.ask("Search query")
            results = products.search_products(arg)
            if results:
                show_table("Search Results", [
                    ("ID", "dim"), ("SKU", "cyan"), ("Name", "white"),
                    ("Price", "green"), ("Stock", "yellow"),
                ], [(p["id"], p["sku"], p["name"],
                     format_money(p["price"], settings), p["stock"]) for p in results])
            else:
                console.print("[yellow]No products found.[/yellow]")
            pause()

        elif action == "pay":
            if cart.is_empty:
                console.print("[red]Cart is empty![/red]")
                pause()
                continue

            payment_screen(cart, sales, auth, settings)
            return

        elif action == "loyalty" and cart.customer_id:
            cust = customers.get_customer(customer_id=cart.customer_id)
            if cust and cust["points"] > 0:
                console.print(f"Available points: [yellow]{cust['points']}[/yellow] "
                              f"(Value: {format_money(cust['points_value'], settings)})")
                pts = IntPrompt.ask("Points to redeem (0 to skip)", default=0)
                if pts > 0:
                    result = customers.redeem_points(cart.customer_id, pts)
                    if result["success"]:
                        cart.set_loyalty_discount(result["discount_amount"])
                        console.print(f"[green]Redeemed {pts} points for "
                                      f"{format_money(result['discount_amount'], settings)} discount[/green]")
                    else:
                        console.print(f"[red]{result['error']}[/red]")
            else:
                console.print("[yellow]No loyalty points available.[/yellow]")
            pause()


def payment_screen(cart: Cart, sales: SalesManager, auth: AuthManager, settings: dict):
    symbol = settings.get("currency", {}).get("symbol", "$")
    total = cart.total

    console.print()
    console.print(Panel(f"[bold]PAYMENT - Total: {symbol}{total:.2f}[/bold]", style="green"))
    console.print("  [bold]1[/bold]. Cash")
    console.print("  [bold]2[/bold]. Card")
    console.print("  [bold]3[/bold]. Split (Cash + Card)")
    console.print("  [bold]0[/bold]. Back to cart")
    console.print()

    choice = IntPrompt.ask("Payment method")

    employee_id = auth.get_current_employee()["id"]

    if choice == 1:
        tendered = FloatPrompt.ask(f"Cash tendered ({symbol})")
        result = sales.complete_sale(
            cart, employee_id, "cash", cash_tendered=tendered
        )
    elif choice == 2:
        card = Prompt.ask("Last 4 digits of card", default="****")
        result = sales.complete_sale(
            cart, employee_id, "card", card_last_four=card
        )
    elif choice == 3:
        cash_amt = FloatPrompt.ask(f"Cash amount ({symbol})")
        card_amt = round(total - cash_amt, 2)
        console.print(f"Card amount: {symbol}{card_amt:.2f}")
        card = Prompt.ask("Last 4 digits of card", default="****")
        result = sales.complete_sale(
            cart, employee_id, "split",
            cash_amount=cash_amt, card_amount=card_amt, card_last_four=card
        )
    else:
        return

    if result["success"]:
        console.print()
        console.print(Panel("[bold green]SALE COMPLETE[/bold green]", style="green"))
        console.print(result["receipt"])
        if result.get("change", 0) > 0:
            from payment_processor import PaymentProcessor
            pp = PaymentProcessor(settings)
            breakdown = pp.calculate_change_breakdown(result["change"])
            if breakdown:
                console.print("[bold]Change breakdown:[/bold]")
                for d in breakdown:
                    console.print(f"  {d['denomination']} x {d['count']}")
        cart.clear()
    else:
        console.print(f"\n[bold red]Payment failed:[/bold red] {result['error']}")

    pause()


# ═══════════════════════════════════════════════════════════════════════════
#  PRODUCT MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════

def products_menu(pm: ProductManager, settings: dict):
    while True:
        choice = show_menu("Product Management", [
            ("View All Products", None),
            ("Search Products", None),
            ("Add New Product", None),
            ("Edit Product", None),
            ("View Categories", None),
            ("Add Category", None),
            ("Low Stock Products", None),
        ])

        if choice == 0:
            return
        elif choice == 1:
            prods = pm.list_products()
            show_table("All Products", [
                ("ID", "dim"), ("SKU", "cyan"), ("Name", "white"),
                ("Category", "blue"), ("Price", "green"),
                ("Cost", "dim"), ("Stock", "yellow"), ("Margin", "magenta"),
            ], [(p["id"], p["sku"], p["name"], p["category"],
                 format_money(p["price"], settings), format_money(p["cost"], settings),
                 p["stock"], f"{p['margin']}%") for p in prods])
            pause()
        elif choice == 2:
            q = Prompt.ask("Search query")
            results = pm.search_products(q)
            if results:
                show_table("Search Results", [
                    ("ID", "dim"), ("SKU", "cyan"), ("Name", "white"),
                    ("Price", "green"), ("Stock", "yellow"),
                ], [(p["id"], p["sku"], p["name"],
                     format_money(p["price"], settings), p["stock"]) for p in results])
            else:
                console.print("[yellow]No products found.[/yellow]")
            pause()
        elif choice == 3:
            name = Prompt.ask("Product name")
            price = FloatPrompt.ask("Price")
            cost = FloatPrompt.ask("Cost", default=0.0)
            stock = IntPrompt.ask("Initial stock", default=0)
            barcode = Prompt.ask("Barcode (optional)", default="")
            cats = pm.list_categories()
            if cats:
                show_table("Categories", [("ID", "dim"), ("Name", "cyan")],
                           [(c["id"], c["name"]) for c in cats])
            cat_id = IntPrompt.ask("Category ID (0 for none)", default=0)
            result = pm.create_product(
                name=name, price=price, cost=cost, stock=stock,
                barcode=barcode or None, category_id=cat_id or None
            )
            console.print(f"[green]{result['message']}[/green]" if result["success"]
                          else f"[red]{result['error']}[/red]")
            pause()
        elif choice == 4:
            pid = IntPrompt.ask("Product ID to edit")
            prod = pm.get_product(product_id=pid)
            if not prod:
                console.print("[red]Product not found.[/red]")
                pause()
                continue
            console.print(f"Editing: [bold]{prod['name']}[/bold] (SKU: {prod['sku']})")
            name = Prompt.ask("New name", default=prod["name"])
            price = FloatPrompt.ask("New price", default=prod["price"])
            cost = FloatPrompt.ask("New cost", default=prod["cost"])
            result = pm.update_product(pid, name=name, price=price, cost=cost)
            console.print(f"[green]{result['message']}[/green]" if result["success"]
                          else f"[red]{result['error']}[/red]")
            pause()
        elif choice == 5:
            cats = pm.list_categories()
            show_table("Categories", [
                ("ID", "dim"), ("Name", "cyan"), ("Description", "white"), ("Products", "yellow"),
            ], [(c["id"], c["name"], c["description"], c["product_count"]) for c in cats])
            pause()
        elif choice == 6:
            name = Prompt.ask("Category name")
            desc = Prompt.ask("Description", default="")
            result = pm.create_category(name, desc)
            console.print(f"[green]{result['message']}[/green]" if result["success"]
                          else f"[red]{result['error']}[/red]")
            pause()
        elif choice == 7:
            low = pm.get_low_stock_products()
            if low:
                show_table("Low Stock Alert", [
                    ("ID", "dim"), ("SKU", "cyan"), ("Name", "white"),
                    ("Stock", "red"), ("Min", "yellow"), ("Category", "blue"),
                ], [(p["id"], p["sku"], p["name"], p["stock"],
                     p["min_stock"], p["category"]) for p in low])
            else:
                console.print("[green]All products are well-stocked![/green]")
            pause()


# ═══════════════════════════════════════════════════════════════════════════
#  INVENTORY MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════

def inventory_menu(inv: InventoryManager, pm: ProductManager, settings: dict):
    while True:
        choice = show_menu("Inventory Management", [
            ("Inventory Summary", None),
            ("Restock Product", None),
            ("Adjust Stock", None),
            ("Low Stock Alerts", None),
            ("Stock History", None),
        ])

        if choice == 0:
            return
        elif choice == 1:
            summary = inv.get_inventory_summary()
            info = Table(title="Inventory Summary", box=box.ROUNDED, title_style="bold magenta")
            info.add_column("Metric", style="cyan")
            info.add_column("Value", style="bold white", justify="right")
            info.add_row("Total Products", str(summary["total_products"]))
            info.add_row("Total Items in Stock", str(summary["total_items"]))
            info.add_row("Total Cost Value", format_money(summary["total_cost_value"], settings))
            info.add_row("Total Retail Value", format_money(summary["total_retail_value"], settings))
            info.add_row("Potential Profit", format_money(summary["potential_profit"], settings))
            info.add_row("Low Stock Items", f"[red]{summary['low_stock_count']}[/red]")
            info.add_row("Out of Stock", f"[bold red]{summary['out_of_stock_count']}[/bold red]")
            console.print(info)
            pause()
        elif choice == 2:
            pid = IntPrompt.ask("Product ID")
            qty = IntPrompt.ask("Quantity to add")
            ref = Prompt.ask("Reference/PO number", default="")
            result = inv.restock(pid, qty, ref)
            if result["success"]:
                console.print(f"[green]Restocked {result['product']}: "
                              f"{result['before']} -> {result['after']}[/green]")
            else:
                console.print(f"[red]{result['error']}[/red]")
            pause()
        elif choice == 3:
            pid = IntPrompt.ask("Product ID")
            qty = IntPrompt.ask("Quantity change (negative to reduce)")
            notes = Prompt.ask("Notes", default="Manual adjustment")
            result = inv.adjust_stock(pid, qty, "adjustment", notes=notes)
            if result["success"]:
                console.print(f"[green]Adjusted {result['product']}: "
                              f"{result['before']} -> {result['after']}[/green]")
            else:
                console.print(f"[red]{result['error']}[/red]")
            pause()
        elif choice == 4:
            alerts = inv.get_low_stock_alerts()
            if alerts:
                show_table("Low Stock Alerts", [
                    ("ID", "dim"), ("SKU", "cyan"), ("Name", "white"),
                    ("Stock", "red"), ("Min", "yellow"), ("Deficit", "bold red"),
                    ("Category", "blue"),
                ], [(a["id"], a["sku"], a["name"], a["stock"],
                     a["min_stock"], a["deficit"], a["category"]) for a in alerts])
            else:
                console.print("[green]No low stock alerts![/green]")
            pause()
        elif choice == 5:
            pid = Prompt.ask("Product ID (empty for all)", default="")
            history = inv.get_stock_history(
                product_id=int(pid) if pid.isdigit() else None
            )
            if history:
                show_table("Stock History", [
                    ("Date", "dim"), ("Product", "white"), ("Type", "cyan"),
                    ("Change", "yellow"), ("Before", "dim"), ("After", "green"),
                    ("Notes", "dim"),
                ], [(h["date"], h["product"], h["type"], h["change"],
                     h["before"], h["after"], h["notes"]) for h in history])
            else:
                console.print("[yellow]No stock history found.[/yellow]")
            pause()


# ═══════════════════════════════════════════════════════════════════════════
#  CUSTOMER MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════

def customers_menu(cm: CustomerManager, settings: dict):
    while True:
        choice = show_menu("Customer Management", [
            ("View All Customers", None),
            ("Search Customer", None),
            ("Add New Customer", None),
            ("Customer Details", None),
            ("Top Customers", None),
            ("Purchase History", None),
        ])

        if choice == 0:
            return
        elif choice == 1:
            custs = cm.list_customers()
            show_table("All Customers", [
                ("ID", "dim"), ("Code", "cyan"), ("Name", "white"),
                ("Email", "blue"), ("Phone", "dim"),
                ("Points", "yellow"), ("Spent", "green"), ("Visits", "magenta"),
            ], [(c["id"], c["code"], c["name"], c["email"], c["phone"],
                 c["points"], format_money(c["total_spent"], settings),
                 c["visits"]) for c in custs])
            pause()
        elif choice == 2:
            q = Prompt.ask("Search (name, email, phone, code)")
            results = cm.list_customers(search=q)
            if results:
                show_table("Search Results", [
                    ("ID", "dim"), ("Code", "cyan"), ("Name", "white"),
                    ("Points", "yellow"), ("Spent", "green"),
                ], [(c["id"], c["code"], c["name"], c["points"],
                     format_money(c["total_spent"], settings)) for c in results])
            else:
                console.print("[yellow]No customers found.[/yellow]")
            pause()
        elif choice == 3:
            fn = Prompt.ask("First name")
            ln = Prompt.ask("Last name")
            email = Prompt.ask("Email (optional)", default="")
            phone = Prompt.ask("Phone (optional)", default="")
            result = cm.create_customer(fn, ln, email or None, phone or None)
            console.print(f"[green]{result['message']}[/green]" if result["success"]
                          else f"[red]{result['error']}[/red]")
            pause()
        elif choice == 4:
            cid = IntPrompt.ask("Customer ID")
            cust = cm.get_customer(customer_id=cid)
            if cust:
                info = Table(title=f"Customer: {cust['name']}", box=box.ROUNDED)
                info.add_column("Field", style="cyan")
                info.add_column("Value", style="white")
                info.add_row("Code", cust["code"])
                info.add_row("Email", cust["email"])
                info.add_row("Phone", cust["phone"])
                info.add_row("Address", cust["address"])
                info.add_row("Loyalty Points", str(cust["points"]))
                info.add_row("Points Value", format_money(cust["points_value"], settings))
                info.add_row("Total Spent", format_money(cust["total_spent"], settings))
                info.add_row("Visits", str(cust["visits"]))
                console.print(info)
            else:
                console.print("[red]Customer not found.[/red]")
            pause()
        elif choice == 5:
            top = cm.get_top_customers()
            show_table("Top Customers", [
                ("Rank", "dim"), ("Name", "white"), ("Spent", "green"),
                ("Points", "yellow"), ("Visits", "magenta"),
            ], [(i + 1, c["name"], format_money(c["total_spent"], settings),
                 c["points"], c["visits"]) for i, c in enumerate(top)])
            pause()
        elif choice == 6:
            cid = IntPrompt.ask("Customer ID")
            history = cm.get_purchase_history(cid)
            if history:
                show_table("Purchase History", [
                    ("TXN ID", "cyan"), ("Date", "dim"), ("Items", "yellow"),
                    ("Total", "green"), ("Payment", "blue"), ("Status", "white"),
                ], [(h["transaction_id"], h["date"], h["items"],
                     format_money(h["total"], settings), h["payment"],
                     h["status"]) for h in history])
            else:
                console.print("[yellow]No purchase history.[/yellow]")
            pause()


# ═══════════════════════════════════════════════════════════════════════════
#  SALES HISTORY & RETURNS
# ═══════════════════════════════════════════════════════════════════════════

def sales_menu(sm: SalesManager, auth: AuthManager, settings: dict):
    while True:
        choice = show_menu("Sales & Returns", [
            ("Recent Sales", None),
            ("Lookup Transaction", None),
            ("Process Return", None),
            ("Void Sale", None),
        ])

        if choice == 0:
            return
        elif choice == 1:
            sales = sm.get_recent_sales()
            show_table("Recent Sales", [
                ("TXN ID", "cyan"), ("Date", "dim"), ("Items", "yellow"),
                ("Total", "green"), ("Payment", "blue"), ("Status", "white"),
            ], [(s["transaction_id"], s["date"], s["items"],
                 format_money(s["total"], settings), s["payment"],
                 s["status"]) for s in sales])
            pause()
        elif choice == 2:
            txn = Prompt.ask("Transaction ID")
            sale = sm.get_sale(txn)
            if sale:
                info = Table(title=f"Transaction: {sale['transaction_id']}", box=box.ROUNDED)
                info.add_column("Field", style="cyan")
                info.add_column("Value", style="white")
                info.add_row("Date", sale["date"])
                info.add_row("Subtotal", format_money(sale["subtotal"], settings))
                info.add_row("Tax", format_money(sale["tax"], settings))
                info.add_row("Discount", format_money(sale["discount"], settings))
                info.add_row("Total", format_money(sale["total"], settings))
                info.add_row("Payment", sale["payment_method"])
                info.add_row("Status", sale["status"])
                console.print(info)

                items_table = Table(title="Items", box=box.SIMPLE)
                items_table.add_column("Product", style="white")
                items_table.add_column("Qty", style="yellow")
                items_table.add_column("Price", style="cyan")
                items_table.add_column("Total", style="green")
                for item in sale["items"]:
                    items_table.add_row(
                        item["product"], str(item["quantity"]),
                        format_money(item["price"], settings),
                        format_money(item["total"], settings)
                    )
                console.print(items_table)
            else:
                console.print("[red]Transaction not found.[/red]")
            pause()
        elif choice == 3:
            if not auth.is_manager_or_above():
                console.print("[red]Manager or Admin access required for returns.[/red]")
                pause()
                continue
            txn = Prompt.ask("Original Transaction ID")
            pid = IntPrompt.ask("Product ID to return")
            qty = IntPrompt.ask("Quantity to return")
            reason = Prompt.ask("Reason for return")
            restock = Confirm.ask("Restock item?", default=True)
            result = sm.process_return(
                txn, pid, qty, reason,
                auth.get_current_employee()["id"], restock
            )
            if result["success"]:
                console.print(f"\n[green]Return processed. Refund: "
                              f"{format_money(result['refund_amount'], settings)}[/green]")
                console.print(result["receipt"])
            else:
                console.print(f"[red]{result['error']}[/red]")
            pause()
        elif choice == 4:
            if not auth.is_manager_or_above():
                console.print("[red]Manager or Admin access required to void sales.[/red]")
                pause()
                continue
            txn = Prompt.ask("Transaction ID to void")
            if Confirm.ask(f"Are you sure you want to void {txn}?", default=False):
                result = sm.void_sale(txn, auth.get_current_employee()["id"])
                if result["success"]:
                    console.print(f"[green]{result['message']}[/green]")
                else:
                    console.print(f"[red]{result['error']}[/red]")
            pause()


# ═══════════════════════════════════════════════════════════════════════════
#  REPORTS
# ═══════════════════════════════════════════════════════════════════════════

def reports_menu(rm: ReportManager, settings: dict):
    while True:
        choice = show_menu("Reports & Analytics", [
            ("Today's Summary", None),
            ("Sales Summary (Custom Period)", None),
            ("Top Selling Products", None),
            ("Revenue by Category", None),
            ("Daily Revenue (14 days)", None),
            ("Payment Method Breakdown", None),
            ("Profit Report", None),
            ("Export Sales to CSV", None),
            ("Export Inventory to CSV", None),
        ])

        if choice == 0:
            return
        elif choice == 1:
            summary = rm.sales_summary("today")
            _show_summary(summary, settings)
            pause()
        elif choice == 2:
            console.print("Periods: today, yesterday, week, month, year, last7, last30")
            period = Prompt.ask("Period", default="last7")
            summary = rm.sales_summary(period)
            _show_summary(summary, settings)
            pause()
        elif choice == 3:
            period = Prompt.ask("Period (last7, last30, month, year)", default="last30")
            top = rm.top_products(period)
            show_table("Top Selling Products", [
                ("Rank", "dim"), ("Name", "white"), ("Qty Sold", "yellow"),
                ("Revenue", "green"),
            ], [(p["rank"], p["name"], p["quantity_sold"],
                 format_money(p["revenue"], settings)) for p in top])
            pause()
        elif choice == 4:
            cats = rm.revenue_by_category()
            show_table("Revenue by Category", [
                ("Category", "cyan"), ("Revenue", "green"),
                ("Items Sold", "yellow"), ("% of Total", "magenta"),
            ], [(c["category"], format_money(c["revenue"], settings),
                 c["items_sold"], f"{c['percentage']}%") for c in cats])
            pause()
        elif choice == 5:
            daily = rm.daily_revenue()
            show_table("Daily Revenue (14 Days)", [
                ("Date", "dim"), ("Revenue", "green"),
                ("Transactions", "yellow"), ("Items", "cyan"),
            ], [(d["date"], format_money(d["revenue"], settings),
                 d["transactions"], d["items_sold"]) for d in daily])

            # Simple bar chart
            max_rev = max((d["revenue"] for d in daily), default=1)
            if max_rev > 0:
                console.print("\n[bold]Revenue Chart:[/bold]")
                for d in daily:
                    bar_len = int((d["revenue"] / max_rev) * 40) if max_rev > 0 else 0
                    bar = "█" * bar_len
                    console.print(f"  {d['date'][-5:]} │[green]{bar}[/green] "
                                  f"{format_money(d['revenue'], settings)}")
            pause()
        elif choice == 6:
            breakdown = rm.payment_method_breakdown()
            show_table("Payment Method Breakdown", [
                ("Method", "cyan"), ("Transactions", "yellow"),
                ("Total", "green"), ("% of Revenue", "magenta"),
            ], [(p["method"], p["transactions"],
                 format_money(p["total"], settings),
                 f"{p['percentage']}%") for p in breakdown])
            pause()
        elif choice == 7:
            period = Prompt.ask("Period", default="last30")
            profit = rm.profit_report(period)
            info = Table(title="Profit Report", box=box.ROUNDED, title_style="bold magenta")
            info.add_column("Metric", style="cyan")
            info.add_column("Value", style="bold white", justify="right")
            info.add_row("Period", profit["period"])
            info.add_row("Total Revenue", format_money(profit["total_revenue"], settings))
            info.add_row("Total Cost", format_money(profit["total_cost"], settings))
            info.add_row("Gross Profit", f"[green]{format_money(profit['gross_profit'], settings)}[/green]")
            info.add_row("Profit Margin", f"[green]{profit['profit_margin']}%[/green]")
            info.add_row("Transactions", str(profit["total_transactions"]))
            console.print(info)
            pause()
        elif choice == 8:
            period = Prompt.ask("Period", default="last30")
            path = rm.export_sales_csv(period)
            console.print(f"[green]Sales exported to: {path}[/green]")
            pause()
        elif choice == 9:
            path = rm.export_inventory_csv()
            console.print(f"[green]Inventory exported to: {path}[/green]")
            pause()


def _show_summary(summary: dict, settings: dict):
    info = Table(title=f"Sales Summary ({summary['period']})",
                 box=box.ROUNDED, title_style="bold magenta")
    info.add_column("Metric", style="cyan")
    info.add_column("Value", style="bold white", justify="right")
    info.add_row("Period", f"{summary['start']} to {summary['end']}")
    info.add_row("Total Sales", str(summary["total_sales"]))
    info.add_row("Total Revenue", format_money(summary["total_revenue"], settings))
    info.add_row("Total Tax", format_money(summary["total_tax"], settings))
    info.add_row("Total Discounts", format_money(summary["total_discounts"], settings))
    info.add_row("Average Sale", format_money(summary["average_sale"], settings))
    info.add_row("Total Items Sold", str(summary["total_items"]))
    info.add_row("Cash Sales", str(summary["cash_sales"]))
    info.add_row("Card Sales", str(summary["card_sales"]))
    console.print(info)


# ═══════════════════════════════════════════════════════════════════════════
#  EMPLOYEE MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════

def employee_menu(auth: AuthManager, settings: dict):
    while True:
        choice = show_menu("Employee Management", [
            ("View Employees", None),
            ("Add Employee", None),
            ("Unlock Account", None),
            ("Change PIN", None),
        ])

        if choice == 0:
            return
        elif choice == 1:
            emps = auth.list_employees()
            show_table("Employees", [
                ("ID", "dim"), ("Emp ID", "cyan"), ("Name", "white"),
                ("Role", "yellow"), ("Email", "blue"), ("Last Login", "dim"),
            ], [(e["id"], e["employee_id"], e["name"], e["role"],
                 e["email"] or "", e["last_login"]) for e in emps])
            pause()
        elif choice == 2:
            if not auth.is_admin():
                console.print("[red]Admin access required.[/red]")
                pause()
                continue
            fn = Prompt.ask("First name")
            ln = Prompt.ask("Last name")
            pin = Prompt.ask("PIN (min 4 digits)", password=True)
            role = Prompt.ask("Role (admin/manager/cashier)", default="cashier")
            email = Prompt.ask("Email (optional)", default="")
            result = auth.create_employee(fn, ln, pin, role, email or None)
            console.print(f"[green]{result['message']}[/green]" if result["success"]
                          else f"[red]{result['error']}[/red]")
            pause()
        elif choice == 3:
            if not auth.is_admin():
                console.print("[red]Admin access required.[/red]")
                pause()
                continue
            eid = Prompt.ask("Employee ID to unlock")
            result = auth.unlock_employee(eid)
            console.print(f"[green]{result['message']}[/green]" if result["success"]
                          else f"[red]{result['error']}[/red]")
            pause()
        elif choice == 4:
            eid = Prompt.ask("Employee ID")
            old_pin = Prompt.ask("Current PIN", password=True)
            new_pin = Prompt.ask("New PIN", password=True)
            result = auth.change_pin(eid, old_pin, new_pin)
            console.print(f"[green]{result['message']}[/green]" if result["success"]
                          else f"[red]{result['error']}[/red]")
            pause()


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN APPLICATION LOOP
# ═══════════════════════════════════════════════════════════════════════════

def main():
    settings = load_settings()

    # Initialize database
    console.print("[dim]Initializing database...[/dim]")
    init_db(settings)

    session = get_session()
    seeded = seed_database(session)
    session.close()
    if seeded:
        console.print("[green]Database seeded with demo data.[/green]")

    auth = AuthManager(settings)
    pm = ProductManager()
    inv = InventoryManager(settings)
    cm = CustomerManager(settings)
    sm = SalesManager(settings)
    rm = ReportManager(settings)
    cart = Cart(settings)

    # Login
    clear_screen()
    show_banner(settings)

    while True:
        if not auth.is_logged_in():
            if not login_screen(auth):
                if not Confirm.ask("Try again?", default=True):
                    console.print("[bold]Goodbye![/bold]")
                    return
                continue

        emp = auth.get_current_employee()
        role = emp["role"]

        # Build menu based on role
        menu_items = [
            ("New Sale", lambda: new_sale_screen(cart, sm, cm, pm, auth, settings)),
            ("Products", lambda: products_menu(pm, settings)),
            ("Inventory", lambda: inventory_menu(inv, pm, settings)),
            ("Customers", lambda: customers_menu(cm, settings)),
            ("Sales & Returns", lambda: sales_menu(sm, auth, settings)),
            ("Reports & Analytics", lambda: reports_menu(rm, settings)),
        ]

        if role in (EmployeeRole.ADMIN, EmployeeRole.MANAGER):
            menu_items.append(("Employee Management", lambda: employee_menu(auth, settings)))

        menu_items.append(("Logout", None))

        # Show alerts
        alerts = inv.get_low_stock_alerts()
        if alerts:
            console.print(f"\n[bold red]⚠ {len(alerts)} product(s) with low stock![/bold red]")

        console.print(f"\n[dim]Logged in as: {emp['name']} ({emp['role'].value})[/dim]")

        choice = show_menu("Main Menu", menu_items, back_label="Exit")

        if choice == 0:
            if Confirm.ask("Exit ElectroPOS?", default=False):
                console.print("[bold cyan]Thank you for using ElectroPOS. Goodbye![/bold cyan]")
                return
        elif choice == len(menu_items):
            name = auth.logout()
            console.print(f"[yellow]Logged out: {name}[/yellow]")
            clear_screen()
            show_banner(settings)
        else:
            _, handler = menu_items[choice - 1]
            if handler:
                handler()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[bold cyan]ElectroPOS terminated. Goodbye![/bold cyan]")
