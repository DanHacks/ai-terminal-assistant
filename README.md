# AI Terminal Assistant

AI Terminal Assistant is a secure, AI-powered command-line tool that converts natural language instructions into safe terminal commands.  
It validates commands, requests user confirmation, and executes them with safety controls in place.

The project is designed to work on **Termux (Android)** and later be transferred seamlessly to **Linux and Windows** systems.

---

## 🚀 Features

- Natural language to terminal command translation
- Command whitelist and blacklist for safety
- User confirmation before command execution
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
