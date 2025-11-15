#!/usr/bin/env python3
"""
Configuration test for the Telegram Claude Bot.
Verifies that environment variables are properly configured.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def main():
    """Test configuration."""
    print("=" * 60)
    print("Configuration Test")
    print("=" * 60)

    # Check TELEGRAM_BOT_TOKEN
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if telegram_token:
        if telegram_token == 'your_telegram_bot_token_here':
            print("❌ TELEGRAM_BOT_TOKEN: Not configured (using placeholder)")
            print("   Please set your actual bot token in .env")
        else:
            print("✅ TELEGRAM_BOT_TOKEN: Configured")
    else:
        print("❌ TELEGRAM_BOT_TOKEN: Missing")

    # Check USE_CLAUDE_CLI
    use_cli = os.getenv('USE_CLAUDE_CLI', 'false').lower() == 'true'
    print(f"✅ USE_CLAUDE_CLI: {use_cli}")

    # Check ANTHROPIC_API_KEY (only required if not using CLI)
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    if not use_cli:
        if anthropic_key:
            if anthropic_key == 'your_anthropic_api_key_here':
                print("❌ ANTHROPIC_API_KEY: Not configured (using placeholder)")
                print("   Please set your actual API key in .env")
            else:
                print("✅ ANTHROPIC_API_KEY: Configured")
        else:
            print("❌ ANTHROPIC_API_KEY: Missing (required when USE_CLAUDE_CLI=false)")
    else:
        print("ℹ️  ANTHROPIC_API_KEY: Not required (using CLI mode)")

    print("=" * 60)

    if not telegram_token or telegram_token == 'your_telegram_bot_token_here':
        print("\n⚠️  Please configure your tokens in .env file before running the bot.")
        return 1

    if not use_cli and (not anthropic_key or anthropic_key == 'your_anthropic_api_key_here'):
        print("\n⚠️  Please configure ANTHROPIC_API_KEY in .env or set USE_CLAUDE_CLI=true")
        return 1

    print("\n✅ Configuration is ready!")
    return 0


if __name__ == '__main__':
    sys.exit(main())
