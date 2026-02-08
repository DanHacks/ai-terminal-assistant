"""
Command Parser module for AI Terminal Assistant.
Maps natural language input to actions or terminal commands using keyword/intent matching.
"""

import re

# Intent definitions: (intent_name, keywords/patterns, description)
INTENT_PATTERNS = [
    {
        "intent": "send_message",
        "patterns": [
            r"\b(send|text|sms|message|msg|write)\b.*(message|text|sms|msg)?\b.*\b(to)?\b",
            r"\b(text|message|msg)\b\s+\w+",
            r"\btell\b\s+\w+\b",
        ],
        "keywords": ["send message", "text", "sms", "send a message", "message to", "msg"],
    },
    {
        "intent": "make_call",
        "patterns": [
            r"\b(call|phone|dial|ring)\b\s+\w+",
            r"\bmake\b.*\bcall\b",
        ],
        "keywords": ["call", "phone", "dial", "ring", "make a call"],
    },
    {
        "intent": "place_order",
        "patterns": [
            r"\b(order|buy|purchase|get me|get)\b\s+\w+",
            r"\bplace\b.*\border\b",
            r"\border\b.*\b(food|pizza|burger|coffee|groceries|items?)\b",
        ],
        "keywords": ["order", "buy", "purchase", "place order", "get me"],
    },
    {
        "intent": "send_email",
        "patterns": [
            r"\b(email|e-mail|mail)\b\s+\w+",
            r"\bsend\b.*\b(email|e-mail|mail)\b",
        ],
        "keywords": ["email", "e-mail", "send email", "mail to", "send mail"],
    },
    {
        "intent": "set_reminder",
        "patterns": [
            r"\b(remind|reminder|alarm|timer|schedule)\b",
            r"\bset\b.*\b(reminder|alarm|timer)\b",
            r"\bremind\s+me\b",
        ],
        "keywords": ["remind", "reminder", "alarm", "timer", "schedule", "remind me"],
    },
    {
        "intent": "web_search",
        "patterns": [
            r"\b(search|google|look\s*up|find\s+info|browse)\b",
            r"\bsearch\b.*\bfor\b",
            r"\bwhat\s+is\b",
            r"\bwho\s+is\b",
            r"\bhow\s+to\b",
        ],
        "keywords": ["search", "google", "look up", "find info", "browse", "what is", "who is"],
    },
    {
        "intent": "get_weather",
        "patterns": [
            r"\b(weather|temperature|forecast|rain|sunny|cloudy)\b",
        ],
        "keywords": ["weather", "temperature", "forecast", "rain", "sunny"],
    },
    {
        "intent": "open_app",
        "patterns": [
            r"\b(open|launch|start|run)\b\s+\w+",
        ],
        "keywords": ["open", "launch", "start app", "run app"],
    },
]

# Natural language → terminal command mappings
COMMAND_MAPPINGS = {
    "list files": "ls",
    "list all files": "ls -la",
    "show files": "ls",
    "show hidden files": "ls -la",
    "current directory": "pwd",
    "where am i": "pwd",
    "show directory": "pwd",
    "disk usage": "df -h",
    "disk space": "df -h",
    "memory usage": "free -h",
    "system info": "uname -a",
    "running processes": "ps aux",
    "network info": "ifconfig",
    "ip address": "hostname -I",
    "date": "date",
    "time": "date +%T",
    "calendar": "cal",
    "uptime": "uptime",
    "whoami": "whoami",
    "clear screen": "clear",
    "show path": "echo $PATH",
}


def detect_intent(user_input):
    """
    Detect the user's intent from natural language input.
    Returns (intent_name, confidence, extracted_details) or None.
    """
    text = user_input.strip().lower()

    if not text:
        return None

    # Check each intent pattern
    best_match = None
    best_score = 0

    for intent_def in INTENT_PATTERNS:
        score = 0

        # Check regex patterns
        for pattern in intent_def["patterns"]:
            if re.search(pattern, text, re.IGNORECASE):
                score += 2
                break

        # Check keywords
        for keyword in intent_def["keywords"]:
            if keyword.lower() in text:
                score += 1

        if score > best_score:
            best_score = score
            best_match = intent_def["intent"]

    if best_match and best_score >= 2:
        details = extract_details(text, best_match)
        return best_match, best_score, details

    return None


def extract_details(text, intent):
    """Extract relevant details from the user input based on intent."""
    details = {}

    if intent == "send_message":
        # Try to extract recipient: "send message to John"
        match = re.search(r"(?:to|tell)\s+(\w+)", text, re.IGNORECASE)
        if match:
            details["recipient"] = match.group(1).title()
        # Try to extract message content: "saying ..." or "that ..."
        match = re.search(r"(?:saying|that|:)\s+(.+)", text, re.IGNORECASE)
        if match:
            details["message"] = match.group(1).strip()

    elif intent == "make_call":
        match = re.search(r"(?:call|phone|dial|ring)\s+(\w+)", text, re.IGNORECASE)
        if match:
            details["recipient"] = match.group(1).title()

    elif intent == "place_order":
        match = re.search(
            r"(?:order|buy|purchase|get me|get)\s+(?:a\s+|some\s+|the\s+)?(.+?)(?:\s+from\s+(.+))?$",
            text, re.IGNORECASE,
        )
        if match:
            details["item"] = match.group(1).strip()
            if match.group(2):
                details["from"] = match.group(2).strip()

    elif intent == "send_email":
        match = re.search(r"(?:email|mail)\s+(\w+)", text, re.IGNORECASE)
        if match:
            details["recipient"] = match.group(1).title()
        match = re.search(r"(?:about|regarding|subject:?)\s+(.+)", text, re.IGNORECASE)
        if match:
            details["subject"] = match.group(1).strip()

    elif intent == "set_reminder":
        match = re.search(r"(?:remind\s+me\s+to|reminder\s+to|reminder:?)\s+(.+)", text, re.IGNORECASE)
        if match:
            details["task"] = match.group(1).strip()
        match = re.search(r"(?:at|in|by)\s+([\d:]+\s*(?:am|pm|minutes?|hours?|mins?|hrs?)?)", text, re.IGNORECASE)
        if match:
            details["time"] = match.group(1).strip()

    elif intent == "web_search":
        match = re.search(
            r"(?:search\s+(?:for\s+)?|google\s+|look\s*up\s+|what\s+is\s+|who\s+is\s+|how\s+to\s+)(.+)",
            text, re.IGNORECASE,
        )
        if match:
            details["query"] = match.group(1).strip()

    elif intent == "get_weather":
        match = re.search(r"(?:weather|temperature|forecast)\s+(?:in|for|at)\s+(.+)", text, re.IGNORECASE)
        if match:
            details["location"] = match.group(1).strip()

    elif intent == "open_app":
        match = re.search(r"(?:open|launch|start|run)\s+(.+)", text, re.IGNORECASE)
        if match:
            details["app"] = match.group(1).strip()

    return details


def parse_natural_language(user_input):
    """
    Parse natural language into a terminal command.
    Returns the command string or None if no mapping found.
    """
    text = user_input.strip().lower()

    # Direct mapping lookup
    for phrase, command in COMMAND_MAPPINGS.items():
        if phrase in text:
            return command

    # Fallback: if it looks like a raw command, return it as-is
    if text.startswith("/") or text.startswith("!"):
        return text[1:].strip()

    return None
