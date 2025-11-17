"""
Permission approval handlers for the Telegram Claude Bot.
Handles inline button callbacks for approving/denying tool usage.
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from ..permission_manager import get_permission_manager

logger = logging.getLogger(__name__)


async def send_permission_request(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    request_id: str,
    tool_name: str,
    tool_input: str
) -> int:
    """
    Send a permission request to the user with approve/deny buttons.

    Args:
        update: Telegram update object
        context: Telegram context object
        request_id: Unique request ID
        tool_name: Name of the tool requesting permission
        tool_input: Input parameters for the tool

    Returns:
        Message ID of the sent permission request
    """
    # Truncate tool input if too long
    display_input = tool_input
    if len(tool_input) > 500:
        display_input = tool_input[:497] + "..."

    message_text = (
        f"🔐 **Permission Required**\n\n"
        f"**Tool:** `{tool_name}`\n\n"
        f"**Parameters:**\n```\n{display_input}\n```\n\n"
        f"Do you want to allow this action?"
    )

    keyboard = [
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"approve_{request_id}"),
            InlineKeyboardButton("❌ Deny", callback_data=f"deny_{request_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = await update.message.reply_text(
        message_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

    return message.message_id


async def handle_permission_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle callback queries from permission approval buttons.

    Args:
        update: Telegram update object
        context: Telegram context object
    """
    query = update.callback_query
    await query.answer()

    callback_data = query.data
    permission_manager = get_permission_manager()

    try:
        if callback_data.startswith("approve_"):
            request_id = callback_data.replace("approve_", "")
            request = permission_manager.get_request(request_id)

            if request:
                permission_manager.approve_request(request_id)
                await query.edit_message_text(
                    f"✅ **Approved**\n\n"
                    f"Tool: `{request.tool_name}`\n\n"
                    f"Executing...",
                    parse_mode='Markdown'
                )
            else:
                await query.edit_message_text("⚠️ Permission request expired or not found.")

        elif callback_data.startswith("deny_"):
            request_id = callback_data.replace("deny_", "")
            request = permission_manager.get_request(request_id)

            if request:
                permission_manager.deny_request(request_id)
                await query.edit_message_text(
                    f"❌ **Denied**\n\n"
                    f"Tool: `{request.tool_name}`\n\n"
                    f"Action cancelled.",
                    parse_mode='Markdown'
                )
            else:
                await query.edit_message_text("⚠️ Permission request expired or not found.")

    except Exception as e:
        logger.error(f"Error handling permission callback: {e}", exc_info=True)
        await query.edit_message_text(f"❌ Error processing your response: {str(e)}")
