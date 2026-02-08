"""
Set Reminder action — create reminders, alarms, and timers.
"""

import json
import os
from datetime import datetime
from actions.base import BaseAction

REMINDERS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data", "reminders.json",
)


class SetReminderAction(BaseAction):

    def describe(self):
        return "Set a reminder, alarm, or timer"

    def examples(self):
        return [
            "remind me to call Mom at 5pm",
            "set a reminder to buy groceries",
            "set an alarm for 7am",
            "timer for 10 minutes",
            "remind me to take medicine",
        ]

    def get_required_fields(self):
        return [
            ("task", "What should I remind you about?"),
            ("time", "When? (e.g., '5pm', 'in 30 minutes', 'tomorrow')"),
        ]

    def execute(self, details):
        task = details.get("task", "")
        time_str = details.get("time", "not specified")

        summary = f"Set reminder: \"{task}\" at {time_str}"
        if not self.confirm(summary):
            return False, "Reminder cancelled."

        reminder = {
            "task": task,
            "time": time_str,
            "created_at": datetime.now().isoformat(),
            "status": "active",
        }

        self._save_reminder(reminder)

        result = (
            f"⏰ Reminder set!\n"
            f"   Task: {task}\n"
            f"   When: {time_str}\n"
            f"   Status: Active ✓\n"
            f"   (You'll be reminded when the time comes)"
        )
        return True, result

    def _save_reminder(self, reminder):
        """Persist the reminder to a JSON file."""
        os.makedirs(os.path.dirname(REMINDERS_FILE), exist_ok=True)

        reminders = []
        if os.path.exists(REMINDERS_FILE):
            try:
                with open(REMINDERS_FILE, "r", encoding="utf-8") as f:
                    reminders = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                reminders = []

        reminders.append(reminder)

        with open(REMINDERS_FILE, "w", encoding="utf-8") as f:
            json.dump(reminders, f, indent=2, ensure_ascii=False)
