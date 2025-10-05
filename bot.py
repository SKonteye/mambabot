#!/usr/bin/env python3
import os
import logging
import base64
import asyncio
import subprocess
import tempfile
import json
from io import BytesIO
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from claude_agent_sdk import query
from claude_agent_sdk.types import ClaudeAgentOptions, PermissionResultAllow, PermissionResultDeny
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get tokens from environment
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
USE_CLI = os.getenv('USE_CLAUDE_CLI', 'false').lower() == 'true'

if not TELEGRAM_TOKEN:
    raise ValueError('Missing required environment variable: TELEGRAM_BOT_TOKEN')

if not USE_CLI and not ANTHROPIC_API_KEY:
    raise ValueError('Missing required environment variable: ANTHROPIC_API_KEY (required when USE_CLAUDE_CLI=false)')

# Set Anthropic API key for the SDK
if not USE_CLI:
    os.environ['ANTHROPIC_API_KEY'] = ANTHROPIC_API_KEY

# Store conversation history per chat
conversations = {}

# Store Claude CLI session directories per chat
claude_session_dirs = {}

# Store pending tool approvals
pending_approvals = {}
approval_events = {}


def get_or_create_session_dir(chat_id: int) -> str:
    """
    Get or create a session directory for the Claude CLI to maintain context

    Args:
        chat_id: Telegram chat ID

    Returns:
        Path to the session directory
    """
    if chat_id in claude_session_dirs:
        return claude_session_dirs[chat_id]

    # Create a session directory for this chat
    session_dir = os.path.join(tempfile.gettempdir(), f'claude_telegram_session_{chat_id}')
    os.makedirs(session_dir, exist_ok=True)

    claude_session_dirs[chat_id] = session_dir
    logger.info(f"Created Claude session directory for chat {chat_id}: {session_dir}")

    return session_dir


async def run_claude_cli(chat_id: int, prompt: str) -> str:
    """
    Send a prompt to Claude CLI, maintaining session context per chat

    Args:
        chat_id: Telegram chat ID
        prompt: The prompt to send to Claude

    Returns:
        Claude's response as a string
    """
    try:
        # Get or create session directory for this chat
        session_dir = get_or_create_session_dir(chat_id)

        # Build the command - claude will maintain context in the session directory
        cmd = ['claude', prompt]
        env = os.environ.copy()

        logger.info(f"Running Claude CLI for chat {chat_id} in session dir: {session_dir}")

        # Run claude command in the session directory
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=session_dir,
            env=env
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode('utf-8').strip()
            logger.error(f"Claude CLI error: {error_msg}")
            return f"❌ Claude CLI error: {error_msg}"

        response = stdout.decode('utf-8').strip()
        return response

    except FileNotFoundError:
        return "❌ Claude CLI not found. Please make sure 'claude' command is installed and available in your PATH."
    except Exception as e:
        logger.error(f"Error running Claude CLI: {e}")
        return f"❌ Error: {str(e)}"


def clear_claude_session(chat_id: int):
    """Clear the Claude CLI session directory for a chat"""
    if chat_id in claude_session_dirs:
        session_dir = claude_session_dirs[chat_id]

        try:
            # Remove the session directory and all its contents
            import shutil
            if os.path.exists(session_dir):
                shutil.rmtree(session_dir)
            logger.info(f"Cleared Claude session directory for chat {chat_id}")
        except Exception as e:
            logger.error(f"Error clearing session directory: {e}")

        del claude_session_dirs[chat_id]


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    chat_id = update.effective_chat.id
    conversations[chat_id] = []

    welcome_message = (
        "👋 Welcome! I'm your Claude Code assistant.\n\n"
        "Send me any task and I'll help you with:\n"
        "• Code generation and debugging\n"
        "• File operations\n"
        "• Terminal commands\n"
        "• Project analysis\n\n"
        "Commands:\n"
        "/start - Start/restart conversation\n"
        "/clear - Clear conversation history\n"
        "/help - Show help message"
    )

    await update.message.reply_text(welcome_message)


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /clear command"""
    chat_id = update.effective_chat.id
    conversations[chat_id] = []

    # Also clear Claude CLI session if using CLI mode
    if USE_CLI:
        clear_claude_session(chat_id)

    await update.message.reply_text("🗑️ Conversation history cleared!")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_message = (
        "📚 *How to use this bot:*\n\n"
        "Simply send me a message with your task, for example:\n"
        "• \"Create a Python script to sort a list\"\n"
        "• \"Explain how async/await works\"\n"
        "• \"Write a function to validate email addresses\"\n\n"
        "*Commands:*\n"
        "/start - Start/restart conversation\n"
        "/clear - Clear conversation history\n"
        "/help - Show this help message"
    )

    await update.message.reply_text(help_message, parse_mode='Markdown')


async def process_with_file(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int, text: str, file_bytes: bytes, file_name: str, mime_type: str, history: list):
    """Process a message with a file (PDF, text, etc.)"""
    try:
        # Send typing indicator
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")

        # Try to extract text content from file
        file_content = ""

        if mime_type == 'application/pdf':
            # For PDF files, you'd need PyPDF2 or similar
            file_content = f"[PDF file: {file_name}]"
        elif mime_type and mime_type.startswith('text/'):
            # Text files
            try:
                file_content = file_bytes.decode('utf-8')
            except:
                file_content = f"[Text file: {file_name} - unable to decode]"
        else:
            file_content = f"[File: {file_name}, Type: {mime_type}]"

        # Build prompt with conversation history and file content
        if history:
            context_messages = []
            for msg in history[-10:]:
                role = msg["role"]
                content = msg["content"]
                if role == "user":
                    context_messages.append(f"User: {content}")
                else:
                    context_messages.append(f"Assistant: {content}")
            full_prompt = "\n\n".join(context_messages) + f"\n\nUser: {text}\n\nFile content:\n{file_content[:4000]}"
        else:
            full_prompt = f"{text}\n\nFile content:\n{file_content[:4000]}"

        # Use bypassPermissions mode
        options = ClaudeAgentOptions(
            permission_mode='bypassPermissions'
        )

        assistant_message = ""
        images = []

        # Send to Claude
        async for message in query(prompt=full_prompt, options=options):
            # Only process TextResult messages with actual content
            if hasattr(message, 'result') and message.result:
                assistant_message += str(message.result)
            # Check if message has content blocks (list format)
            elif hasattr(message, 'content') and isinstance(message.content, list):
                for content in message.content:
                    if hasattr(content, 'type'):
                        if content.type == 'text':
                            assistant_message += content.text
                        elif content.type == 'image':
                            # Handle image content from Claude
                            if hasattr(content, 'source'):
                                if content.source.type == 'base64':
                                    images.append({
                                        'data': content.source.data,
                                        'media_type': content.source.media_type
                                    })
                                elif content.source.type == 'url':
                                    images.append({
                                        'url': content.source.url
                                    })

        assistant_message = assistant_message.strip()

        # Add to history
        history.append({
            "role": "user",
            "content": f"[File: {file_name}] {text}"
        })
        history.append({
            "role": "assistant",
            "content": assistant_message
        })

        # Keep history manageable
        if len(history) > 20:
            history = history[-20:]
            conversations[chat_id] = history

        # Send images first if any
        for image in images:
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

        # Send response
        if assistant_message:
            chunks = split_message(assistant_message, 4000)
            for chunk in chunks:
                await update.message.reply_text(chunk)
        else:
            if not images:
                await update.message.reply_text("⚠️ No response received from Claude.")

    except Exception as e:
        logger.error(f"Error processing file: {e}")
        await update.message.reply_text(f"❌ Error processing file: {str(e)}")


async def process_with_image(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id: int, text: str, photo_base64: str, history: list):
    """Process a message with an image"""
    try:
        # Send typing indicator
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")

        # Save image temporarily so Claude can access it
        import tempfile
        temp_dir = tempfile.gettempdir()
        temp_image_path = os.path.join(temp_dir, f"telegram_image_{chat_id}.jpg")

        # Decode and save the image
        image_data = base64.b64decode(photo_base64)
        with open(temp_image_path, 'wb') as f:
            f.write(image_data)

        # Build prompt with conversation history and image reference
        if history:
            context_messages = []
            for msg in history[-10:]:
                role = msg["role"]
                content = msg["content"]
                if role == "user":
                    context_messages.append(f"User: {content}")
                else:
                    context_messages.append(f"Assistant: {content}")
            full_prompt = "\n\n".join(context_messages) + f"\n\nUser: {text}\n\nUser has sent an image saved at: {temp_image_path}\nPlease analyze this image and respond to the user's request."
        else:
            full_prompt = f"{text}\n\nUser has sent an image saved at: {temp_image_path}\nPlease analyze this image and respond to the user's request."

        # Use bypassPermissions mode
        options = ClaudeAgentOptions(
            permission_mode='bypassPermissions'
        )

        assistant_message = ""
        images = []

        # Send to Claude
        async for message in query(prompt=full_prompt, options=options):
            # Only process TextResult messages with actual content
            if hasattr(message, 'result') and message.result:
                assistant_message += str(message.result)
            # Check if message has content blocks (list format)
            elif hasattr(message, 'content') and isinstance(message.content, list):
                for content in message.content:
                    if hasattr(content, 'type'):
                        if content.type == 'text':
                            assistant_message += content.text
                        elif content.type == 'image':
                            # Handle image content from Claude
                            if hasattr(content, 'source'):
                                if content.source.type == 'base64':
                                    images.append({
                                        'data': content.source.data,
                                        'media_type': content.source.media_type
                                    })
                                elif content.source.type == 'url':
                                    images.append({
                                        'url': content.source.url
                                    })

        assistant_message = assistant_message.strip()

        # Add to history
        history.append({
            "role": "user",
            "content": f"[Image] {text}"
        })
        history.append({
            "role": "assistant",
            "content": assistant_message
        })

        # Keep history manageable
        if len(history) > 20:
            history = history[-20:]
            conversations[chat_id] = history

        # Send images first if any
        for image in images:
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

        # Send response
        if assistant_message:
            chunks = split_message(assistant_message, 4000)
            for chunk in chunks:
                await update.message.reply_text(chunk)
        else:
            if not images:
                await update.message.reply_text("⚠️ No response received from Claude.")

    except Exception as e:
        logger.error(f"Error processing image: {e}")
        await update.message.reply_text(f"❌ Error processing image: {str(e)}")


async def handle_approval_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle approval/denial button clicks"""
    query = update.callback_query
    await query.answer()

    approval_id = query.data

    if approval_id in pending_approvals:
        if query.data.startswith("approve_"):
            pending_approvals[approval_id]['approved'] = True
            await query.edit_message_text("✅ Approved! Executing action...")
        elif query.data.startswith("deny_"):
            pending_approvals[approval_id]['approved'] = False
            await query.edit_message_text("❌ Denied! Action cancelled.")

        # Trigger the event to continue execution
        if approval_id in approval_events:
            approval_events[approval_id].set()


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages"""
    chat_id = update.effective_chat.id
    text = update.message.text
    photo = update.message.photo
    document = update.message.document

    # Handle photo messages
    if photo:
        # Get the highest resolution photo
        photo_file = await photo[-1].get_file()
        photo_bytes = await photo_file.download_as_bytearray()

        # Encode to base64 for Claude
        photo_base64 = base64.b64encode(photo_bytes).decode('utf-8')

        # Get caption as text
        text = update.message.caption or "What's in this image?"

        # Initialize conversation history if needed
        if chat_id not in conversations:
            conversations[chat_id] = []

        history = conversations[chat_id]

        # Send the image to Claude with the text
        await process_with_image(update, context, chat_id, text, photo_base64, history)
        return

    # Handle document/file messages
    if document:
        file = await document.get_file()
        file_bytes = await file.download_as_bytearray()

        # Get file info
        file_name = document.file_name
        mime_type = document.mime_type

        # Get caption as text
        text = update.message.caption or f"Analyze this file: {file_name}"

        # Initialize conversation history if needed
        if chat_id not in conversations:
            conversations[chat_id] = []

        history = conversations[chat_id]

        # Check if it's an image file sent as document
        if mime_type and mime_type.startswith('image/'):
            file_base64 = base64.b64encode(file_bytes).decode('utf-8')
            await process_with_image(update, context, chat_id, text, file_base64, history)
        else:
            # Handle other file types (PDF, text, etc.)
            await process_with_file(update, context, chat_id, text, file_bytes, file_name, mime_type, history)
        return

    if not text:
        await update.message.reply_text("❌ Please send a text message, image, or file.")
        return

    # Initialize conversation history if needed
    if chat_id not in conversations:
        conversations[chat_id] = []

    history = conversations[chat_id]

    # Permission callback for tool approvals
    async def can_use_tool_callback(tool_name: str, tool_input: dict, context_info):
        """Request user approval before using tools"""
        import time
        approval_id = f"approve_{chat_id}_{int(time.time() * 1000)}"
        deny_id = f"deny_{chat_id}_{int(time.time() * 1000)}"

        # Format tool details
        input_preview = str(tool_input)[:400]
        if len(str(tool_input)) > 400:
            input_preview += "..."

        approval_text = (
            f"🔐 **Permission Required**\n\n"
            f"**Tool:** `{tool_name}`\n\n"
            f"**Details:**\n`{input_preview}`\n\n"
            f"Approve this action?"
        )

        keyboard = [
            [
                InlineKeyboardButton("✅ Approve", callback_data=approval_id),
                InlineKeyboardButton("❌ Deny", callback_data=deny_id)
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Create event for async waiting
        event = asyncio.Event()
        approval_events[approval_id] = event
        approval_events[deny_id] = event
        pending_approvals[approval_id] = {'approved': None}
        pending_approvals[deny_id] = {'approved': None}

        # Send approval request
        await update.message.reply_text(approval_text, reply_markup=reply_markup, parse_mode='Markdown')

        # Wait for user response (5 min timeout)
        try:
            await asyncio.wait_for(event.wait(), timeout=300)
        except asyncio.TimeoutError:
            await update.message.reply_text("⏱️ Approval timeout. Action denied.")
            # Cleanup
            for aid in [approval_id, deny_id]:
                pending_approvals.pop(aid, None)
                approval_events.pop(aid, None)
            return PermissionResultDeny(message="Timeout")

        # Check which button was clicked
        approved = pending_approvals.get(approval_id, {}).get('approved', False)

        # Cleanup
        for aid in [approval_id, deny_id]:
            pending_approvals.pop(aid, None)
            approval_events.pop(aid, None)

        if approved:
            return PermissionResultAllow()
        else:
            return PermissionResultDeny(message="User denied permission")

    try:
        # Send typing indicator
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")

        # Build the prompt with conversation history
        if history:
            # Format previous conversation for context
            context_messages = []
            for msg in history[-10:]:  # Last 5 exchanges (10 messages)
                role = msg["role"]
                content = msg["content"]
                if role == "user":
                    context_messages.append(f"User: {content}")
                else:
                    context_messages.append(f"Assistant: {content}")

            prompt = "\n\n".join(context_messages) + f"\n\nUser: {text}"
        else:
            prompt = text

        assistant_message = ""
        images = []

        # Choose between CLI and SDK based on configuration
        if USE_CLI:
            # Use globally installed Claude CLI with persistent session
            logger.info("Using Claude CLI mode")
            assistant_message = await run_claude_cli(chat_id, prompt)
        else:
            # Use SDK (original behavior)
            logger.info("Using Claude SDK mode")

            # Use bypassPermissions mode to auto-approve all tool uses
            options = ClaudeAgentOptions(
                permission_mode='bypassPermissions'  # Auto-approve all tools
            )

            async for message in query(prompt=prompt, options=options):
                # Only process TextResult messages with actual content
                if hasattr(message, 'result') and message.result:
                    assistant_message += str(message.result)
                # Check if message has content blocks (list format)
                elif hasattr(message, 'content') and isinstance(message.content, list):
                    for content in message.content:
                        if hasattr(content, 'type'):
                            if content.type == 'text':
                                assistant_message += content.text
                            elif content.type == 'image':
                                # Handle image content
                                if hasattr(content, 'source'):
                                    if content.source.type == 'base64':
                                        images.append({
                                            'data': content.source.data,
                                            'media_type': content.source.media_type
                                        })
                                    elif content.source.type == 'url':
                                        images.append({
                                            'url': content.source.url
                                        })
                # Skip system messages and metadata

        assistant_message = assistant_message.strip()

        # Add messages to history
        history.append({
            "role": "user",
            "content": text
        })
        history.append({
            "role": "assistant",
            "content": assistant_message
        })

        # Keep conversation history manageable (last 10 exchanges = 20 messages)
        if len(history) > 20:
            history = history[-20:]
            conversations[chat_id] = history

        # Send images first if any
        for image in images:
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

        # Send response to user
        if assistant_message:
            # Split long messages (Telegram limit is 4096 characters)
            chunks = split_message(assistant_message, 4000)
            for chunk in chunks:
                try:
                    await update.message.reply_text(chunk)
                except Exception as send_error:
                    logger.error(f"Error sending chunk: {send_error}")
                    # If chunk is still too long, split it further by characters
                    for i in range(0, len(chunk), 4000):
                        await update.message.reply_text(chunk[i:i+4000])
        else:
            if not images:
                await update.message.reply_text("⚠️ No text response received from Claude.")

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        await update.message.reply_text(
            f"❌ An error occurred while processing your request.\n"
            f"Error: {str(e)}"
        )


def split_message(text: str, max_length: int = 4000) -> list[str]:
    """Split long messages into chunks"""
    if len(text) <= max_length:
        return [text]

    chunks = []
    current_chunk = ""

    lines = text.split('\n')

    for line in lines:
        if len(current_chunk) + len(line) + 1 > max_length:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = line + '\n'
        else:
            current_chunk += line + '\n'

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")


def main():
    """Start the bot"""
    # Create application
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("clear", clear_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(handle_approval_callback))
    application.add_handler(MessageHandler(filters.PHOTO, handle_message))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_message))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Add error handler
    application.add_error_handler(error_handler)

    # Start the bot
    logger.info("Bot started successfully! Send /start to begin.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
