"""
Message handlers for the Telegram Claude Bot.
Handles text messages, images, and documents.
"""

import os
import base64
import logging
import tempfile
from io import BytesIO

from telegram import Update
from telegram.ext import ContextTypes

from ..config import config, ERROR_MESSAGES
from ..session import get_session_manager
from ..utils import split_message, extract_image_paths, send_image_from_path, format_context_messages
from ..claude_manager import get_claude_manager
from ..interactive_sdk import query_claude_with_permissions, query_claude_bypass

logger = logging.getLogger(__name__)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle incoming messages (text, images, documents).

    Args:
        update: Telegram update object
        context: Telegram context object
    """
    chat_id = update.effective_chat.id
    text = update.message.text
    photo = update.message.photo
    document = update.message.document

    # Handle photo messages
    if photo:
        await _handle_photo_message(update, context, chat_id, photo)
        return

    # Handle document/file messages
    if document:
        await _handle_document_message(update, context, chat_id, document)
        return

    # Handle text messages
    if not text:
        await update.message.reply_text("❌ Please send a text message, image, or file.")
        return

    await _handle_text_message(update, context, chat_id, text)


async def _handle_text_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    text: str
):
    """
    Handle text messages.

    Args:
        update: Telegram update object
        context: Telegram context object
        chat_id: Telegram chat ID
        text: Message text
    """
    try:
        # Send typing indicator
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")

        session_manager = get_session_manager()
        history = session_manager.get_history(chat_id)

        assistant_message = ""
        images = []

        # Choose between CLI and SDK based on configuration
        if config.use_cli:
            # Use Claude CLI (always bypass mode)
            # CLI handles conversation history internally via --continue flag
            logger.info("Using Claude CLI mode with bypass permissions")
            claude_manager = await get_claude_manager()
            assistant_message = await claude_manager.send_prompt(text, chat_id)
        else:
            # Use SDK with permission mode
            # SDK should receive structured messages, not text-prepended history
            if config.permission_mode == 'interactive':
                logger.info("Using Claude SDK mode with interactive permissions")
                assistant_message, images = await query_claude_with_permissions(text, history, update, context)
            else:
                logger.info("Using Claude SDK mode with bypass permissions")
                assistant_message, images = await query_claude_bypass(text, history)

        assistant_message = assistant_message.strip()

        # Add messages to history
        session_manager.add_message(chat_id, "user", text)
        session_manager.add_message(chat_id, "assistant", assistant_message)

        # Send images first if any (from Claude's base64/URL responses)
        for image in images:
            await _send_image(update, image)

        # Extract and send any image file paths mentioned by Claude
        if assistant_message:
            image_paths = extract_image_paths(assistant_message)
            for img_path in image_paths:
                try:
                    await send_image_from_path(update, context, img_path)
                except Exception as img_error:
                    logger.error(f"Error auto-sending image {img_path}: {img_error}")

        # Send response to user
        if assistant_message:
            await _send_text_chunks(update, assistant_message)
        else:
            if not images:
                await update.message.reply_text(ERROR_MESSAGES['no_text_response'])

    except Exception as e:
        logger.error(f"Error processing text message: {e}", exc_info=True)
        await update.message.reply_text(
            f"❌ An error occurred while processing your request.\n"
            f"Error: {str(e)}"
        )


async def _handle_photo_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    photo
):
    """
    Handle photo messages.

    Args:
        update: Telegram update object
        context: Telegram context object
        chat_id: Telegram chat ID
        photo: Telegram photo object
    """
    try:
        # Get the highest resolution photo
        photo_file = await photo[-1].get_file()
        photo_bytes = await photo_file.download_as_bytearray()

        # Encode to base64 for Claude
        photo_base64 = base64.b64encode(photo_bytes).decode('utf-8')

        # Get caption as text
        text = update.message.caption or "What's in this image?"

        await _process_with_image(update, context, chat_id, text, photo_base64)

    except Exception as e:
        logger.error(f"Error processing photo: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Error processing image: {str(e)}")


async def _handle_document_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    document
):
    """
    Handle document/file messages.

    Args:
        update: Telegram update object
        context: Telegram context object
        chat_id: Telegram chat ID
        document: Telegram document object
    """
    try:
        file = await document.get_file()
        file_bytes = await file.download_as_bytearray()

        # Get file info
        file_name = document.file_name
        mime_type = document.mime_type

        # Get caption as text
        text = update.message.caption or f"Analyze this file: {file_name}"

        # Check if it's an image file sent as document
        if mime_type and mime_type.startswith('image/'):
            file_base64 = base64.b64encode(file_bytes).decode('utf-8')
            await _process_with_image(update, context, chat_id, text, file_base64)
        else:
            # Handle other file types (PDF, text, etc.)
            await _process_with_file(update, context, chat_id, text, file_bytes, file_name, mime_type)

    except Exception as e:
        logger.error(f"Error processing document: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Error processing file: {str(e)}")


async def _process_with_image(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    text: str,
    photo_base64: str
):
    """
    Process a message with an image.

    Args:
        update: Telegram update object
        context: Telegram context object
        chat_id: Telegram chat ID
        text: Message text
        photo_base64: Base64-encoded image data
    """
    try:
        # Send typing indicator
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")

        # Save image temporarily so Claude can access it
        temp_dir = tempfile.gettempdir()
        temp_image_path = os.path.join(temp_dir, f"telegram_image_{chat_id}.jpg")

        # Decode and save the image
        image_data = base64.b64decode(photo_base64)
        with open(temp_image_path, 'wb') as f:
            f.write(image_data)

        session_manager = get_session_manager()
        history = session_manager.get_history(chat_id)

        # Build prompt with image reference
        full_prompt = (
            f"{text}\n\n"
            f"User has sent an image saved at: {temp_image_path}\n"
            f"Please analyze this image and respond to the user's request."
        )

        assistant_message = ""
        images = []

        # Choose between CLI and SDK based on configuration
        if config.use_cli:
            # Use Claude CLI (always bypass mode)
            # CLI handles conversation history internally via --continue flag
            logger.info("Using Claude CLI mode for image processing with bypass permissions")
            claude_manager = await get_claude_manager()
            assistant_message = await claude_manager.send_prompt(full_prompt, chat_id)
        else:
            # Use SDK with permission mode
            # SDK should receive structured messages, not text-prepended history
            if config.permission_mode == 'interactive':
                logger.info("Using Claude SDK mode for image processing with interactive permissions")
                assistant_message, images = await query_claude_with_permissions(full_prompt, history, update, context)
            else:
                logger.info("Using Claude SDK mode for image processing with bypass permissions")
                assistant_message, images = await query_claude_bypass(full_prompt, history)

        assistant_message = assistant_message.strip()

        # Add to history
        session_manager.add_message(chat_id, "user", f"[Image] {text}")
        session_manager.add_message(chat_id, "assistant", assistant_message)

        # Send images first if any
        for image in images:
            await _send_image(update, image)

        # Send response
        if assistant_message:
            await _send_text_chunks(update, assistant_message)
        else:
            if not images:
                await update.message.reply_text(ERROR_MESSAGES['no_response'])

    except Exception as e:
        logger.error(f"Error processing image: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Error processing image: {str(e)}")


async def _process_with_file(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    text: str,
    file_bytes: bytes,
    file_name: str,
    mime_type: str
):
    """
    Process a message with a file (PDF, text, etc.).

    Args:
        update: Telegram update object
        context: Telegram context object
        chat_id: Telegram chat ID
        text: Message text
        file_bytes: File content as bytes
        file_name: Name of the file
        mime_type: MIME type of the file
    """
    try:
        # Send typing indicator
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")

        # Try to extract text content from file
        file_content = ""

        if mime_type == 'application/pdf':
            file_content = f"[PDF file: {file_name}]"
        elif mime_type and mime_type.startswith('text/'):
            # Text files
            try:
                file_content = file_bytes.decode('utf-8')
            except:
                file_content = f"[Text file: {file_name} - unable to decode]"
        else:
            file_content = f"[File: {file_name}, Type: {mime_type}]"

        session_manager = get_session_manager()
        history = session_manager.get_history(chat_id)

        # Build prompt with file content
        full_prompt = f"{text}\n\nFile content:\n{file_content[:4000]}"

        assistant_message = ""
        images = []

        # Choose between CLI and SDK based on configuration
        if config.use_cli:
            # Use Claude CLI (always bypass mode)
            # CLI handles conversation history internally via --continue flag
            logger.info("Using Claude CLI mode for file processing with bypass permissions")
            claude_manager = await get_claude_manager()
            assistant_message = await claude_manager.send_prompt(full_prompt, chat_id)
        else:
            # Use SDK with permission mode
            # SDK should receive structured messages, not text-prepended history
            if config.permission_mode == 'interactive':
                logger.info("Using Claude SDK mode for file processing with interactive permissions")
                assistant_message, images = await query_claude_with_permissions(full_prompt, history, update, context)
            else:
                logger.info("Using Claude SDK mode for file processing with bypass permissions")
                assistant_message, images = await query_claude_bypass(full_prompt, history)

        assistant_message = assistant_message.strip()

        # Add to history
        session_manager.add_message(chat_id, "user", f"[File: {file_name}] {text}")
        session_manager.add_message(chat_id, "assistant", assistant_message)

        # Send images first if any
        for image in images:
            await _send_image(update, image)

        # Send response
        if assistant_message:
            await _send_text_chunks(update, assistant_message)
        else:
            if not images:
                await update.message.reply_text(ERROR_MESSAGES['no_response'])

    except Exception as e:
        logger.error(f"Error processing file: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Error processing file: {str(e)}")




async def _send_image(update: Update, image: dict):
    """
    Send an image to Telegram.

    Args:
        update: Telegram update object
        image: Image dictionary with either 'data' or 'url'
    """
    try:
        if 'data' in image:
            # Base64 encoded image
            image_data = base64.b64decode(image['data'])
            photo = BytesIO(image_data)
            photo.name = f"image.{image['media_type'].split('/')[-1]}"
            await update.message.reply_photo(photo=photo)
        elif 'url' in image:
            # URL image
            await update.message.reply_photo(photo=image['url'])
    except Exception as img_error:
        logger.error(f"Error sending image: {img_error}")


async def _send_text_chunks(update: Update, text: str):
    """
    Send text message in chunks if it's too long.

    Args:
        update: Telegram update object
        text: Text to send
    """
    chunks = split_message(text, config.max_message_length)
    for chunk in chunks:
        try:
            await update.message.reply_text(chunk)
        except Exception as send_error:
            logger.error(f"Error sending chunk: {send_error}")
            # If chunk is still too long, split it further by characters
            for i in range(0, len(chunk), config.max_message_length):
                await update.message.reply_text(chunk[i:i+config.max_message_length])
