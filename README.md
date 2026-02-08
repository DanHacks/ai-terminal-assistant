# AI Terminal Assistant - Interactive Edition

AI Terminal Assistant is a secure, AI-powered command-line tool that helps you interact with your system and the world using natural language. From executing terminal commands to sending messages, making calls, and placing orders - all through conversational AI.

The project is designed to work on **Termux (Android)**, **Linux**, and **Windows** systems.

---

## 🚀 Features

### Core Capabilities
- **Natural Language Processing**: Convert plain English into actions
- **Terminal Commands**: Execute safe system commands with validation
- **Message Sending**: Send SMS, emails, WhatsApp, Telegram, Slack messages
- **Phone & Video Calls**: Initiate calls through various services
- **Order Placement**: Order food, groceries, and products online
- **Reminders**: Set reminders and alarms
- **Extensible Plugin System**: Easy to add new interaction types

### Safety Features
- Command whitelist and blacklist for security
- User confirmation before ALL executions
- Risk assessment for every command
- Command execution logging
- Security-first design (dangerous commands blocked)

### Technical Features
- Supports multiple AI providers (Anthropic Claude, OpenAI GPT)
- Cross-platform support (Termux, Linux, Windows)
- Modular and extensible architecture
- Comprehensive logging system
- Execution history tracking

---

## 📋 Prerequisites

- Python 3.8+
- API key for Anthropic Claude or OpenAI GPT
- Internet connection (for AI processing)

---

## 🔧 Installation

### 1. Clone the repository
```bash
git clone <repository-url>
cd ai-terminal-assistant
```

### 2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up API key

Set one of these environment variables:

**For Anthropic Claude:**
```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

**For OpenAI:**
```bash
export OPENAI_API_KEY="your-api-key-here"
```

Or create a `.env` file:
```
ANTHROPIC_API_KEY=your-api-key-here
# OR
OPENAI_API_KEY=your-api-key-here
```

---

## 🎯 Usage

### Starting the Assistant

```bash
python src/main.py
```

### Example Interactions

**Terminal Commands:**
```
>> list all files in this directory
>> show me the current date and time
>> find all python files
```

**Sending Messages:**
```
>> send a message to John saying "Meeting at 3pm"
>> email Alice about the project update
>> send a WhatsApp to Mom saying I'll be late
```

**Making Calls:**
```
>> call Dad
>> video call with the team on Zoom
>> make a phone call to +1234567890
```

**Placing Orders:**
```
>> order pizza from Uber Eats
>> order groceries from Instacart
>> buy batteries from Amazon
```

**Setting Reminders:**
```
>> remind me to take medicine at 8pm
>> set an alarm for 6am tomorrow
>> remind me about the meeting in 1 hour
```

**General Conversation:**
```
>> what's the weather like?
>> tell me a joke
>> help me plan my day
```

### Special Commands

- `help` - Show usage instructions
- `history` - View recent execution history
- `interactions` - List available interaction types
- `exit` or `quit` - Exit the application

---

## 🛡️ Safety Principles

This tool **never executes commands automatically**.

Before any command or action runs:
1. The AI interprets your request
2. The command is validated against a blacklist
3. The command is checked against an allowed whitelist
4. Risk level is assessed (low/medium/high)
5. **You must explicitly confirm execution**

Dangerous commands such as `rm -rf`, `dd`, `format`, etc. are blocked by design.

---

## 🔌 Interactive Plugins

The system includes the following plugins:

### MessagePlugin
- Services: SMS, Email, WhatsApp, Telegram, Slack
- Parameters: recipient, content, service

### CallPlugin
- Types: Voice, Video
- Services: Phone, WhatsApp, Zoom, etc.
- Parameters: recipient, call_type, service

### OrderPlugin
- Services: Uber Eats, DoorDash, GrubHub, Amazon, Instacart
- Parameters: service, item, quantity, delivery_address, notes

### ReminderPlugin
- Features: One-time and recurring reminders
- Parameters: content, time, repeat

---

## 📁 Project Structure

```
ai-terminal-assistant/
├── src/
│   ├── main.py              # Main application entry point
│   ├── assistant.py         # AI assistant with Claude/OpenAI integration
│   ├── command_parser.py    # Parses AI output into structured commands
│   ├── validator.py         # Command validation (whitelist/blacklist)
│   ├── command_executor.py  # Executes commands with confirmation
│   ├── interactions.py      # Interactive plugins (messages, calls, orders)
│   ├── logger.py           # Execution logging
│   └── platform_utils.py   # Platform detection utilities
├── config/
│   ├── command_whitelist.json  # Allowed commands
│   └── command_blacklist.json  # Forbidden commands/patterns
├── logs/                   # Execution logs (created automatically)
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

---

## ⚙️ Configuration

### Command Whitelist (`config/command_whitelist.json`)

Add commands that are allowed to execute:
```json
[
  "ls", "pwd", "cd", "cat", "echo",
  "find", "grep", "python", "pip"
]
```

### Command Blacklist (`config/command_blacklist.json`)

Add forbidden patterns:
```json
[
  "rm -rf",
  "dd",
  "mkfs",
  "shutdown",
  "reboot",
  "format"
]
```

---

## 🔨 Extending the System

### Adding a New Plugin

Create a new plugin class in `src/interactions.py`:

```python
class MyPlugin(InteractionPlugin):
    def __init__(self):
        super().__init__("my_plugin")

    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        # Your implementation here
        return {
            "success": True,
            "message": "Plugin executed"
        }

    def validate_parameters(self, parameters: Dict[str, Any]) -> tuple[bool, str]:
        # Validate parameters
        return True, "Valid"
```

Register it in `InteractionManager`:
```python
self.register_plugin(MyPlugin())
```

---

## 🖥️ Supported Platforms

- ✅ Termux (Android)
- ✅ Linux
- ✅ macOS
- ⚠️ Windows (basic support)

Platform detection is automatic at runtime.

---

## 🔐 Security Considerations

1. **API Keys**: Keep your API keys secure. Never commit them to version control.
2. **Command Execution**: Always review commands before confirming execution.
3. **Third-Party Services**: Interactive features (messages, calls, orders) are currently simulated. Integration with real services requires proper authentication and authorization.
4. **Whitelist/Blacklist**: Customize these based on your security requirements.
5. **Logging**: Execution logs may contain sensitive information. Protect the `logs/` directory.

---

## 🤝 Contributing

Contributions are welcome! Areas for improvement:

- Integration with real messaging/calling APIs
- Support for more interaction types
- Enhanced natural language understanding
- Better error handling
- Unit and integration tests
- Windows platform improvements

---

## 📄 License

This project is provided as-is for educational and personal use.

---

## ⚠️ Disclaimer

This tool executes system commands and interacts with external services. Use at your own risk. The authors are not responsible for any damage caused by misuse of this tool.

**Always review and understand commands before executing them.**

---

## 🆘 Troubleshooting

### "AI client not initialized"
- Make sure you've set `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`
- Check that the API key is valid
- Ensure you have installed the required packages: `pip install anthropic openai`

### "Command blocked"
- The command may be in the blacklist
- The command executable may not be in the whitelist
- Edit `config/command_whitelist.json` or `config/command_blacklist.json`

### "Import errors"
- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Activate your virtual environment

---

## 📞 Support

For issues, questions, or suggestions, please open an issue on the repository.
