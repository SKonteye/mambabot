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
- An Anthropic API key

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
# ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

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
2. The bot forwards your message to the Claude Agent SDK using the `query()` function
3. Claude processes your request with access to agent tools (file operations, bash commands, etc.)
4. The bot sends Claude's response back to you
5. Conversation history is maintained for context

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

- This bot uses the Claude Agent SDK which provides access to powerful agent tools
- Conversation history is stored in memory and will be lost when the bot restarts
- The bot keeps the last 10 message exchanges (20 messages total) for context
- Long responses are automatically split to fit Telegram's message limits
- The bot uses Claude Sonnet 4.5 model through the Agent SDK

## Security

- Never commit your `.env` file to version control
- Keep your bot token and API key private
- The `.gitignore` file is configured to exclude sensitive files

## License

MIT
