"""
ElectroPOS - Command Parser
Parses POS terminal commands for the sale screen.
"""


def parse_pos_command(raw_input: str) -> dict:
    """Parse a POS command string into action and arguments."""
    raw_input = raw_input.strip()
    if not raw_input:
        return {"action": None, "args": []}

    parts = raw_input.split(maxsplit=1)
    action = parts[0].lower()
    arg_str = parts[1] if len(parts) > 1 else ""

    command_map = {
        "add": "add_item",
        "a": "add_item",
        "scan": "add_item",
        "del": "remove_item",
        "rm": "remove_item",
        "remove": "remove_item",
        "qty": "update_quantity",
        "quantity": "update_quantity",
        "disc": "item_discount",
        "discount": "item_discount",
        "cartdisc": "cart_discount",
        "cd": "cart_discount",
        "pay": "payment",
        "checkout": "payment",
        "customer": "set_customer",
        "cust": "set_customer",
        "loyalty": "loyalty",
        "search": "search",
        "find": "search",
        "clear": "clear_cart",
        "void": "void_cart",
        "cancel": "cancel",
        "help": "help",
        "h": "help",
    }

    mapped_action = command_map.get(action, action)
    args = arg_str.split() if arg_str else []

    return {
        "action": mapped_action,
        "args": args,
        "raw": raw_input,
    }


def get_help_text() -> str:
    return """
POS Commands:
  add <sku/barcode/id> [qty]  - Add item to cart
  qty <item#> <quantity>      - Update item quantity
  del <item#>                 - Remove item from cart
  disc <item#> <percent>      - Apply item discount
  cartdisc <percent>          - Apply cart-wide discount
  customer                    - Attach customer to sale
  loyalty                     - Redeem loyalty points
  search <query>              - Search products
  pay                         - Proceed to payment
  clear                       - Clear cart
  cancel                      - Cancel and return to menu
  help                        - Show this help
"""
