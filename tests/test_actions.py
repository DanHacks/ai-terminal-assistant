"""Tests for the actions package."""

from unittest.mock import patch
from actions import get_action, list_actions, ACTION_REGISTRY
from actions.base import BaseAction


class TestActionRegistry:
    """Tests for the action registry."""

    def test_all_actions_registered(self):
        expected = [
            "send_message", "make_call", "place_order", "send_email",
            "set_reminder", "web_search", "get_weather", "open_app",
        ]
        for name in expected:
            assert name in ACTION_REGISTRY, f"Action '{name}' not registered"

    def test_get_action_valid(self):
        action = get_action("send_message")
        assert action is not None
        assert isinstance(action, BaseAction)

    def test_get_action_invalid(self):
        action = get_action("nonexistent_action")
        assert action is None

    def test_list_actions(self):
        actions = list_actions()
        assert len(actions) == len(ACTION_REGISTRY)
        for action_info in actions:
            assert "name" in action_info
            assert "description" in action_info
            assert "examples" in action_info

    def test_all_actions_have_descriptions(self):
        for name, cls in ACTION_REGISTRY.items():
            instance = cls()
            desc = instance.describe()
            assert desc and len(desc) > 0, f"Action '{name}' has no description"

    def test_all_actions_have_examples(self):
        for name, cls in ACTION_REGISTRY.items():
            instance = cls()
            examples = instance.examples()
            assert len(examples) > 0, f"Action '{name}' has no examples"

    def test_all_actions_have_required_fields(self):
        for name, cls in ACTION_REGISTRY.items():
            instance = cls()
            fields = instance.get_required_fields()
            assert isinstance(fields, list), f"Action '{name}' fields not a list"
            for field_name, prompt in fields:
                assert field_name and prompt, f"Action '{name}' has empty field definition"


class TestSendMessageAction:
    """Tests for the SendMessage action."""

    @patch("builtins.input", return_value="y")
    def test_execute_success(self, mock_input):
        action = get_action("send_message")
        details = {"recipient": "John", "message": "Hello there!"}
        success, result = action.execute(details)
        assert success is True
        assert "John" in result
        assert "Hello there!" in result

    @patch("builtins.input", return_value="n")
    def test_execute_cancelled(self, mock_input):
        action = get_action("send_message")
        details = {"recipient": "John", "message": "Hello"}
        success, result = action.execute(details)
        assert success is False
        assert "cancelled" in result.lower()


class TestMakeCallAction:
    """Tests for the MakeCall action."""

    @patch("builtins.input", return_value="y")
    def test_execute_success(self, mock_input):
        action = get_action("make_call")
        details = {"recipient": "Mom"}
        success, result = action.execute(details)
        assert success is True
        assert "Mom" in result

    @patch("builtins.input", return_value="n")
    def test_execute_cancelled(self, mock_input):
        action = get_action("make_call")
        details = {"recipient": "Mom"}
        success, result = action.execute(details)
        assert success is False


class TestPlaceOrderAction:
    """Tests for the PlaceOrder action."""

    @patch("builtins.input", return_value="y")
    def test_execute_success(self, mock_input):
        action = get_action("place_order")
        details = {"item": "pizza", "quantity": "2"}
        success, result = action.execute(details)
        assert success is True
        assert "pizza" in result.lower()
        assert "ORD-" in result


class TestSetReminderAction:
    """Tests for the SetReminder action."""

    @patch("builtins.input", return_value="y")
    def test_execute_success(self, mock_input):
        action = get_action("set_reminder")
        details = {"task": "Buy groceries", "time": "5pm"}
        success, result = action.execute(details)
        assert success is True
        assert "Buy groceries" in result


class TestGetWeatherAction:
    """Tests for the GetWeather action."""

    @patch("builtins.input", return_value="y")
    def test_execute_success(self, mock_input):
        action = get_action("get_weather")
        details = {"location": "New York"}
        success, result = action.execute(details)
        assert success is True
        assert "New York" in result
