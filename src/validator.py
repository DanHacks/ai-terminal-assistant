"""
Validator module for AI Terminal Assistant.
Checks commands against blacklist and whitelist for safety.
"""

import json
import os

CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config")


def load_blacklist():
    """Load the command blacklist from config."""
    path = os.path.join(CONFIG_DIR, "command_blacklist.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def load_whitelist():
    """Load the command whitelist from config."""
    path = os.path.join(CONFIG_DIR, "command_whitelist.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def is_blacklisted(command, blacklist=None):
    """Check if a command matches any blacklisted pattern."""
    if blacklist is None:
        blacklist = load_blacklist()
    cmd_lower = command.strip().lower()
    for blocked in blacklist:
        if blocked.lower() in cmd_lower:
            return True
    return False


def is_whitelisted(command, whitelist=None):
    """Check if a command's base program is in the whitelist."""
    if whitelist is None:
        whitelist = load_whitelist()
    base_cmd = command.strip().split()[0].lower() if command.strip() else ""
    return base_cmd in [w.lower() for w in whitelist]


def validate_command(command):
    """
    Validate a command against safety rules.
    Returns (is_safe, reason).
    """
    if not command or not command.strip():
        return False, "Empty command"

    if is_blacklisted(command):
        return False, f"Command blocked: matches blacklisted pattern"

    if is_whitelisted(command):
        return True, "Command is whitelisted"

    return True, "Command not in blacklist (proceed with caution)"
