#!/usr/bin/env python3
"""
Test suite for the Telegram Claude Bot.
Validates module imports and basic functionality.
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    try:
        from telegram_claude_bot import config
        from telegram_claude_bot import utils
        from telegram_claude_bot import session
        from telegram_claude_bot import claude_manager
        from telegram_claude_bot import screenshot
        from telegram_claude_bot import bot
        from telegram_claude_bot.handlers import commands, messages, errors
        print("✅ PASS: All modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ FAIL: Import error - {e}")
        return False


def test_config():
    """Test configuration loading."""
    print("\nTesting configuration...")
    try:
        from telegram_claude_bot.config import config, ERROR_MESSAGES, WELCOME_MESSAGE, HELP_MESSAGE

        # Check that config has required attributes
        assert hasattr(config, 'telegram_token'), "Config missing telegram_token"
        assert hasattr(config, 'use_cli'), "Config missing use_cli"
        assert hasattr(config, 'max_history_length'), "Config missing max_history_length"

        # Check that messages are defined
        assert WELCOME_MESSAGE, "WELCOME_MESSAGE is empty"
        assert HELP_MESSAGE, "HELP_MESSAGE is empty"
        assert ERROR_MESSAGES, "ERROR_MESSAGES is empty"

        print("✅ PASS: Configuration loaded correctly")
        return True
    except Exception as e:
        print(f"❌ FAIL: Configuration error - {e}")
        return False


def test_utils():
    """Test utility functions."""
    print("\nTesting utilities...")
    try:
        from telegram_claude_bot.utils import split_message, extract_image_paths

        # Test split_message
        long_text = "a" * 5000
        chunks = split_message(long_text, max_length=4000)
        assert len(chunks) > 1, "split_message should split long text"

        short_text = "Hello"
        chunks = split_message(short_text, max_length=4000)
        assert len(chunks) == 1, "split_message should not split short text"

        # Test extract_image_paths
        text = "Here is an image at /path/to/image.png"
        paths = extract_image_paths(text)
        assert len(paths) > 0, "extract_image_paths should find image paths"

        print("✅ PASS: Utilities work correctly")
        return True
    except Exception as e:
        print(f"❌ FAIL: Utilities error - {e}")
        return False


def test_session_manager():
    """Test session manager."""
    print("\nTesting session manager...")
    try:
        from telegram_claude_bot.session import get_session_manager

        session_manager = get_session_manager()

        # Test get_history
        history = session_manager.get_history(12345)
        assert isinstance(history, list), "get_history should return a list"

        # Test add_message
        session_manager.add_message(12345, "user", "Hello")
        history = session_manager.get_history(12345)
        assert len(history) == 1, "add_message should add to history"
        assert history[0]["role"] == "user", "Message role should be 'user'"
        assert history[0]["content"] == "Hello", "Message content should match"

        # Test clear_history
        session_manager.clear_history(12345)
        history = session_manager.get_history(12345)
        assert len(history) == 0, "clear_history should clear all messages"

        print("✅ PASS: Session manager works correctly")
        return True
    except Exception as e:
        print(f"❌ FAIL: Session manager error - {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Telegram Claude Bot - Test Suite")
    print("=" * 60)

    results = []

    results.append(("Imports", test_imports()))
    results.append(("Configuration", test_config()))
    results.append(("Utilities", test_utils()))
    results.append(("Session Manager", test_session_manager()))

    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:.<40} {status}")

    all_passed = all(result[1] for result in results)

    print("=" * 60)
    if all_passed:
        print("🎉 All tests passed! Bot is ready to run.")
        return 0
    else:
        print("❌ Some tests failed. Please fix the issues before running.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
