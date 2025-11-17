# Telegram Claude Code Bot

A Telegram bot that gives you **remote access to Claude Code** running on your computer. Control your local machine through Telegram messages with full access to Claude Code's agent capabilities - **all tool permissions automatically approved**.

⚠️ **Security Warning**: This bot has unrestricted access to your computer via Claude Code. Only use it for personal use and keep your bot token private. Anyone with access to your Telegram bot can execute commands on your machine.

## What This Bot Does

- 🖥️ **Remote Computer Access**: Control Claude Code on your machine from anywhere via Telegram
- 🔓 **Permission-Free Operation**: All Claude Code tools auto-approved (file operations, bash commands, code execution)
- 📁 **Full File System Access**: Read, write, and modify files on your computer
- 💻 **Command Execution**: Run bash commands and scripts through Claude
- 🔧 **Code Operations**: Generate, debug, and refactor code with full project context
- 📸 **Screenshot Capture**: Take and analyze screenshots remotely
- 🖼️ **Image Analysis**: Send images for Claude to analyze
- 🤖 **Persistent Sessions**: Maintains conversation context across messages

## Prerequisites

- Python 3.8 or higher
- A Telegram account
- **Either:**
  - An Anthropic API key (for SDK mode), **OR**
  - Globally installed Claude CLI (for CLI mode)

## Setup Instructions

### 1. Create a Telegram Bot

1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Send `/newbot` command
3. Follow the instructions to create your bot
4. Copy the bot token provided by BotFather

### 2. Get Anthropic API Key

1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key and copy it

### 3. Install Dependencies

```bash
# Clone or navigate to the project directory
cd "Projet telegram"

# Create a virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your tokens
# TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
# ANTHROPIC_API_KEY=your_anthropic_api_key_here  (only if USE_CLAUDE_CLI=false)
# USE_CLAUDE_CLI=false  (set to 'true' to use globally installed claude command)
# PERMISSION_MODE=interactive  (set to 'bypass' for auto-approval, SDK mode only)
```

#### Choosing Between SDK and CLI Mode

**SDK Mode** (default):
- Set `USE_CLAUDE_CLI=false` in `.env`
- Requires `ANTHROPIC_API_KEY`
- Uses the Claude Agent SDK library
- Good for API-based integration
- Supports interactive permission mode (see below)

**CLI Mode**:
- Set `USE_CLAUDE_CLI=true` in `.env`
- Requires globally installed `claude` command
- Uses your system's Claude CLI installation
- Good if you already have Claude CLI configured
- To install Claude CLI, visit: https://docs.claude.com/claude-code
- Each chat gets its own persistent session directory until `/clear` is called
- Always uses bypass permissions (auto-approve all tools)

#### Permission Modes

You can choose between two permission modes:

**Interactive Mode** (SDK only - Recommended for security):
- Set `PERMISSION_MODE=interactive` in `.env`
- **Requires `USE_CLAUDE_CLI=false`** (SDK mode)
- You'll receive Telegram messages with Approve/Deny buttons when Claude wants to use tools
- Each tool usage (file operations, bash commands, etc.) requires your explicit approval
- More secure as you control what Claude can do
- Great for learning what Claude is doing behind the scenes

**Bypass Mode**:
- Set `PERMISSION_MODE=bypass` in `.env`
- All tool usage is automatically approved
- Faster workflow but requires trust in Claude's actions
- Works with both CLI and SDK modes
- **CLI mode always uses this** (technical limitation)

### 5. Run the Bot

```bash
python run_bot.py
```

You should see: `Bot started successfully! Send /start to begin.`

### 6. Use Your Bot

1. Open Telegram
2. Search for your bot by the username you created with BotFather
3. Send `/start` to begin
4. Start chatting with Claude!

## Available Commands

- `/start` - Start/restart conversation
- `/clear` - Clear conversation history
- `/help` - Show help message

## Usage Examples

Simply send messages to your bot:

- "Create a Python script to sort a list"
- "Explain how async/await works in Python"
- "Write a function to validate email addresses"
- "Help me debug this code: [paste your code]"
- "What's the best way to handle errors in Python?"

## How It Works

1. **You send a message** to your bot on Telegram from anywhere
2. **Bot forwards to Claude Code** running on your computer:
   - **SDK Mode**: Uses Claude Agent SDK
     - `PERMISSION_MODE=interactive`: You approve/deny each tool via Telegram buttons
     - `PERMISSION_MODE=bypass`: Auto-approves all tool usage
   - **CLI Mode**: Uses Claude CLI with `--permission-mode bypassPermissions`
     - Always auto-approves all tool usage (bypass only)
3. **Claude executes based on permission mode**:
   - **Interactive** (SDK only): You see approval requests for file operations, bash commands, etc.
   - **Bypass**: Everything auto-approved (reads/writes files, runs commands, takes screenshots)
4. **Response sent back** to you on Telegram
5. **Conversation context maintained** across messages

### CLI Mode Architecture

When using CLI mode (`USE_CLAUDE_CLI=true`), the bot operates as follows:

- Uses `claude --print --permission-mode bypassPermissions`
- Fast non-interactive output
- All tools auto-approved
- **Per-Chat Session Directories**: Each chat gets its own isolated session
- **Concurrent Safe**: AsyncIO lock ensures safe concurrent access
- **Clean Architecture**: Each message spawns a process that exits cleanly
- **Session Continuity**: `--continue` flag maintains conversation context across messages

### What Claude Can Do (Auto-Approved)

- ✅ Read any file on your computer
- ✅ Write/modify/delete files
- ✅ Execute bash commands
- ✅ Install packages
- ✅ Run scripts
- ✅ Access network
- ✅ Take screenshots
- ✅ Search your filesystem

## Project Structure

```
telegram-claude-bot/
├── src/
│   └── telegram_claude_bot/        # Main package
│       ├── __init__.py
│       ├── bot.py                  # Main application
│       ├── config.py               # Configuration management
│       ├── utils.py                # Utility functions
│       ├── claude_manager.py       # Claude CLI integration
│       ├── screenshot.py           # Screenshot functionality
│       ├── session.py              # Session management
│       └── handlers/               # Message handlers
│           ├── __init__.py
│           ├── commands.py         # Command handlers
│           ├── messages.py         # Message processing
│           └── errors.py           # Error handling
├── run_bot.py                      # Entry point (use this to start)
├── test_bot.py                     # Test suite
├── test_config.py                  # Configuration tests
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment template
├── .env                            # Your tokens (not in git)
├── .gitignore                      # Git exclusions
├── LICENSE                         # MIT License
└── README.md                       # This file
```

## Troubleshooting

### Bot doesn't respond
- Check that your bot is running (`python3 run_bot.py`)
- Verify your tokens are correct in `.env`
- Check the console for error messages
- Run tests: `python3 test_bot.py`

### API errors
- Ensure your Anthropic API key is valid
- Check you have sufficient API credits
- Verify internet connection

### Import errors
- Make sure virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`

## Notes

- This bot can use either the Claude Agent SDK or your globally installed Claude CLI
- In CLI mode, the bot uses **`--print` mode** for efficient communication
  - Each message spawns a `claude` process that completes and exits
  - Uses `--continue` flag to maintain session context across messages
  - Shared session directory keeps conversation history
  - AsyncIO lock serializes concurrent requests for thread safety
- Conversation history is stored in memory and will be lost when the bot restarts
- The bot keeps the last 10 message exchanges (20 messages total) for context
- Long responses are automatically split to fit Telegram's message limits
- The bot uses Claude Sonnet 4.5 model (exact model depends on your configuration)

## Security

### ⚠️ Important Security Considerations

**When using bypass permissions** (CLI mode or SDK with `PERMISSION_MODE=bypass`), **this bot has UNRESTRICTED access to your computer.** Anyone who can message your Telegram bot can:
- Read all your files
- Execute arbitrary commands
- Modify or delete data
- Install software
- Access your network

**Interactive permission mode** (SDK with `PERMISSION_MODE=interactive`) provides better security:
- You approve each tool usage via Telegram buttons
- You can deny dangerous operations
- You see exactly what Claude wants to do before it happens
- Still requires trust in your judgment for each approval

### Recommended Security Measures

1. **Use Interactive Permission Mode**:
   - Set `PERMISSION_MODE=interactive` when using SDK mode
   - Approve each tool usage individually via Telegram
   - Deny any suspicious or unexpected operations
   - Review what files/commands Claude wants to access

2. **Keep Bot Token Private**:
   - Never share your Telegram bot token
   - Never commit `.env` to version control
   - Treat it like a password to your computer

3. **Restrict Bot Access**:
   - Only use this bot for personal use
   - Consider adding Telegram username whitelist in the code
   - Don't share your bot username with others

4. **Network Security**:
   - Run on a trusted network
   - Consider using a firewall
   - Be aware of what files/data are accessible

5. **Monitor Usage**:
   - Check bot logs regularly
   - Review conversation history
   - Watch for unexpected behavior

6. **Environment Variables**:
   - Never commit `.env` file (already in `.gitignore`)
   - Keep API keys and tokens secure
   - Rotate credentials if compromised

### Use Cases

✅ **Good for**:
- Personal automation and remote access to your machine
- Coding assistance when away from your computer
- File management and quick tasks
- Screenshot monitoring
- Learning and experimentation

❌ **NOT suitable for**:
- Production environments
- Shared computers
- Processing sensitive data without additional security
- Public/multi-user scenarios

## License

MIT
