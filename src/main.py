import os
import sys
from platform_utils import detect_platform
from assistant import AIAssistant
from command_parser import CommandParser
from validator import CommandValidator
from command_executor import CommandExecutor
from logger import ExecutionLogger
from interactions import InteractionManager

def print_banner():
    """Print application banner."""
    banner = """
╔═══════════════════════════════════════════════════════════╗
║          AI Terminal Assistant - Interactive Mode          ║
║                                                            ║
║  Your AI-powered assistant for:                           ║
║  • Terminal commands                                       ║
║  • Sending messages (SMS, Email, Chat)                     ║
║  • Making calls (Voice, Video)                             ║
║  • Placing orders (Food, Shopping)                         ║
║  • Setting reminders                                       ║
║  • And much more!                                          ║
╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)

def print_help():
    """Print help information."""
    help_text = """
Available Commands:
  • Natural language: Just type what you want to do!
    - "send a message to John saying hello"
    - "call mom"
    - "order pizza from uber eats"
    - "list all files in this directory"
    - "remind me to take medicine at 8pm"

  • Special commands:
    - help: Show this help
    - history: Show execution history
    - interactions: List available interaction types
    - exit/quit: Exit the application
    """
    print(help_text)

def main():
    """Main application entry point."""
    print_banner()

    platform = detect_platform()
    print(f"Platform: {platform}")
    print(f"Type 'help' for usage instructions\n")

    # Initialize components
    ai_assistant = AIAssistant()
    command_parser = CommandParser()
    validator = CommandValidator()
    executor = CommandExecutor()
    logger = ExecutionLogger()
    interaction_manager = InteractionManager()

    # Check if AI client is available
    if not ai_assistant.client:
        print("⚠️  Warning: AI client not initialized.")
        print("Set ANTHROPIC_API_KEY or OPENAI_API_KEY environment variable.")
        print("Some features will be limited.\n")

    # Main loop
    while True:
        try:
            user_input = input(">> ").strip()

            if not user_input:
                continue

            # Handle special commands
            if user_input.lower() in ["exit", "quit"]:
                print("\nGoodbye! 👋\n")
                break

            elif user_input.lower() == "help":
                print_help()
                continue

            elif user_input.lower() == "history":
                history = executor.get_history(limit=10)
                if history:
                    print("\nRecent execution history:")
                    for i, entry in enumerate(history[-10:], 1):
                        print(f"{i}. {entry.get('command', entry.get('type', 'unknown'))}")
                        print(f"   Success: {entry.get('success', False)}")
                else:
                    print("No execution history yet.")
                continue

            elif user_input.lower() == "interactions":
                available = interaction_manager.get_available_interactions()
                print("\nAvailable interaction types:")
                for interaction in available:
                    print(f"  • {interaction}")
                continue

            # Parse user input with AI
            print("\nProcessing...")
            context = {"platform": platform}
            ai_output = ai_assistant.parse_command(user_input, context)

            # Handle errors
            if ai_output.get("type") == "error":
                print(f"❌ Error: {ai_output.get('message')}")
                continue

            # Parse command
            parsed_command = command_parser.parse(ai_output)

            command_type = parsed_command.get("type")
            action = parsed_command.get("action", "")

            # Display what was understood
            print(f"\nUnderstood: {ai_output.get('explanation', 'Processing your request')}")

            # Handle different command types
            if command_type == "conversation":
                # Just a conversation, respond accordingly
                response = ai_assistant.generate_response(user_input, context)
                print(f"\n{response}\n")
                continue

            elif command_type == "command":
                # Validate shell command
                is_valid, reason = validator.validate(action)
                if not is_valid:
                    print(f"\n❌ {reason}")
                    print("Command blocked for security reasons.\n")
                    continue

                # Execute command
                result = executor.execute(parsed_command)

                if result.get("cancelled"):
                    print("\n❌ Execution cancelled by user.\n")
                elif result.get("success"):
                    print("\n✅ Command executed successfully!")
                    if result.get("stdout"):
                        print("\nOutput:")
                        print(result["stdout"])
                    if result.get("stderr"):
                        print("\nErrors:")
                        print(result["stderr"])
                    print()
                else:
                    print(f"\n❌ Execution failed: {result.get('error', 'Unknown error')}\n")

            elif command_type in ["message", "call", "order", "interaction"]:
                # Handle interactive actions
                parameters = parsed_command.get("parameters", {})
                result = interaction_manager.execute_interaction(command_type, parameters)

                if result.get("cancelled"):
                    print("\n❌ Action cancelled by user.\n")
                elif result.get("success"):
                    print(f"\n✅ {result.get('message', 'Action completed')}\n")
                else:
                    print(f"\n❌ {result.get('error', 'Action failed')}\n")

            else:
                print(f"\n⚠️  Unknown command type: {command_type}\n")

        except KeyboardInterrupt:
            print("\n\nInterrupted. Type 'exit' to quit.\n")
            continue
        except Exception as e:
            print(f"\n❌ Unexpected error: {str(e)}\n")
            logger.log_event("error", str(e))

if __name__ == "__main__":
    main()
