"""
AI Terminal Assistant — Main entry point.
An interactive assistant that helps you send messages, make calls,
place orders, search the web, and much more — all from the terminal.
"""

import sys
import os

# Ensure src directory is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from platform_utils import detect_platform
from assistant import Assistant
from logger import log_event

BANNER = """
╔══════════════════════════════════════════════════════════╗
║              🤖 AI Terminal Assistant                    ║
║                                                          ║
║  Your personal assistant — right in the terminal.        ║
║  Send messages, make calls, place orders, and more!      ║
╚══════════════════════════════════════════════════════════╝
"""

QUICK_HELP = """  💡 Quick start:
     • "send a message to John"    — Send a text message
     • "call Mom"                  — Make a phone call
     • "order a pizza"             — Place an order
     • "email Bob about meeting"   — Send an email
     • "remind me to buy milk"     — Set a reminder
     • "search for Python tips"    — Search the web
     • "weather in New York"       — Check the weather
     • "open browser"              — Launch an app
     • "list files"                — Run terminal commands
     • !ls -la                     — Direct terminal command
     • help                        — Full help
     • exit                        — Quit
"""


def main():
    platform = detect_platform()

    print(BANNER)
    print(f"  📍 Platform: {platform}")
    print(QUICK_HELP)

    log_event("session_start", f"Platform: {platform}")

    assistant = Assistant(confirm_commands=True)

    while True:
        try:
            user_input = input("\n🤖 >> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nGoodbye 👋")
            log_event("session_end", "User interrupted")
            break

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit", "/exit", "/quit"):
            print("\nGoodbye 👋 Have a great day!")
            log_event("session_end", "User exited")
            break

        response = assistant.process(user_input)
        if response:
            print(f"\n{response}")


if __name__ == "__main__":
    main()
