"""
Command Executor module for AI Terminal Assistant.
Safely executes validated terminal commands with output capture.
"""

import subprocess
import shlex
from logger import log_command
from validator import validate_command


def execute_command(command, timeout=30):
    """
    Execute a terminal command safely.
    Returns (success, output, error).
    """
    is_safe, reason = validate_command(command)

    if not is_safe:
        log_command(command, approved=False, output=reason)
        return False, "", reason

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=None,
        )

        output = result.stdout.strip()
        error = result.stderr.strip()
        success = result.returncode == 0

        log_command(command, approved=True, output=output if success else error)

        return success, output, error

    except subprocess.TimeoutExpired:
        log_command(command, approved=True, output="TIMEOUT")
        return False, "", f"Command timed out after {timeout} seconds"

    except Exception as e:
        log_command(command, approved=True, output=str(e))
        return False, "", str(e)


def execute_with_confirmation(command, auto_confirm=False):
    """
    Execute a command with user confirmation.
    Returns (executed, success, output, error).
    """
    is_safe, reason = validate_command(command)

    if not is_safe:
        return False, False, "", f"⛔ Blocked: {reason}"

    if not auto_confirm:
        print(f"\n📋 Command to execute: {command}")
        print(f"   Safety: {reason}")
        try:
            confirm = input("   Execute? [y/N]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            confirm = "n"

        if confirm not in ("y", "yes"):
            log_command(command, approved=False, output="User declined")
            return False, False, "", "Command cancelled by user"

    success, output, error = execute_command(command)
    return True, success, output, error
