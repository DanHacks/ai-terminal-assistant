import platform
import os

def detect_platform():
    if "TERMUX_VERSION" in os.environ:
        return "termux"
    return platform.system().lower()
