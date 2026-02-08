"""Tests for the command parser module."""

from command_parser import parse_natural_language, detect_intent, extract_details


class TestParseNaturalLanguage:
    """Tests for natural language → terminal command mapping."""

    def test_list_files(self):
        assert parse_natural_language("list files") == "ls"

    def test_list_all_files(self):
        assert parse_natural_language("list all files") == "ls -la"

    def test_current_directory(self):
        assert parse_natural_language("current directory") == "pwd"

    def test_where_am_i(self):
        assert parse_natural_language("where am i") == "pwd"

    def test_disk_usage(self):
        assert parse_natural_language("disk usage") == "df -h"

    def test_system_info(self):
        assert parse_natural_language("system info") == "uname -a"

    def test_direct_command_bang(self):
        assert parse_natural_language("!ls -la") == "ls -la"

    def test_direct_command_slash(self):
        assert parse_natural_language("/ls -la") == "ls -la"

    def test_no_match(self):
        assert parse_natural_language("random gibberish xyz") is None

    def test_empty_input(self):
        assert parse_natural_language("") is None


class TestDetectIntent:
    """Tests for intent detection from natural language."""

    def test_send_message_intent(self):
        result = detect_intent("send a message to John")
        assert result is not None
        intent, confidence, details = result
        assert intent == "send_message"
        assert confidence >= 2

    def test_make_call_intent(self):
        result = detect_intent("call Mom")
        assert result is not None
        intent, confidence, details = result
        assert intent == "make_call"

    def test_place_order_intent(self):
        result = detect_intent("order a pizza")
        assert result is not None
        intent, confidence, details = result
        assert intent == "place_order"

    def test_send_email_intent(self):
        result = detect_intent("email Bob about the meeting")
        assert result is not None
        intent, confidence, details = result
        assert intent == "send_email"

    def test_set_reminder_intent(self):
        result = detect_intent("remind me to buy groceries")
        assert result is not None
        intent, confidence, details = result
        assert intent == "set_reminder"

    def test_web_search_intent(self):
        result = detect_intent("search for Python tutorials")
        assert result is not None
        intent, confidence, details = result
        assert intent == "web_search"

    def test_weather_intent(self):
        result = detect_intent("weather in New York")
        assert result is not None
        intent, confidence, details = result
        assert intent == "get_weather"

    def test_empty_input(self):
        result = detect_intent("")
        assert result is None


class TestExtractDetails:
    """Tests for detail extraction from user input."""

    def test_message_recipient(self):
        details = extract_details("send a message to john", "send_message")
        assert details.get("recipient") == "John"

    def test_call_recipient(self):
        details = extract_details("call mom", "make_call")
        assert details.get("recipient") == "Mom"

    def test_order_item(self):
        details = extract_details("order a pizza", "place_order")
        assert "pizza" in details.get("item", "").lower()

    def test_email_recipient(self):
        details = extract_details("email bob about the meeting", "send_email")
        assert details.get("recipient") == "Bob"

    def test_reminder_task(self):
        details = extract_details("remind me to buy groceries", "set_reminder")
        assert "buy groceries" in details.get("task", "").lower()

    def test_search_query(self):
        details = extract_details("search for python tutorials", "web_search")
        assert "python tutorials" in details.get("query", "").lower()

    def test_weather_location(self):
        details = extract_details("weather in new york", "get_weather")
        assert "new york" in details.get("location", "").lower()
