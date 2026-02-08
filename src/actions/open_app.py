"""
Open App action — launch applications on the current platform.
"""

import subprocess
from actions.base import BaseAction
from platform_utils import detect_platform


# Common app name → command mappings per platform
APP_COMMANDS = {
    "linux": {
        "browser": "xdg-open https://www.google.com",
        "firefox": "firefox",
        "chrome": "google-chrome",
        "files": "nautilus",
        "file manager": "nautilus",
        "terminal": "gnome-terminal",
        "calculator": "gnome-calculator",
        "text editor": "gedit",
        "settings": "gnome-control-center",
        "music": "rhythmbox",
        "video": "totem",
    },
    "termux": {
        "browser": "termux-open-url https://www.google.com",
        "files": "termux-storage-get",
        "camera": "termux-camera-photo /sdcard/photo.jpg",
        "contacts": "termux-contact-list",
        "location": "termux-location",
        "battery": "termux-battery-status",
        "wifi": "termux-wifi-connectioninfo",
        "clipboard": "termux-clipboard-get",
        "torch": "termux-torch on",
        "vibrate": "termux-vibrate",
    },
    "windows": {
        "browser": "start https://www.google.com",
        "chrome": "start chrome",
        "firefox": "start firefox",
        "notepad": "notepad",
        "calculator": "calc",
        "file manager": "explorer",
        "files": "explorer",
        "paint": "mspaint",
        "settings": "start ms-settings:",
        "task manager": "taskmgr",
        "cmd": "cmd",
        "powershell": "powershell",
    },
}


class OpenAppAction(BaseAction):

    def describe(self):
        return "Open or launch an application"

    def examples(self):
        return [
            "open browser",
            "launch calculator",
            "start file manager",
            "open camera",
            "run firefox",
        ]

    def get_required_fields(self):
        return [
            ("app", "Which app do you want to open?"),
        ]

    def execute(self, details):
        app = details.get("app", "").lower().strip()
        platform = detect_platform()

        summary = f"Open {app} on {platform}"
        if not self.confirm(summary):
            return False, "App launch cancelled."

        platform_apps = APP_COMMANDS.get(platform, APP_COMMANDS.get("linux", {}))
        command = platform_apps.get(app)

        if not command:
            # Try fuzzy match
            for app_name, cmd in platform_apps.items():
                if app in app_name or app_name in app:
                    command = cmd
                    break

        if not command:
            available = ", ".join(sorted(platform_apps.keys()))
            result = (
                f"❓ App \"{app}\" not found for {platform}.\n"
                f"   Available apps: {available}\n"
                f"   Tip: You can also run terminal commands with: !<command>"
            )
            return False, result

        try:
            subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            result = (
                f"🚀 Launching {app}...\n"
                f"   Command: {command}\n"
                f"   Platform: {platform}\n"
                f"   Status: Launched ✓"
            )
            return True, result

        except Exception as e:
            result = (
                f"❌ Failed to open {app}\n"
                f"   Error: {str(e)}\n"
                f"   Try running manually: {command}"
            )
            return False, result
