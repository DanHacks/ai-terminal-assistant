import subprocess
import os
from typing import Dict, Any, Optional
from datetime import datetime

class CommandExecutor:
    """Executes validated commands with user confirmation."""

    def __init__(self, logger=None):
        """
        Initialize the executor.

        Args:
            logger: Optional logger instance
        """
        self.logger = logger
        self.execution_history = []

    def confirm_execution(self, command_info: Dict[str, Any]) -> bool:
        """
        Ask user for confirmation before executing.

        Args:
            command_info: Command information dictionary

        Returns:
            True if user confirms
        """
        command_type = command_info.get("type", "unknown")
        action = command_info.get("action", "")
        risk_level = command_info.get("risk_level", "medium")

        # Display command information
        print("\n" + "="*60)
        print(f"Command Type: {command_type.upper()}")
        print(f"Action: {action}")
        print(f"Risk Level: {risk_level.upper()}")

        if command_info.get("parameters"):
            print(f"Parameters: {command_info['parameters']}")

        print("="*60)

        # Get user confirmation
        while True:
            response = input("\nExecute this command? (yes/no): ").lower().strip()
            if response in ['yes', 'y']:
                return True
            elif response in ['no', 'n']:
                return False
            else:
                print("Please enter 'yes' or 'no'")

    def execute_shell_command(self, command: str) -> Dict[str, Any]:
        """
        Execute a shell command.

        Args:
            command: Shell command to execute

        Returns:
            Execution result dictionary
        """
        start_time = datetime.now()

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )

            execution_result = {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": command,
                "timestamp": start_time.isoformat(),
                "duration": (datetime.now() - start_time).total_seconds()
            }

            # Log execution
            self._log_execution(execution_result)

            return execution_result

        except subprocess.TimeoutExpired:
            execution_result = {
                "success": False,
                "error": "Command timed out after 30 seconds",
                "command": command,
                "timestamp": start_time.isoformat()
            }
            self._log_execution(execution_result)
            return execution_result

        except Exception as e:
            execution_result = {
                "success": False,
                "error": str(e),
                "command": command,
                "timestamp": start_time.isoformat()
            }
            self._log_execution(execution_result)
            return execution_result

    def execute_interactive_action(self, action_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an interactive action (message, call, order, etc.).

        Args:
            action_info: Action information dictionary

        Returns:
            Execution result
        """
        action_type = action_info.get("type")
        action = action_info.get("action")
        parameters = action_info.get("parameters", {})

        start_time = datetime.now()

        # For now, simulate interactive actions
        # In a real implementation, this would integrate with APIs
        result = {
            "success": True,
            "type": action_type,
            "action": action,
            "parameters": parameters,
            "timestamp": start_time.isoformat(),
            "simulated": True,
            "message": f"Simulated {action_type} action: {action}"
        }

        if action_type == "message":
            result["message"] = f"Would send message to {parameters.get('recipient', 'unknown')}: {parameters.get('content', '')}"
        elif action_type == "call":
            result["message"] = f"Would initiate call to {parameters.get('recipient', 'unknown')}"
        elif action_type == "order":
            result["message"] = f"Would place order: {parameters.get('item', 'unknown')} from {parameters.get('service', 'unknown')}"
        elif action_type == "interaction":
            result["message"] = f"Would perform interaction: {action}"

        self._log_execution(result)
        return result

    def execute(self, command_info: Dict[str, Any], skip_confirmation: bool = False) -> Dict[str, Any]:
        """
        Execute a command or action.

        Args:
            command_info: Command information
            skip_confirmation: Skip user confirmation (use with caution)

        Returns:
            Execution result
        """
        # Check if confirmation is required
        if command_info.get("requires_confirmation", True) and not skip_confirmation:
            if not self.confirm_execution(command_info):
                return {
                    "success": False,
                    "cancelled": True,
                    "message": "Execution cancelled by user"
                }

        command_type = command_info.get("type")

        if command_type == "command":
            return self.execute_shell_command(command_info.get("action", ""))
        elif command_type in ["message", "call", "order", "interaction"]:
            return self.execute_interactive_action(command_info)
        elif command_type == "conversation":
            return {
                "success": True,
                "type": "conversation",
                "message": "Conversational response - no action to execute"
            }
        else:
            return {
                "success": False,
                "error": f"Unknown command type: {command_type}"
            }

    def _log_execution(self, execution_result: Dict[str, Any]) -> None:
        """
        Log command execution.

        Args:
            execution_result: Result of execution
        """
        self.execution_history.append(execution_result)

        if self.logger:
            self.logger.log_execution(execution_result)

    def get_history(self, limit: Optional[int] = None) -> list:
        """
        Get execution history.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of execution results
        """
        if limit:
            return self.execution_history[-limit:]
        return self.execution_history.copy()
