"""
Send Message action — send SMS or text messages to contacts.
"""

from datetime import datetime
from actions.base import BaseAction


class SendMessageAction(BaseAction):

    def describe(self):
        return "Send a text message or SMS to a contact"

    def examples(self):
        return [
            "send a message to John",
            "text Mom saying I'll be late",
            "message Sarah that the meeting is at 3pm",
            "send sms to Dave",
        ]

    def get_required_fields(self):
        return [
            ("recipient", "Who should I send the message to?"),
            ("message", "What should the message say?"),
        ]

    def execute(self, details):
        recipient = details.get("recipient", "Unknown")
        message = details.get("message", "")

        summary = f"Send message to {recipient}: \"{message}\""
        if not self.confirm(summary):
            return False, "Message cancelled."

        # Simulated message sending
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        result = (
            f"📨 Message sent successfully!\n"
            f"   To: {recipient}\n"
            f"   Message: {message}\n"
            f"   Time: {timestamp}\n"
            f"   Status: Delivered ✓"
        )
        return True, result
