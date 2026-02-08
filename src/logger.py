"""
Logging module for command execution and interactions.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, Optional

class ExecutionLogger:
    """Logs command execution and interactions."""

    def __init__(self, log_dir: str = "logs", log_file: str = "execution.log"):
        """Initialize the logger."""
        self.log_dir = log_dir
        self.log_file = log_file
        self.log_path = os.path.join(log_dir, log_file)
        os.makedirs(log_dir, exist_ok=True)

    def log_execution(self, execution_result: Dict[str, Any]) -> None:
        """Log an execution result."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "result": execution_result
        }
        try:
            with open(self.log_path, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            print(f"Warning: Could not write to log file: {e}")

    def log_event(self, event_type: str, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Log a general event."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "message": message,
            "data": data or {}
        }
        try:
            with open(self.log_path, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            print(f"Warning: Could not write to log file: {e}")

    def get_logs(self, limit: Optional[int] = None) -> list:
        """Get recent log entries."""
        if not os.path.exists(self.log_path):
            return []
        try:
            with open(self.log_path, "r") as f:
                lines = f.readlines()
            logs = []
            for line in lines:
                try:
                    logs.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    continue
            if limit:
                return logs[-limit:]
            return logs
        except Exception as e:
            print(f"Warning: Could not read log file: {e}")
            return []

