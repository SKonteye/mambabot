"""
Command handlers for the Telegram Claude Bot.
Handles /start, /clear, /help, and /screenshot commands.
"""

import os
import logging
from telegram import Update
from telegram.ext import ContextTypes

from ..config import WELCOME_MESSAGE, HELP_MESSAGE
from ..session import get_session_manager
from ..screenshot import capture_screenshot, get_screenshot_error_message

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /start command.

    Args:
        update: Telegram update object
        context: Telegram context object
    """
    chat_id = update.effective_chat.id
    session_manager = get_session_manager()
    session_manager.clear_history(chat_id)

    await update.message.reply_text(WELCOME_MESSAGE)
    logger.info(f"Started new conversation for chat {chat_id}")


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /clear command.

    Args:
        update: Telegram update object
        context: Telegram context object
    """
    chat_id = update.effective_chat.id
    session_manager = get_session_manager()
    await session_manager.clear_all(chat_id)

    await update.message.reply_text("🗑️ Conversation history cleared!")
    logger.info(f"Cleared conversation history for chat {chat_id}")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /help command.

    Args:
        update: Telegram update object
        context: Telegram context object
    """
    await update.message.reply_text(HELP_MESSAGE, parse_mode='Markdown')


async def screenshot_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /screenshot command - capture and send a screenshot.

    Args:
        update: Telegram update object
        context: Telegram context object
    """
    chat_id = update.effective_chat.id

    try:
        await update.message.reply_text("📸 Taking screenshot...")
        await context.bot.send_chat_action(chat_id=chat_id, action="upload_photo")

        # Capture screenshot
        screenshot_path = await capture_screenshot(chat_id)

        if screenshot_path and os.path.exists(screenshot_path):
            # Send the screenshot to Telegram
            with open(screenshot_path, 'rb') as photo_file:
                await update.message.reply_photo(
                    photo=photo_file,
                    caption="📸 Screenshot captured"
                )

            # Clean up the temporary file
            os.remove(screenshot_path)
            logger.info(f"Screenshot sent successfully to chat {chat_id}")
        else:
            await update.message.reply_text(get_screenshot_error_message())

    except Exception as e:
        logger.error(f"Error in screenshot command: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Error capturing screenshot: {str(e)}")
