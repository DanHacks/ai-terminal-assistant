"""
ElectroPOS - Logger
Application logging for POS operations.
"""

import os
import logging
from datetime import datetime


def setup_logger(name: str = "electropos", log_dir: str = None) -> logging.Logger:
    if log_dir is None:
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        # File handler
        log_file = os.path.join(log_dir, "pos_operations.log")
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        ))
        logger.addHandler(fh)

        # Console handler (errors only)
        ch = logging.StreamHandler()
        ch.setLevel(logging.ERROR)
        ch.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        logger.addHandler(ch)

    return logger


def log_sale(transaction_id: str, total: float, payment_method: str, employee: str):
    logger = setup_logger("pos.sales")
    logger.info(f"SALE | TXN:{transaction_id} | Total:{total:.2f} | "
                f"Payment:{payment_method} | Employee:{employee}")


def log_return(return_id: str, refund: float, reason: str, employee: str):
    logger = setup_logger("pos.returns")
    logger.info(f"RETURN | ID:{return_id} | Refund:{refund:.2f} | "
                f"Reason:{reason} | Employee:{employee}")


def log_inventory(product: str, change: int, change_type: str):
    logger = setup_logger("pos.inventory")
    logger.info(f"INVENTORY | Product:{product} | Change:{change} | Type:{change_type}")


def log_auth(employee: str, action: str, success: bool):
    logger = setup_logger("pos.auth")
    level = logging.INFO if success else logging.WARNING
    logger.log(level, f"AUTH | Employee:{employee} | Action:{action} | Success:{success}")
