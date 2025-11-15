"""
Configuration module for Telegram Claude Bot.
Centralizes all configuration settings and environment variable management.
"""

import os
import logging
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


@dataclass
class BotConfig:
    """Bot configuration class."""

    telegram_token: str
    anthropic_api_key: Optional[str]
    use_cli: bool
    max_history_length: int = 20
    max_message_length: int = 4000
    claude_timeout: float = 300.0

    @classmethod
    def from_env(cls) -> 'BotConfig':
        """
        Create configuration from environment variables.

        Returns:
            BotConfig instance

        Raises:
            ValueError: If required environment variables are missing
        """
        telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not telegram_token:
            raise ValueError('Missing required environment variable: TELEGRAM_BOT_TOKEN')

        use_cli = os.getenv('USE_CLAUDE_CLI', 'false').lower() == 'true'
        anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')

        if not use_cli and not anthropic_api_key:
            raise ValueError(
                'Missing required environment variable: ANTHROPIC_API_KEY '
                '(required when USE_CLAUDE_CLI=false)'
            )

        # Set API key in environment if using SDK
        if not use_cli and anthropic_api_key:
            os.environ['ANTHROPIC_API_KEY'] = anthropic_api_key

        logger.info(f"Configuration loaded - Mode: {'CLI' if use_cli else 'SDK'}")

        return cls(
            telegram_token=telegram_token,
            anthropic_api_key=anthropic_api_key,
            use_cli=use_cli
        )


# Global configuration instance
config = BotConfig.from_env()


# Error messages
ERROR_MESSAGES = {
    'claude_cli_not_found': (
        "❌ Claude CLI not found. Please make sure 'claude' command is installed "
        "and available in your PATH."
    ),
    'timeout': "❌ Timeout: Claude took too long to respond. Please try again.",
    'no_response': "⚠️ No response received from Claude.",
    'no_text_response': "⚠️ No text response received from Claude.",
}


# Welcome message
WELCOME_MESSAGE = (
    "👋 Welcome! I'm your Claude Code assistant.\n\n"
    "Send me any task and I'll help you with:\n"
    "• Code generation and debugging\n"
    "• File operations\n"
    "• Terminal commands\n"
    "• Project analysis\n"
    "• Screenshot capture\n"
    "• Automatic image sending from your computer\n\n"
    "Commands:\n"
    "/start - Start/restart conversation\n"
    "/clear - Clear conversation history\n"
    "/screenshot - Capture and send a screenshot\n"
    "/help - Show help message\n\n"
    "💡 Tip: I can automatically send images when I mention file paths!"
)


# Help message
HELP_MESSAGE = (
    "📚 *How to use this bot:*\n\n"
    "Simply send me a message with your task, for example:\n"
    "• \"Create a Python script to sort a list\"\n"
    "• \"Explain how async/await works\"\n"
    "• \"Take a screenshot and show me\"\n"
    "• \"Send me the image at ~/Pictures/photo.png\"\n\n"
    "*Commands:*\n"
    "/start - Start/restart conversation\n"
    "/clear - Clear conversation history\n"
    "/screenshot - Capture and send a screenshot\n"
    "/help - Show this help message\n\n"
    "*Image Features:*\n"
    "🖼️ I automatically detect and send images that I mention in my responses!\n"
    "📸 Just ask me to find, create, or take screenshots and I'll send them to you."
)
