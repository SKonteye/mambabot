"""
Session management for the Telegram Claude Bot.
Handles conversation history and Claude CLI session directories.
"""

import os
import logging
import tempfile
import shutil
from typing import Dict, List

from .config import config

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages conversation sessions and history for users."""

    def __init__(self):
        """Initialize the session manager."""
        self.conversations: Dict[int, List[dict]] = {}
        self.claude_session_dirs: Dict[int, str] = {}

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

    def get_or_create_session_dir(self, chat_id: int) -> str:
        """
        Get or create a session directory for the Claude CLI.

        Args:
            chat_id: Telegram chat ID

        Returns:
            Path to the session directory
        """
        if chat_id in self.claude_session_dirs:
            return self.claude_session_dirs[chat_id]

        # Create a session directory for this chat
        session_dir = os.path.join(
            tempfile.gettempdir(),
            f'claude_telegram_session_{chat_id}'
        )
        os.makedirs(session_dir, exist_ok=True)

        self.claude_session_dirs[chat_id] = session_dir
        logger.info(f"Created Claude session directory for chat {chat_id}: {session_dir}")

        return session_dir

    def clear_session_dir(self, chat_id: int) -> None:
        """
        Clear the Claude CLI session directory for a chat.

        Args:
            chat_id: Telegram chat ID
        """
        if chat_id not in self.claude_session_dirs:
            return

        session_dir = self.claude_session_dirs[chat_id]

        try:
            # Remove the session directory and all its contents
            if os.path.exists(session_dir):
                shutil.rmtree(session_dir)
            logger.info(f"Cleared Claude session directory for chat {chat_id}")
        except Exception as e:
            logger.error(f"Error clearing session directory: {e}")

        del self.claude_session_dirs[chat_id]

    def clear_all(self, chat_id: int) -> None:
        """
        Clear both conversation history and session directory.

        Args:
            chat_id: Telegram chat ID
        """
        self.clear_history(chat_id)
        if config.use_cli:
            self.clear_session_dir(chat_id)


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
