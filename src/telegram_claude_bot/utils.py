"""
Utility functions for the Telegram Claude Bot.
Contains reusable functions for message processing, image handling, etc.
"""

import os
import re
import logging
from typing import List
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


def split_message(text: str, max_length: int = 4000) -> List[str]:
    """
    Split long messages into chunks that fit Telegram's message size limit.

    Args:
        text: The text to split
        max_length: Maximum length per chunk (default: 4000)

    Returns:
        List of message chunks
    """
    if len(text) <= max_length:
        return [text]

    chunks = []
    current_chunk = ""

    lines = text.split('\n')

    for line in lines:
        # If a single line is longer than max_length, split it by characters
        if len(line) > max_length:
            # First, add any current chunk
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""

            # Split the long line into character chunks
            for i in range(0, len(line), max_length):
                chunks.append(line[i:i + max_length])
        elif len(current_chunk) + len(line) + 1 > max_length:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = line + '\n'
        else:
            current_chunk += line + '\n'

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


def extract_image_paths(text: str) -> List[str]:
    """
    Extract potential image file paths from text.

    Args:
        text: The text to search for image paths

    Returns:
        List of image file paths found
    """
    # Pattern to match common image paths
    patterns = [
        r'(?:image|screenshot|photo|picture|saved|created|written|at|to)\s+(?:at|to|in)?\s*[:\s]*([~/\w\-./]+\.(?:png|jpg|jpeg|gif|bmp|webp|svg))',
        r'([~/\w\-./]+\.(?:png|jpg|jpeg|gif|bmp|webp|svg))',
        r'\[([^\]]+\.(?:png|jpg|jpeg|gif|bmp|webp|svg))\]',
        r'`([^`]+\.(?:png|jpg|jpeg|gif|bmp|webp|svg))`',
    ]

    found_paths = []
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            path = match.group(1) if match.lastindex >= 1 else match.group(0)
            path = path.strip()
            if path and path not in found_paths:
                found_paths.append(path)

    return found_paths


async def send_image_from_path(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    image_path: str,
    caption: str = None
) -> bool:
    """
    Helper function to send an image from a file path to Telegram.

    Args:
        update: Telegram update object
        context: Telegram context object
        image_path: Path to the image file
        caption: Optional caption for the image

    Returns:
        True if image was sent successfully, False otherwise
    """
    try:
        # Expand user path if needed
        image_path = os.path.expanduser(image_path)

        if not os.path.exists(image_path):
            logger.debug(f"Image path not found: {image_path}")
            return False

        # Check if it's an image file
        valid_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')
        if not image_path.lower().endswith(valid_extensions):
            logger.debug(f"Not a valid image file: {image_path}")
            return False

        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action="upload_photo"
        )

        # Send the image
        with open(image_path, 'rb') as photo_file:
            await update.message.reply_photo(
                photo=photo_file,
                caption=caption or f"📷 {os.path.basename(image_path)}"
            )

        logger.info(f"Image sent successfully: {image_path}")
        return True

    except Exception as e:
        logger.error(f"Error sending image {image_path}: {e}")
        return False


def format_context_messages(history: list, max_exchanges: int = 10) -> str:
    """
    Format conversation history for context.

    Args:
        history: List of message dictionaries with 'role' and 'content'
        max_exchanges: Maximum number of message exchanges to include

    Returns:
        Formatted context string
    """
    if not history:
        return ""

    context_messages = []
    for msg in history[-max_exchanges * 2:]:  # 2 messages per exchange
        role = msg["role"]
        content = msg["content"]
        if role == "user":
            context_messages.append(f"User: {content}")
        else:
            context_messages.append(f"Assistant: {content}")

    return "\n\n".join(context_messages)
