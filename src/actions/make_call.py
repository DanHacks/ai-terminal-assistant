"""
Make Call action — initiate phone calls to contacts.
"""

from datetime import datetime
from actions.base import BaseAction


class MakeCallAction(BaseAction):

    def describe(self):
        return "Make a phone call to a contact"

    def examples(self):
        return [
            "call Mom",
            "phone John",
            "dial 555-1234",
            "ring Sarah",
            "make a call to Dave",
        ]

    def get_required_fields(self):
        return [
            ("recipient", "Who do you want to call?"),
        ]

    def execute(self, details):
        recipient = details.get("recipient", "Unknown")

        summary = f"Call {recipient}"
        if not self.confirm(summary):
            return False, "Call cancelled."

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        result = (
            f"📞 Calling {recipient}...\n"
            f"   Status: Ringing...\n"
            f"   Time: {timestamp}\n"
            f"   Call connected ✓\n"
            f"   (Simulated — integrate with Twilio or phone API for real calls)"
        )
        return True, result
