"""
Base action class for all interactive actions.
"""

from abc import ABC, abstractmethod


class BaseAction(ABC):
    """Base class for all assistant actions."""

    @abstractmethod
    def describe(self):
        """Return a short description of what this action does."""
        pass

    @abstractmethod
    def examples(self):
        """Return example phrases that trigger this action."""
        pass

    @abstractmethod
    def get_required_fields(self):
        """Return a list of (field_name, prompt_text) for required info."""
        pass

    @abstractmethod
    def execute(self, details):
        """
        Execute the action with the given details.
        Returns (success, result_message).
        """
        pass

    def collect_missing_info(self, details):
        """
        Interactively collect any missing required fields from the user.
        Returns the updated details dict.
        """
        for field, prompt_text in self.get_required_fields():
            if field not in details or not details[field]:
                try:
                    value = input(f"   {prompt_text}: ").strip()
                except (EOFError, KeyboardInterrupt):
                    value = ""
                if value:
                    details[field] = value
                else:
                    return None  # User cancelled
        return details

    def confirm(self, summary):
        """Ask user to confirm the action."""
        print(f"\n✅ Ready: {summary}")
        try:
            response = input("   Proceed? [Y/n]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            response = "n"
        return response in ("", "y", "yes")
