import re
from typing import Dict, Any, List

class CommandParser:
    """Parses and structures commands from AI assistant output."""

    def __init__(self):
        """Initialize the command parser."""
        self.command_patterns = {
            'shell': r'^[\w\-]+(\s+[\w\-\.\/]+)*$',  # Basic shell command pattern
        }

    def parse(self, ai_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse AI output into a structured command.

        Args:
            ai_output: Output from AI assistant

        Returns:
            Structured command dictionary
        """
        if ai_output.get("type") == "error":
            return ai_output

        command_type = ai_output.get("type", "conversation")
        action = ai_output.get("action", "")
        parameters = ai_output.get("parameters", {})

        return {
            "type": command_type,
            "action": action,
            "parameters": parameters,
            "raw": ai_output,
            "requires_confirmation": self._requires_confirmation(command_type, action),
            "risk_level": self._assess_risk(command_type, action)
        }

    def _requires_confirmation(self, command_type: str, action: str) -> bool:
        """
        Determine if a command requires user confirmation.

        Args:
            command_type: Type of command
            action: The action to perform

        Returns:
            True if confirmation is required
        """
        # All commands require confirmation by default for safety
        if command_type == "conversation":
            return False

        # Interactive actions need confirmation
        if command_type in ["message", "call", "order"]:
            return True

        # Shell commands need confirmation
        if command_type == "command":
            return True

        return True

    def _assess_risk(self, command_type: str, action: str) -> str:
        """
        Assess the risk level of a command.

        Args:
            command_type: Type of command
            action: The action to perform

        Returns:
            Risk level: "low", "medium", "high"
        """
        if command_type == "conversation":
            return "low"

        dangerous_patterns = [
            r'\brm\b.*-rf',
            r'\bdd\b',
            r'\bmkfs\b',
            r'\bformat\b',
            r'\bshutdown\b',
            r'\breboot\b',
            r':.*\|.*&',  # Fork bomb pattern
        ]

        action_lower = action.lower() if action else ""

        for pattern in dangerous_patterns:
            if re.search(pattern, action_lower):
                return "high"

        # Commands that modify system
        if command_type == "command" and any(cmd in action_lower for cmd in ['chmod', 'chown', 'sudo', 'su']):
            return "high"

        # Interactive actions with financial implications
        if command_type == "order":
            return "high"

        # Messages and calls are medium risk
        if command_type in ["message", "call"]:
            return "medium"

        # Default to medium for unknown commands
        return "medium"

    def extract_command_parts(self, command: str) -> Dict[str, Any]:
        """
        Extract parts of a shell command.

        Args:
            command: Shell command string

        Returns:
            Dictionary with command parts
        """
        parts = command.split()
        if not parts:
            return {"executable": "", "args": [], "full_command": command}

        return {
            "executable": parts[0],
            "args": parts[1:] if len(parts) > 1 else [],
            "full_command": command
        }

    def is_safe_command(self, command: str, whitelist: List[str], blacklist: List[str]) -> tuple[bool, str]:
        """
        Check if a command is safe based on whitelist and blacklist.

        Args:
            command: Command to check
            whitelist: List of allowed commands
            blacklist: List of forbidden commands/patterns

        Returns:
            Tuple of (is_safe, reason)
        """
        parts = self.extract_command_parts(command)
        executable = parts["executable"]

        # Check blacklist first
        for forbidden in blacklist:
            if forbidden in command:
                return False, f"Command contains forbidden pattern: {forbidden}"

        # Check whitelist
        if whitelist and executable not in whitelist:
            return False, f"Command '{executable}' not in whitelist"

        return True, "Command passed validation"
