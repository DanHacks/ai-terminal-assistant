"""
Actions package for AI Terminal Assistant.
Provides a registry of interactive actions users can perform.
"""

from actions.base import BaseAction
from actions.send_message import SendMessageAction
from actions.make_call import MakeCallAction
from actions.place_order import PlaceOrderAction
from actions.send_email import SendEmailAction
from actions.set_reminder import SetReminderAction
from actions.web_search import WebSearchAction
from actions.get_weather import GetWeatherAction
from actions.open_app import OpenAppAction

# Action registry: maps intent names to action classes
ACTION_REGISTRY = {
    "send_message": SendMessageAction,
    "make_call": MakeCallAction,
    "place_order": PlaceOrderAction,
    "send_email": SendEmailAction,
    "set_reminder": SetReminderAction,
    "web_search": WebSearchAction,
    "get_weather": GetWeatherAction,
    "open_app": OpenAppAction,
}


def get_action(intent_name):
    """Get an action instance by intent name."""
    action_class = ACTION_REGISTRY.get(intent_name)
    if action_class:
        return action_class()
    return None


def list_actions():
    """List all available actions with descriptions."""
    actions = []
    for name, cls in ACTION_REGISTRY.items():
        instance = cls()
        actions.append({
            "name": name,
            "description": instance.describe(),
            "examples": instance.examples(),
        })
    return actions
