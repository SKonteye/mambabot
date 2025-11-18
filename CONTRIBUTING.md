# Contributing to Telegram Claude Bot

Thank you for your interest in contributing to Telegram Claude Bot! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)

## Code of Conduct

This project follows a simple code of conduct:

- Be respectful and inclusive
- Focus on constructive feedback
- Welcome newcomers and help them get started
- Respect differing viewpoints and experiences

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Set up your development environment (see below)
4. Create a new branch for your changes
5. Make your changes
6. Test your changes
7. Submit a pull request

## Development Setup

### Prerequisites

- Python 3.8 or higher
- Git
- A Telegram bot token (for testing)
- Either an Anthropic API key or Claude CLI installed

### Installation

```bash
# Clone your fork
git clone https://github.com/yourusername/telegram-claude-bot.git
cd telegram-claude-bot

# Create a virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
```

### Running Tests

```bash
# Run the test suite
python tests/test_bot.py

# Run configuration test
python tests/test_config.py

# Or run all tests from the tests directory
cd tests
python test_bot.py
python test_config.py
```

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When creating a bug report, include:

- A clear and descriptive title
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- Your environment (OS, Python version, etc.)
- Relevant logs or error messages

Use the bug report template when creating issues.

### Suggesting Enhancements

Enhancement suggestions are welcome! When suggesting an enhancement:

- Use a clear and descriptive title
- Provide a detailed description of the proposed feature
- Explain why this enhancement would be useful
- Provide examples of how it would work

Use the feature request template when creating issues.

### Contributing Code

1. **Find or create an issue** - Check existing issues or create a new one describing what you plan to work on
2. **Fork and branch** - Fork the repo and create a branch from `main`
3. **Write code** - Follow the coding standards below
4. **Add tests** - If applicable, add tests for your changes
5. **Test** - Ensure all tests pass
6. **Commit** - Use clear and descriptive commit messages
7. **Push** - Push to your fork
8. **Pull request** - Submit a PR with a clear description

## Coding Standards

### Python Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions focused and concise
- Maximum line length: 100 characters

### Example

```python
def process_message(message: str, chat_id: int) -> str:
    """
    Process a user message and return a response.

    Args:
        message: The user's message text
        chat_id: The Telegram chat ID

    Returns:
        The bot's response text
    """
    # Implementation here
    pass
```

### File Organization

- Keep related functionality together
- Use the existing directory structure:
  - `src/telegram_claude_bot/` - Main package
  - `src/telegram_claude_bot/handlers/` - Message handlers
  - `tests/` - Test files
- Import order: standard library, third-party, local

### Comments

- Use comments to explain "why", not "what"
- Keep comments up-to-date with code changes
- Use TODO comments for future improvements

### Error Handling

- Use try-except blocks appropriately
- Provide meaningful error messages
- Log errors with sufficient context
- Don't expose sensitive information in error messages

## Testing

### Running Tests

```bash
# Run all tests
python tests/test_bot.py

# Test configuration
python tests/test_config.py
```

### Writing Tests

- Add tests for new features
- Update tests when modifying existing features
- Ensure tests are isolated and repeatable
- Use descriptive test names

## Pull Request Process

### Before Submitting

1. Ensure your code follows the coding standards
2. Run all tests and ensure they pass
3. Update documentation if needed
4. Update CHANGELOG.md with your changes
5. Rebase on the latest main branch

### PR Description

Include in your PR description:

- What changes you made
- Why you made these changes
- Any related issues (use "Fixes #123" or "Closes #123")
- Screenshots (if UI changes)
- Testing performed

### Review Process

1. A maintainer will review your PR
2. Address any requested changes
3. Once approved, a maintainer will merge your PR
4. Your contribution will be included in the next release

### PR Guidelines

- Keep PRs focused on a single feature or fix
- Write a clear PR title and description
- Link to related issues
- Be responsive to feedback
- Be patient - reviews may take time

## Project Structure

```
telegram-claude-bot/
├── src/
│   └── telegram_claude_bot/        # Main package
│       ├── __init__.py
│       ├── bot.py                  # Main application
│       ├── config.py               # Configuration
│       ├── utils.py                # Utilities
│       ├── claude_manager.py       # Claude integration
│       ├── screenshot.py           # Screenshot functionality
│       ├── session.py              # Session management
│       └── handlers/               # Message handlers
│           ├── __init__.py
│           ├── commands.py         # Command handlers
│           ├── messages.py         # Message processing
│           └── errors.py           # Error handling
├── tests/                          # Test files
├── run_bot.py                      # Entry point
├── requirements.txt                # Dependencies
├── CONTRIBUTING.md                 # This file
├── CHANGELOG.md                    # Version history
└── README.md                       # Documentation
```

## Questions?

If you have questions:

- Check existing documentation
- Search existing issues
- Create a new issue with your question

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Thank You!

Your contributions are greatly appreciated and help make this project better for everyone.
