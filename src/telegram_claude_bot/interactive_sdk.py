"""
Interactive SDK handler with permission approvals via Telegram.
Handles Claude SDK queries with user approval for tool usage.
"""

import logging
from typing import List, Optional, Any
from telegram import Update
from telegram.ext import ContextTypes

from .config import config
from .permission_manager import get_permission_manager
from .handlers.permissions import send_permission_request

logger = logging.getLogger(__name__)

# Only import SDK if not using CLI mode
if not config.use_cli:
    try:
        from claude_agent_sdk import query
        from claude_agent_sdk.types import ClaudeAgentOptions
    except ImportError:
        logger.warning("Claude SDK not installed. SDK mode will not work.")


async def query_claude_with_permissions(
    prompt: str,
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> tuple[str, List[dict]]:
    """
    Query Claude using the SDK with interactive permission mode.

    This function sends tool usage requests to the user via Telegram
    for approval before executing them.

    Args:
        prompt: The prompt to send to Claude
        update: Telegram update object for sending permission requests
        context: Telegram context object

    Returns:
        Tuple of (response text, list of images)
    """
    assistant_message = ""
    images = []
    permission_manager = get_permission_manager()

    # Determine permission mode
    if config.permission_mode == 'bypass':
        # Use bypassPermissions mode to auto-approve all tool uses
        options = ClaudeAgentOptions(permission_mode='bypassPermissions')
    else:
        # Use interactive mode - we'll handle permissions manually
        options = ClaudeAgentOptions(permission_mode='ask')

    try:
        async for message in query(prompt=prompt, options=options):
            # Handle text results
            if hasattr(message, 'result') and message.result:
                assistant_message += str(message.result)

            # Handle content blocks (list format)
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
                                    images.append({'url': content.source.url})

            # Handle tool use requests in interactive mode
            elif config.permission_mode == 'interactive' and hasattr(message, 'type') and message.type == 'tool_use':
                tool_name = message.name if hasattr(message, 'name') else 'unknown'
                tool_input = str(message.input) if hasattr(message, 'input') else ''

                # Create permission request
                request_id = permission_manager.create_request(tool_name, tool_input)

                # Send permission request to user
                message_id = await send_permission_request(
                    update, context, request_id, tool_name, tool_input
                )
                permission_manager.set_message_id(request_id, message_id)

                # Wait for user approval
                approved = await permission_manager.wait_for_approval(request_id)

                if approved:
                    logger.info(f"Tool {tool_name} approved, continuing execution")
                    # The SDK will continue with the tool execution
                else:
                    logger.info(f"Tool {tool_name} denied by user")
                    # Clean up and stop processing
                    permission_manager.cleanup_request(request_id)
                    assistant_message += f"\n\n❌ Tool '{tool_name}' was denied. Stopping execution."
                    break

                permission_manager.cleanup_request(request_id)

    except Exception as e:
        logger.error(f"Error during Claude SDK query: {e}", exc_info=True)
        raise

    return assistant_message, images


async def query_claude_bypass(prompt: str) -> tuple[str, List[dict]]:
    """
    Query Claude using the SDK with bypass permissions (auto-approve).

    Args:
        prompt: The prompt to send to Claude

    Returns:
        Tuple of (response text, list of images)
    """
    assistant_message = ""
    images = []

    # Use bypassPermissions mode to auto-approve all tool uses
    options = ClaudeAgentOptions(permission_mode='bypassPermissions')

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
                                images.append({'url': content.source.url})

    return assistant_message, images
