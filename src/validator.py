import json
import os
from typing import List, Tuple

class CommandValidator:
    """Validates commands against whitelist and blacklist."""

    def __init__(self, whitelist_path: str = "config/command_whitelist.json",
                 blacklist_path: str = "config/command_blacklist.json"):
        """
        Initialize the validator.

        Args:
            whitelist_path: Path to whitelist JSON file
            blacklist_path: Path to blacklist JSON file
        """
        self.whitelist_path = whitelist_path
        self.blacklist_path = blacklist_path
        self.whitelist = self._load_list(whitelist_path)
        self.blacklist = self._load_list(blacklist_path)

    def _load_list(self, path: str) -> List[str]:
        """
        Load a JSON list from file.

        Args:
            path: Path to JSON file

        Returns:
            List of strings
        """
        try:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load {path}: {e}")
        return []

    def validate(self, command: str) -> Tuple[bool, str]:
        """
        Validate a command against whitelist and blacklist.

        Args:
            command: Command to validate

        Returns:
            Tuple of (is_valid, reason)
        """
        # Check blacklist first
        for forbidden in self.blacklist:
            if forbidden in command:
                return False, f"BLOCKED: Command contains forbidden pattern '{forbidden}'"

        # Extract executable (first word)
        parts = command.split()
        if not parts:
            return False, "Empty command"

        executable = parts[0]

        # Check whitelist
        if self.whitelist and executable not in self.whitelist:
            return False, f"BLOCKED: Command '{executable}' not in whitelist. Allowed: {', '.join(self.whitelist)}"

        return True, "Command validated successfully"

    def add_to_whitelist(self, command: str) -> bool:
        """
        Add a command to the whitelist.

        Args:
            command: Command to add

        Returns:
            True if successful
        """
        if command not in self.whitelist:
            self.whitelist.append(command)
            return self._save_list(self.whitelist_path, self.whitelist)
        return True

    def add_to_blacklist(self, pattern: str) -> bool:
        """
        Add a pattern to the blacklist.

        Args:
            pattern: Pattern to add

        Returns:
            True if successful
        """
        if pattern not in self.blacklist:
            self.blacklist.append(pattern)
            return self._save_list(self.blacklist_path, self.blacklist)
        return True

    def _save_list(self, path: str, data: List[str]) -> bool:
        """
        Save a list to JSON file.

        Args:
            path: Path to save to
            data: List to save

        Returns:
            True if successful
        """
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving {path}: {e}")
            return False

    def get_whitelist(self) -> List[str]:
        """Get the current whitelist."""
        return self.whitelist.copy()

    def get_blacklist(self) -> List[str]:
        """Get the current blacklist."""
        return self.blacklist.copy()
