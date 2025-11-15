"""
Screenshot capture functionality for the Telegram Claude Bot.
Supports macOS, Linux, and Windows platforms.
"""

import os
import sys
import logging
import asyncio
import tempfile
from typing import Optional

logger = logging.getLogger(__name__)


async def capture_screenshot(chat_id: int) -> Optional[str]:
    """
    Capture a screenshot and save it to a temporary file.

    Args:
        chat_id: Telegram chat ID (used for unique filename)

    Returns:
        Path to the screenshot file, or None if capture failed
    """
    try:
        # Create a temporary file for the screenshot
        temp_dir = tempfile.gettempdir()
        timestamp = int(asyncio.get_event_loop().time() * 1000)
        screenshot_path = os.path.join(temp_dir, f"screenshot_{chat_id}_{timestamp}.png")

        # Platform-specific screenshot capture
        if sys.platform == 'darwin':
            # macOS screenshot command
            success = await _capture_macos(screenshot_path)
        elif sys.platform == 'linux':
            # Linux screenshot using scrot or import (ImageMagick)
            success = await _capture_linux(screenshot_path)
        elif sys.platform == 'win32':
            # Windows screenshot using PowerShell
            success = await _capture_windows(screenshot_path)
        else:
            logger.error(f"Unsupported platform: {sys.platform}")
            return None

        if success and os.path.exists(screenshot_path):
            return screenshot_path
        else:
            return None

    except Exception as e:
        logger.error(f"Error capturing screenshot: {e}", exc_info=True)
        return None


async def _capture_macos(screenshot_path: str) -> bool:
    """
    Capture screenshot on macOS.

    Args:
        screenshot_path: Path to save the screenshot

    Returns:
        True if successful, False otherwise
    """
    try:
        process = await asyncio.create_subprocess_exec(
            'screencapture', '-x', screenshot_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()
        return process.returncode == 0
    except Exception as e:
        logger.error(f"macOS screenshot failed: {e}")
        return False


async def _capture_linux(screenshot_path: str) -> bool:
    """
    Capture screenshot on Linux.

    Args:
        screenshot_path: Path to save the screenshot

    Returns:
        True if successful, False otherwise
    """
    # Try scrot first
    try:
        process = await asyncio.create_subprocess_exec(
            'scrot', screenshot_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()
        if process.returncode == 0:
            return True
    except FileNotFoundError:
        pass

    # Try ImageMagick's import command
    try:
        process = await asyncio.create_subprocess_exec(
            'import', '-window', 'root', screenshot_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()
        return process.returncode == 0
    except FileNotFoundError:
        logger.error("Neither scrot nor ImageMagick found on Linux system")
        return False
    except Exception as e:
        logger.error(f"Linux screenshot failed: {e}")
        return False


async def _capture_windows(screenshot_path: str) -> bool:
    """
    Capture screenshot on Windows.

    Args:
        screenshot_path: Path to save the screenshot

    Returns:
        True if successful, False otherwise
    """
    try:
        ps_script = f"""
        Add-Type -AssemblyName System.Windows.Forms
        $screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
        $bitmap = New-Object System.Drawing.Bitmap $screen.Width, $screen.Height
        $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
        $graphics.CopyFromScreen($screen.Location, [System.Drawing.Point]::Empty, $screen.Size)
        $bitmap.Save('{screenshot_path}', [System.Drawing.Imaging.ImageFormat]::Png)
        $graphics.Dispose()
        $bitmap.Dispose()
        """
        process = await asyncio.create_subprocess_exec(
            'powershell', '-Command', ps_script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()
        return process.returncode == 0
    except Exception as e:
        logger.error(f"Windows screenshot failed: {e}")
        return False


def get_screenshot_error_message() -> str:
    """
    Get platform-specific error message for screenshot failures.

    Returns:
        Error message string
    """
    if sys.platform == 'darwin':
        return "❌ Failed to capture screenshot. screencapture command failed."
    elif sys.platform == 'linux':
        return (
            "❌ Screenshot tool not found. Please install:\n"
            "• scrot: `sudo apt install scrot` or\n"
            "• ImageMagick: `sudo apt install imagemagick`"
        )
    elif sys.platform == 'win32':
        return "❌ Failed to capture screenshot. PowerShell command failed."
    else:
        return f"❌ Unsupported operating system: {sys.platform}"
