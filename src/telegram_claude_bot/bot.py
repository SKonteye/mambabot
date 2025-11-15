"""
Main bot application for the Telegram Claude Bot.
Sets up and runs the Telegram bot with all handlers.
"""

import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from .config import config
from .handlers import (
    start_command,
    clear_command,
    help_command,
    screenshot_command,
    handle_message,
    error_handler
)
from .claude_manager import get_claude_manager, shutdown_claude_manager

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def post_init(application: Application):
    """
    Called after the application is initialized.

    Args:
        application: Telegram application instance
    """
    if config.use_cli:
        try:
            await get_claude_manager()
            logger.info("✓ Claude CLI initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Claude CLI: {e}")
            logger.warning("Bot will attempt to start Claude CLI on first use")


async def post_shutdown(application: Application):
    """
    Called when the application is shutting down.

    Args:
        application: Telegram application instance
    """
    if config.use_cli:
        await shutdown_claude_manager()


def main():
    """Start the bot."""
    logger.info("Starting Telegram Claude Bot...")
    logger.info(f"Mode: {'CLI' if config.use_cli else 'SDK'}")

    # Create application
    application = Application.builder().token(config.telegram_token).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("clear", clear_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("screenshot", screenshot_command))

    # Add message handlers
    application.add_handler(MessageHandler(filters.PHOTO, handle_message))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_message))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Add error handler
    application.add_error_handler(error_handler)

    # Add lifecycle hooks
    application.post_init = post_init
    application.post_shutdown = post_shutdown

    # Start the bot
    logger.info("Bot started successfully! Send /start to begin.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
