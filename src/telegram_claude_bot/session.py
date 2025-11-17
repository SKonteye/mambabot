"""
Session management for the Telegram Claude Bot.
Handles conversation history for chats.
"""

import logging
from typing import Dict, List

from .config import config

logger = logging.getLogger(__name__)


async def _get_claude_manager_if_cli():
    """Get Claude manager if in CLI mode, otherwise return None."""
    if config.use_cli:
        from .claude_manager import get_claude_manager
        return await get_claude_manager()
    return None


class SessionManager:
    """Manages conversation sessions and history for users."""

    def __init__(self):
        """Initialize the session manager."""
        self.conversations: Dict[int, List[dict]] = {}

    def get_history(self, chat_id: int) -> List[dict]:
        """
        Get conversation history for a chat.

        Args:
            chat_id: Telegram chat ID

        Returns:
            List of message dictionaries
        """
        if chat_id not in self.conversations:
            self.conversations[chat_id] = []
        return self.conversations[chat_id]

    def add_message(self, chat_id: int, role: str, content: str) -> None:
        """
        Add a message to conversation history.

        Args:
            chat_id: Telegram chat ID
            role: Message role ('user' or 'assistant')
            content: Message content
        """
        history = self.get_history(chat_id)
        history.append({
            "role": role,
            "content": content
        })

        # Keep history manageable
        if len(history) > config.max_history_length:
            self.conversations[chat_id] = history[-config.max_history_length:]

    def clear_history(self, chat_id: int) -> None:
        """
        Clear conversation history for a chat.

        Args:
            chat_id: Telegram chat ID
        """
        self.conversations[chat_id] = []
        logger.info(f"Cleared conversation history for chat {chat_id}")

    async def clear_all(self, chat_id: int) -> None:
        """
        Clear both conversation history and session directory.

        Args:
            chat_id: Telegram chat ID
        """
        self.clear_history(chat_id)
        if config.use_cli:
            # Use the claude_manager's clear method instead of local session dir
            claude_manager = await _get_claude_manager_if_cli()
            if claude_manager:
                claude_manager.clear_chat_session(chat_id)


# Global session manager instance
_session_manager = None


def get_session_manager() -> SessionManager:
    """
    Get the global session manager instance.

    Returns:
        SessionManager instance
    """
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
