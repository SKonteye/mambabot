"""
Claude CLI process management for the Telegram Claude Bot.
Handles communication with Claude CLI using --print mode.
"""

import os
import logging
import asyncio
import tempfile
from typing import Optional

from .config import config, ERROR_MESSAGES

logger = logging.getLogger(__name__)


class ClaudeProcessManager:
    """Manages persistent Claude CLI processes using --print mode for non-interactive communication."""

    def __init__(self):
        """Initialize the Claude process manager."""
        self.lock = asyncio.Lock()
        # Track session directories per chat_id
        self.session_dirs: dict[int, str] = {}

    def _get_session_dir(self, chat_id: int) -> str:
        """
        Get or create session directory for a specific chat.

        Args:
            chat_id: Telegram chat ID

        Returns:
            Path to the session directory
        """
        if chat_id not in self.session_dirs:
            # Create a persistent session directory for this chat
            session_dir = os.path.join(
                tempfile.gettempdir(),
                f'claude_telegram_chat_{chat_id}'
            )
            os.makedirs(session_dir, exist_ok=True)
            self.session_dirs[chat_id] = session_dir
            logger.info(f"✓ Created Claude CLI session directory for chat {chat_id}: {session_dir}")

        return self.session_dirs[chat_id]

    async def start(self):
        """Initialize the Claude process manager."""
        try:
            logger.info("Claude CLI process manager initialized")
        except Exception as e:
            logger.error(f"Error initializing Claude process manager: {e}")
            raise

    async def send_prompt(self, prompt: str, chat_id: int, timeout: Optional[float] = None) -> str:
        """
        Send a prompt to Claude CLI using --print mode (non-interactive).

        Args:
            prompt: The prompt to send
            chat_id: Telegram chat ID for session isolation
            timeout: Maximum time to wait for response (uses config default if None)

        Returns:
            Claude's response as a string
        """
        if timeout is None:
            timeout = config.claude_timeout

        async with self.lock:
            try:
                # Get the session directory for this specific chat
                session_dir = self._get_session_dir(chat_id)

                # Use --print mode for non-interactive output with --continue to maintain session
                # Use permission mode from config
                permission_arg = 'bypassPermissions' if config.permission_mode == 'bypass' else 'default'
                cmd = [
                    'claude',
                    '--print',
                    '--permission-mode', permission_arg,
                    '--continue',  # Continue the most recent conversation
                    prompt
                ]

                logger.info(f"Sending prompt to Claude CLI (--print mode) for chat {chat_id}")

                # Run claude command in the session directory
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=session_dir
                )

                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(),
                        timeout=timeout
                    )
                except asyncio.TimeoutError:
                    logger.error("Timeout waiting for Claude response")
                    process.kill()
                    await process.wait()
                    return ERROR_MESSAGES['timeout']

                if process.returncode != 0:
                    error_msg = stderr.decode('utf-8').strip()
                    logger.error(f"Claude CLI error: {error_msg}")
                    return f"❌ Claude CLI error: {error_msg}"

                response = stdout.decode('utf-8').strip()
                return response if response else ERROR_MESSAGES['no_response']

            except FileNotFoundError:
                return ERROR_MESSAGES['claude_cli_not_found']
            except Exception as e:
                logger.error(f"Error communicating with Claude: {e}", exc_info=True)
                return f"❌ Error: {str(e)}"

    async def stop(self):
        """Cleanup session directory."""
        logger.info("Claude CLI session cleanup (no persistent process to stop)")

    def clear_chat_session(self, chat_id: int) -> None:
        """
        Clear the session directory for a specific chat.

        Args:
            chat_id: Telegram chat ID
        """
        import shutil

        if chat_id in self.session_dirs:
            session_dir = self.session_dirs[chat_id]
            try:
                if os.path.exists(session_dir):
                    shutil.rmtree(session_dir)
                    logger.info(f"✓ Cleared Claude CLI session for chat {chat_id}")
            except Exception as e:
                logger.error(f"Error clearing session for chat {chat_id}: {e}")

            # Remove from tracking
            del self.session_dirs[chat_id]

    def is_alive(self) -> bool:
        """
        Check if process manager is initialized.

        Returns:
            True (manager is always ready)
        """
        return True


# Global Claude process manager instance
_claude_process_manager: Optional[ClaudeProcessManager] = None


async def get_claude_manager() -> ClaudeProcessManager:
    """
    Get the global Claude process manager instance.

    Returns:
        ClaudeProcessManager instance
    """
    global _claude_process_manager

    if _claude_process_manager is None:
        _claude_process_manager = ClaudeProcessManager()
        await _claude_process_manager.start()

    # Check if process is alive, restart if needed
    if not _claude_process_manager.is_alive():
        logger.warning("Claude process died, restarting...")
        await _claude_process_manager.start()

    return _claude_process_manager


async def shutdown_claude_manager():
    """Shutdown the global Claude process manager."""
    global _claude_process_manager

    if _claude_process_manager:
        logger.info("Shutting down Claude CLI process...")
        await _claude_process_manager.stop()
        logger.info("✓ Claude CLI process stopped")
        _claude_process_manager = None
