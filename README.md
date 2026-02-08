# AI Terminal Assistant

AI Terminal Assistant is a secure, AI-powered command-line tool that converts natural language instructions into safe terminal commands **and** interactive actions.  
It helps you send messages, make calls, place orders, send emails, set reminders, search the web, check weather, and open apps — all from the terminal.

The project is designed to work on **Termux (Android)** and later be transferred seamlessly to **Linux and Windows** systems.

---

## 🚀 Features

### Interactive Actions
- **Send Messages** — "send a message to John saying hello"
- **Make Calls** — "call Mom"
- **Place Orders** — "order a pizza from Dominos"
- **Send Emails** — "email Bob about the meeting"
- **Set Reminders** — "remind me to buy groceries at 5pm"
- **Web Search** — "search for Python tutorials"
- **Check Weather** — "weather in New York"
- **Open Apps** — "open browser", "launch calculator"

### Terminal Commands
- Natural language to terminal command translation ("list files" → `ls`)
- Direct command execution with `!` prefix (`!ls -la`)
- Command whitelist and blacklist for safety
- User confirmation before command execution

### Core
- Cross-platform support (Termux, Linux, Windows)
- Command execution logging
- Modular and extensible architecture
- Security-first design (dangerous commands blocked)

---

## 🛡️ Safety Principles

This tool **never executes commands automatically**.

Before any command runs:
1. The command is validated against a blacklist
2. The command is checked against an allowed whitelist
3. The user must explicitly confirm execution

Dangerous commands such as destructive file operations are blocked by design.

---

## 🖥️ Supported Platforms

- Termux (Android)
- Linux
- Windows (planned)

Platform detection is automatic at runtime.

---

## 📦 Installation

```bash
pip install -r requirements.txt
```

## ▶️ Usage

```bash
cd src
python main.py
```

### Example Interactions

```
🤖 >> send a message to John saying I'll be late
🤖 >> call Mom
🤖 >> order a pizza
🤖 >> email Sarah about the project deadline
🤖 >> remind me to take medicine at 9pm
🤖 >> search for best Python libraries
🤖 >> weather in Tokyo
🤖 >> open browser
🤖 >> list files
🤖 >> !ls -la
🤖 >> help
```

---

## 🧪 Running Tests

```bash
python -m pytest tests/ -v
```

---

## 🏗️ Architecture

```
src/
├── main.py              # Entry point — interactive REPL
├── assistant.py         # Orchestrator — routes input to actions/commands
├── command_parser.py    # NLP intent detection & command mapping
├── command_executor.py  # Safe terminal command execution
├── validator.py         # Blacklist/whitelist safety checks
├── logger.py            # Action & command logging
├── platform_utils.py    # Cross-platform detection
└── actions/             # Interactive action modules
    ├── __init__.py      # Action registry
    ├── base.py          # BaseAction abstract class
    ├── send_message.py  # Send SMS/text messages
    ├── make_call.py     # Make phone calls
    ├── place_order.py   # Place orders
    ├── send_email.py    # Send emails
    ├── set_reminder.py  # Set reminders & alarms
    ├── web_search.py    # Web search
    ├── get_weather.py   # Weather information
    └── open_app.py      # Launch applications
```

---

## 🔌 Extending with Real APIs

Each action is a self-contained module with a plug-in architecture. To connect real services:

- **Messages/Calls**: Integrate [Twilio](https://www.twilio.com/) in `send_message.py` / `make_call.py`
- **Email**: Configure SMTP in `send_email.py`
- **Orders**: Connect your preferred API in `place_order.py`
- **Weather**: Add [OpenWeatherMap](https://openweathermap.org/api) API key in `get_weather.py`

Configuration is managed in `config/settings.yaml`.
