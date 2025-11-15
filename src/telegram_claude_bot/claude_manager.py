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
        self.session_dir: Optional[str] = None

    async def start(self):
        """Initialize session directory for Claude CLI."""
        try:
            logger.info("Initializing Claude CLI session directory...")

            # Create a persistent session directory
            self.session_dir = os.path.join(tempfile.gettempdir(), 'claude_telegram_persistent')
            os.makedirs(self.session_dir, exist_ok=True)

            logger.info(f"✓ Claude CLI session directory ready: {self.session_dir}")

        except Exception as e:
            logger.error(f"Error initializing Claude session: {e}")
            raise

    async def send_prompt(self, prompt: str, timeout: Optional[float] = None) -> str:
        """
        Send a prompt to Claude CLI using --print mode (non-interactive).

        Args:
            prompt: The prompt to send
            timeout: Maximum time to wait for response (uses config default if None)

        Returns:
            Claude's response as a string
        """
        if timeout is None:
            timeout = config.claude_timeout

        async with self.lock:
            try:
                if not self.session_dir:
                    await self.start()

                # Use --print mode for non-interactive output with --continue to maintain session
                cmd = [
                    'claude',
                    '--print',
                    '--permission-mode', 'bypassPermissions',
                    '--continue',  # Continue the most recent conversation
                    prompt
                ]

                logger.info("Sending prompt to Claude CLI (--print mode)")

                # Run claude command in the session directory
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=self.session_dir
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

    def is_alive(self) -> bool:
        """
        Check if session is initialized.

        Returns:
            True if session directory is initialized
        """
        return self.session_dir is not None


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
