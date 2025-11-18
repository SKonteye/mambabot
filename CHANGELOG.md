# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- CONTRIBUTING.md with contribution guidelines
- CHANGELOG.md for version tracking
- GitHub issue templates for bug reports and feature requests
- Installation badges to README
- Demo section in README with usage examples
- Reorganized test files to tests/ directory

### Changed
- Updated README.md with clearer project description
- Improved requirements.txt documentation for SDK dependencies
- Project name changed from "Projet telegram" to "telegram-claude-bot"

## [0.2.0] - 2025-01-15

### Added
- Interactive permission mode for SDK operations
- Per-chat session management with isolation
- Support for both SDK and CLI modes
- Configurable permission modes (interactive/bypass)
- Session continuity across messages

### Changed
- Refactored message handling to remove conversation history from prompts
- Improved structured message handling for SDK
- Enhanced session management architecture

### Fixed
- README description to accurately reflect permission modes
- Session directory cleanup and management

## [0.1.0] - 2025-01-14

### Added
- Initial release of Telegram Claude Bot
- Basic Telegram bot integration
- Claude Code CLI integration
- Remote file access capabilities
- Command execution through Claude
- Code generation and debugging features
- Screenshot capture functionality
- Image analysis support
- Persistent conversation context
- Basic commands: /start, /clear, /help
- Environment configuration via .env
- Security warnings and documentation
- MIT License

### Security
- Added security warnings for bypass mode
- Documentation for safe usage practices
- Environment variable protection via .gitignore

## Release Notes

### [0.2.0] - Interactive Permission Mode

This release adds interactive permission approval for SDK mode, allowing users to approve or deny each tool usage via Telegram buttons. This significantly improves security by giving users explicit control over what Claude can do on their machine.

**Breaking Changes:** None

**Migration Notes:**
- Set `PERMISSION_MODE=interactive` in .env to enable the new interactive mode
- CLI mode continues to use bypass permissions only

### [0.1.0] - Initial Release

First public release of Telegram Claude Bot. Provides remote access to Claude Code through Telegram with support for file operations, code generation, and command execution.

**Note:** This version uses bypass permissions by default. Users should be aware of security implications.

---

## Version Format

- **Major** version for incompatible API changes
- **Minor** version for added functionality in a backwards compatible manner
- **Patch** version for backwards compatible bug fixes

## Categories

- **Added** for new features
- **Changed** for changes in existing functionality
- **Deprecated** for soon-to-be removed features
- **Removed** for now removed features
- **Fixed** for any bug fixes
- **Security** for security-related changes
