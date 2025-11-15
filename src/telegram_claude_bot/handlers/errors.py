"""
Error handler for the Telegram Claude Bot.
Handles and logs errors that occur during bot operation.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle errors that occur during bot operation.

    Args:
        update: Telegram update object
        context: Telegram context object
    """
    logger.error(f"Update {update} caused error {context.error}", exc_info=context.error)
