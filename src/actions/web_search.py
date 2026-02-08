"""
Web Search action — search the web for information.
"""

import urllib.parse
import webbrowser
from actions.base import BaseAction
from platform_utils import detect_platform


class WebSearchAction(BaseAction):

    def describe(self):
        return "Search the web for information"

    def examples(self):
        return [
            "search for Python tutorials",
            "google how to make pasta",
            "look up the weather in New York",
            "what is machine learning",
            "who is Elon Musk",
        ]

    def get_required_fields(self):
        return [
            ("query", "What do you want to search for?"),
        ]

    def execute(self, details):
        query = details.get("query", "")

        summary = f"Search the web for: \"{query}\""
        if not self.confirm(summary):
            return False, "Search cancelled."

        encoded_query = urllib.parse.quote_plus(query)
        search_url = f"https://www.google.com/search?q={encoded_query}"

        platform = detect_platform()
        opened = False

        try:
            if platform == "termux":
                import subprocess
                subprocess.run(
                    ["termux-open-url", search_url],
                    capture_output=True, timeout=5,
                )
                opened = True
            else:
                webbrowser.open(search_url)
                opened = True
        except Exception:
            opened = False

        if opened:
            result = (
                f"🔍 Searching for: \"{query}\"\n"
                f"   URL: {search_url}\n"
                f"   Status: Browser opened ✓"
            )
        else:
            result = (
                f"🔍 Search for: \"{query}\"\n"
                f"   URL: {search_url}\n"
                f"   (Could not open browser — copy the URL above)"
            )

        return True, result
