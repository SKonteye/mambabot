#!/usr/bin/env python3
"""
Launcher script for the Telegram Claude Bot.
This is the main entry point to run the bot.
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from telegram_claude_bot.bot import main

if __name__ == '__main__':
    main()
