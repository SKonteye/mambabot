# Telegram Claude Agent Bot

A Telegram bot that connects to Claude Code Agent SDK to help you with coding tasks, directly from Telegram.

## Features

- 💬 Natural conversation with Claude AI
- 🔧 Code generation and debugging
- 📝 File operations and project analysis
- 🛠️ Access to Claude Code agent tools
- 🤖 Context-aware responses
- 📜 Conversation history management

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
```

#### Choosing Between SDK and CLI Mode

**SDK Mode** (default):
- Set `USE_CLAUDE_CLI=false` in `.env`
- Requires `ANTHROPIC_API_KEY`
- Uses the Claude Agent SDK library
- Good for API-based integration

**CLI Mode**:
- Set `USE_CLAUDE_CLI=true` in `.env`
- Requires globally installed `claude` command
- Uses your system's Claude CLI installation
- Good if you already have Claude CLI configured
- To install Claude CLI, visit: https://docs.claude.com/claude-code
- Automatically uses `--permission-mode bypassPermissions` to auto-approve all tool usage
- Each chat gets its own persistent session directory until `/clear` is called

### 5. Run the Bot

```bash
python bot.py
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

1. You send a message to the bot on Telegram
2. The bot forwards your message to Claude:
   - **SDK Mode**: Uses the Claude Agent SDK `query()` function
   - **CLI Mode**: Sends messages to a persistent Claude CLI process via stdin/stdout pipes
3. Claude processes your request with access to agent tools (file operations, bash commands, etc.)
4. The bot sends Claude's response back to you
5. Conversation history is maintained for context

### CLI Mode Architecture

When using CLI mode (`USE_CLAUDE_CLI=true`), the bot uses Claude CLI's `--print` mode for efficient non-interactive communication:

- **Print Mode**: Uses `claude --print --continue` for non-interactive output
- **Session Continuity**: `--continue` flag maintains conversation context across messages
- **Shared Session Directory**: All messages use the same session directory for context persistence
- **Concurrent Handling**: AsyncIO lock ensures safe concurrent access from multiple users
- **Auto-approval**: `--permission-mode bypassPermissions` auto-approves all tool usage
- **Clean Architecture**: No persistent process to manage - each message spawns a process that exits cleanly

## Project Structure

```
Projet telegram/
├── bot.py              # Main bot application
├── requirements.txt    # Python dependencies
├── .env.example       # Environment variables template
├── .env               # Your actual environment variables (not in git)
├── .gitignore         # Git ignore file
└── README.md          # This file
```

## Troubleshooting

### Bot doesn't respond
- Check that your bot is running (`python bot.py`)
- Verify your tokens are correct in `.env`
- Check the console for error messages

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

- Never commit your `.env` file to version control
- Keep your bot token and API key private
- The `.gitignore` file is configured to exclude sensitive files

## License

MIT
