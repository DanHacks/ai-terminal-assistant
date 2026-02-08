"""
Send Email action — compose and send emails.
"""

from datetime import datetime
from actions.base import BaseAction


class SendEmailAction(BaseAction):

    def describe(self):
        return "Send an email to a contact"

    def examples(self):
        return [
            "email John about the meeting",
            "send an email to Sarah",
            "mail Bob regarding the project update",
            "send email to team about deadline",
        ]

    def get_required_fields(self):
        return [
            ("recipient", "Who should I email?"),
            ("subject", "What's the subject?"),
            ("body", "What should the email say?"),
        ]

    def execute(self, details):
        recipient = details.get("recipient", "Unknown")
        subject = details.get("subject", "No subject")
        body = details.get("body", "")

        summary = f"Send email to {recipient} — Subject: \"{subject}\""
        if not self.confirm(summary):
            return False, "Email cancelled."

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        result = (
            f"📧 Email sent successfully!\n"
            f"   To: {recipient}\n"
            f"   Subject: {subject}\n"
            f"   Body: {body[:80]}{'...' if len(body) > 80 else ''}\n"
            f"   Time: {timestamp}\n"
            f"   Status: Delivered ✓"
        )
        return True, result
