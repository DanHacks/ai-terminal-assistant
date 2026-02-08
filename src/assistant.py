"""
Assistant module — the main orchestrator for AI Terminal Assistant.
Ties together parsing, action resolution, confirmation, execution, and logging.
"""

import sys
import os

# Ensure src is on the path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from command_parser import detect_intent, parse_natural_language
from command_executor import execute_with_confirmation
from actions import get_action, list_actions
from logger import log_action, log_command, log_event


class Assistant:
    """Main assistant that processes user input and routes to actions or commands."""

    def __init__(self, confirm_commands=True):
        self.confirm_commands = confirm_commands
        log_event("assistant_start", "Assistant initialized")

    def process(self, user_input):
        """
        Process user input and route to the appropriate handler.
        Returns a response string.
        """
        text = user_input.strip()

        if not text:
            return ""

        # Handle special prefixes
        if text.startswith("!") or text.startswith("/cmd "):
            # Direct terminal command
            command = text.lstrip("!").lstrip("/cmd ").strip()
            return self._handle_command(command)

        if text.lower() in ("help", "/help"):
            return self._show_help()

        if text.lower() in ("actions", "/actions"):
            return self._show_actions()

        if text.lower() in ("history", "/history"):
            return self._show_history()

        # Try to detect an interactive action intent
        intent_result = detect_intent(text)
        if intent_result:
            intent_name, confidence, details = intent_result
            return self._handle_action(intent_name, details)

        # Try to parse as a natural language command
        command = parse_natural_language(text)
        if command:
            return self._handle_command(command)

        # No match — offer help
        return (
            "🤔 I'm not sure what you mean. Here's what I can do:\n"
            "   • Send messages, make calls, send emails\n"
            "   • Place orders, set reminders\n"
            "   • Search the web, check weather\n"
            "   • Open apps, run terminal commands\n"
            "   Type 'help' for full details or '!<command>' for terminal commands."
        )

    def _handle_action(self, intent_name, details):
        """Handle an interactive action."""
        action = get_action(intent_name)
        if not action:
            return f"❌ Action '{intent_name}' not found."

        print(f"\n🎯 Detected: {action.describe()}")

        # Collect any missing required information
        details = action.collect_missing_info(details)
        if details is None:
            log_action(intent_name, "User cancelled info collection", success=False)
            return "❌ Action cancelled."

        # Execute the action
        success, result = action.execute(details)
        log_action(intent_name, result.split("\n")[0] if result else "", success=success)

        return result

    def _handle_command(self, command):
        """Handle a terminal command with validation and confirmation."""
        executed, success, output, error = execute_with_confirmation(
            command, auto_confirm=not self.confirm_commands
        )

        if not executed:
            return error

        if success:
            return f"✅ Output:\n{output}" if output else "✅ Command executed successfully."
        else:
            return f"❌ Error:\n{error}" if error else "❌ Command failed."

    def _show_help(self):
        """Show help information."""
        actions_list = list_actions()
        lines = [
            "╔══════════════════════════════════════════════╗",
            "║        AI Terminal Assistant — Help          ║",
            "╚══════════════════════════════════════════════╝",
            "",
            "🗣️  INTERACTIVE ACTIONS (just type naturally):",
            "",
        ]

        for action_info in actions_list:
            desc = action_info["description"]
            examples = action_info["examples"][:2]
            lines.append(f"  • {desc}")
            for ex in examples:
                lines.append(f"    → \"{ex}\"")
            lines.append("")

        lines.extend([
            "⌨️  TERMINAL COMMANDS:",
            "  • Type natural language: \"list files\", \"show disk usage\"",
            "  • Direct command: !ls -la  or  /cmd ls -la",
            "",
            "📋 OTHER COMMANDS:",
            "  • help      — Show this help",
            "  • actions   — List all available actions",
            "  • history   — Show recent command history",
            "  • exit/quit — Exit the assistant",
            "",
        ])

        return "\n".join(lines)

    def _show_actions(self):
        """List all available actions."""
        actions_list = list_actions()
        lines = ["📋 Available Actions:\n"]
        for i, action_info in enumerate(actions_list, 1):
            lines.append(f"  {i}. {action_info['description']}")
            for ex in action_info["examples"][:2]:
                lines.append(f"     → \"{ex}\"")
        return "\n".join(lines)

    def _show_history(self):
        """Show recent command history from the log file."""
        log_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "logs", "command_history.log",
        )
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
            if not lines:
                return "📜 No history yet."
            recent = lines[-15:]  # Last 15 entries
            return "📜 Recent History:\n" + "".join(recent)
        except FileNotFoundError:
            return "📜 No history yet."
