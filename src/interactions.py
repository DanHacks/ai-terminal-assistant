"""
Interactive capabilities module for messages, calls, orders, and more.
This module provides plugins for various user interactions.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import json

class InteractionPlugin:
    """Base class for interaction plugins."""

    def __init__(self, name: str):
        """Initialize the plugin."""
        self.name = name
        self.enabled = True

    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the interaction."""
        raise NotImplementedError("Subclasses must implement execute()")

    def validate_parameters(self, parameters: Dict[str, Any]) -> tuple[bool, str]:
        """Validate parameters for the interaction."""
        return True, "Parameters valid"


class MessagePlugin(InteractionPlugin):
    """Plugin for sending messages (SMS, email, chat apps)."""

    def __init__(self):
        """Initialize message plugin."""
        super().__init__("message")
        self.supported_services = ["sms", "email", "whatsapp", "telegram", "slack"]

    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a message.

        Parameters:
            recipient: Phone number, email, or username
            content: Message content
            service: Service to use (sms, email, whatsapp, etc.)
        """
        recipient = parameters.get("recipient")
        content = parameters.get("content")
        service = parameters.get("service", "sms").lower()

        is_valid, error_msg = self.validate_parameters(parameters)
        if not is_valid:
            return {"success": False, "error": error_msg}

        # Simulate sending message
        # In production, integrate with actual APIs (Twilio, SendGrid, etc.)
        return {
            "success": True,
            "plugin": self.name,
            "service": service,
            "recipient": recipient,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "simulated": True,
            "message": f"[SIMULATED] Would send {service} message to {recipient}: {content}"
        }

    def validate_parameters(self, parameters: Dict[str, Any]) -> tuple[bool, str]:
        """Validate message parameters."""
        if not parameters.get("recipient"):
            return False, "Missing recipient"
        if not parameters.get("content"):
            return False, "Missing message content"

        service = parameters.get("service", "sms").lower()
        if service not in self.supported_services:
            return False, f"Unsupported service. Supported: {', '.join(self.supported_services)}"

        return True, "Valid"


class CallPlugin(InteractionPlugin):
    """Plugin for making phone/video calls."""

    def __init__(self):
        """Initialize call plugin."""
        super().__init__("call")
        self.supported_types = ["voice", "video"]

    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a call.

        Parameters:
            recipient: Phone number or contact
            call_type: voice or video
            service: Service to use (phone, whatsapp, zoom, etc.)
        """
        recipient = parameters.get("recipient")
        call_type = parameters.get("call_type", "voice").lower()
        service = parameters.get("service", "phone")

        is_valid, error_msg = self.validate_parameters(parameters)
        if not is_valid:
            return {"success": False, "error": error_msg}

        # Simulate call
        return {
            "success": True,
            "plugin": self.name,
            "recipient": recipient,
            "call_type": call_type,
            "service": service,
            "timestamp": datetime.now().isoformat(),
            "simulated": True,
            "message": f"[SIMULATED] Would initiate {call_type} call to {recipient} via {service}"
        }

    def validate_parameters(self, parameters: Dict[str, Any]) -> tuple[bool, str]:
        """Validate call parameters."""
        if not parameters.get("recipient"):
            return False, "Missing recipient"

        call_type = parameters.get("call_type", "voice").lower()
        if call_type not in self.supported_types:
            return False, f"Unsupported call type. Supported: {', '.join(self.supported_types)}"

        return True, "Valid"


class OrderPlugin(InteractionPlugin):
    """Plugin for making orders (food delivery, shopping, etc.)."""

    def __init__(self):
        """Initialize order plugin."""
        super().__init__("order")
        self.supported_services = ["uber_eats", "doordash", "grubhub", "amazon", "instacart"]

    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Place an order.

        Parameters:
            service: Service to use (uber_eats, amazon, etc.)
            item: Item or meal to order
            quantity: Quantity (default 1)
            delivery_address: Delivery address (optional)
            notes: Special instructions (optional)
        """
        service = parameters.get("service", "").lower()
        item = parameters.get("item")
        quantity = parameters.get("quantity", 1)
        delivery_address = parameters.get("delivery_address", "Default address")
        notes = parameters.get("notes", "")

        is_valid, error_msg = self.validate_parameters(parameters)
        if not is_valid:
            return {"success": False, "error": error_msg}

        # Simulate order
        return {
            "success": True,
            "plugin": self.name,
            "service": service,
            "item": item,
            "quantity": quantity,
            "delivery_address": delivery_address,
            "notes": notes,
            "timestamp": datetime.now().isoformat(),
            "simulated": True,
            "message": f"[SIMULATED] Would place order on {service}: {quantity}x {item} to {delivery_address}"
        }

    def validate_parameters(self, parameters: Dict[str, Any]) -> tuple[bool, str]:
        """Validate order parameters."""
        if not parameters.get("item"):
            return False, "Missing item to order"

        service = parameters.get("service", "").lower()
        if service and service not in self.supported_services:
            return False, f"Unsupported service. Supported: {', '.join(self.supported_services)}"

        return True, "Valid"


class ReminderPlugin(InteractionPlugin):
    """Plugin for setting reminders and alarms."""

    def __init__(self):
        """Initialize reminder plugin."""
        super().__init__("reminder")
        self.reminders = []

    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Set a reminder.

        Parameters:
            content: What to be reminded about
            time: When to remind (timestamp or relative time)
            repeat: Repeat interval (optional)
        """
        content = parameters.get("content")
        time = parameters.get("time")
        repeat = parameters.get("repeat")

        is_valid, error_msg = self.validate_parameters(parameters)
        if not is_valid:
            return {"success": False, "error": error_msg}

        reminder = {
            "id": len(self.reminders) + 1,
            "content": content,
            "time": time,
            "repeat": repeat,
            "created_at": datetime.now().isoformat()
        }

        self.reminders.append(reminder)

        return {
            "success": True,
            "plugin": self.name,
            "reminder": reminder,
            "simulated": True,
            "message": f"[SIMULATED] Would set reminder: '{content}' at {time}"
        }

    def validate_parameters(self, parameters: Dict[str, Any]) -> tuple[bool, str]:
        """Validate reminder parameters."""
        if not parameters.get("content"):
            return False, "Missing reminder content"
        if not parameters.get("time"):
            return False, "Missing reminder time"
        return True, "Valid"


class InteractionManager:
    """Manages all interaction plugins."""

    def __init__(self):
        """Initialize the interaction manager."""
        self.plugins: Dict[str, InteractionPlugin] = {}
        self._register_default_plugins()

    def _register_default_plugins(self):
        """Register default plugins."""
        self.register_plugin(MessagePlugin())
        self.register_plugin(CallPlugin())
        self.register_plugin(OrderPlugin())
        self.register_plugin(ReminderPlugin())

    def register_plugin(self, plugin: InteractionPlugin):
        """Register a new plugin."""
        self.plugins[plugin.name] = plugin

    def execute_interaction(self, interaction_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an interaction.

        Args:
            interaction_type: Type of interaction (message, call, order, etc.)
            parameters: Parameters for the interaction

        Returns:
            Execution result
        """
        plugin = self.plugins.get(interaction_type)

        if not plugin:
            return {
                "success": False,
                "error": f"Unknown interaction type: {interaction_type}",
                "available_types": list(self.plugins.keys())
            }

        if not plugin.enabled:
            return {
                "success": False,
                "error": f"Plugin '{interaction_type}' is disabled"
            }

        return plugin.execute(parameters)

    def get_available_interactions(self) -> List[str]:
        """Get list of available interaction types."""
        return [name for name, plugin in self.plugins.items() if plugin.enabled]

    def get_plugin_info(self, interaction_type: str) -> Optional[Dict[str, Any]]:
        """Get information about a plugin."""
        plugin = self.plugins.get(interaction_type)
        if not plugin:
            return None

        return {
            "name": plugin.name,
            "enabled": plugin.enabled,
            "type": type(plugin).__name__
        }
