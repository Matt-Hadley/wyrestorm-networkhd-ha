# Contributing to WyreStorm NetworkHD Home Assistant Integration

Thank you for your interest in contributing! This project welcomes contributions of all kinds, from bug reports and
feature requests to code contributions and documentation improvements.

## 🚀 Quick Start

1. **Fork the repository** on GitHub
2. **Clone your fork**: `git clone https://github.com/YOUR-USERNAME/wyrestorm-networkhd-ha.git`
3. **Set up development environment**: `make install`
4. **Create a feature branch**: `git checkout -b feature/amazing-feature`
5. **Make your changes**
6. **Run tests and quality checks**: `make dev-workflow`
7. **Commit with conventional commits**: `git commit -m "feat: add amazing feature"`
8. **Push to your fork**: `git push origin feature/amazing-feature`
9. **Create a Pull Request**

## 🛠️ Development Environment Setup

### Prerequisites

- **Python 3.11+** (see `pyproject.toml` for exact requirements)
- **Git** for version control
- **Make** (optional but recommended for using project commands)

### Initial Setup

```bash
# Clone the repository
git clone https://github.com/Matt-Hadley/wyrestorm-networkhd-ha.git
cd wyrestorm-networkhd-ha

# Complete development environment setup
make install
```

This single command will:

- Create a Python virtual environment (`.venv`)
- Install all development dependencies
- Set up pre-commit hooks
- Validate your environment

### Manual Setup (if Make is not available)

```bash
# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install package in development mode with all dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

## 🧪 Testing and Quality

### Development Workflow Commands

```bash
# Daily development workflow: format → lint → test (fast)
make dev-workflow

# Individual commands
make format           # Format code with Ruff and Prettier
make lint            # Run linting checks
make test            # Run all tests
make test-fast       # Run only fast unit tests
make test-cov        # Run tests with coverage report
make check           # Run all quality checks
make build           # Build and validate package

# Comprehensive validation (before commits/releases)
make health-check    # Full project validation
make pre-commit      # Run pre-commit hooks

# See all available commands
make help
```

### Test Categories

Tests are organized into categories using pytest markers:

```bash
# Unit tests (fast, no external dependencies)
make test-fast
# or: pytest -m "unit"

# Integration tests (require device/mocking)
pytest -m "integration"

# Performance tests (slow, benchmark-focused)
pytest -m "performance"

# All tests
make test
```

### Code Quality Standards

- **Line Length**: 120 characters maximum
- **Formatter**: Ruff (replaces Black and isort)
- **Linter**: Ruff + MyPy for type checking
- **Security**: Bandit for security analysis
- **Pre-commit hooks**: Automatically run on commit

## 📝 Code Style and Standards

### Python Style

- Follow **PEP 8** guidelines (enforced by Ruff)
- Use **type hints** for all function signatures
- Write **comprehensive docstrings** using Google style
- Maximum **line length of 120 characters**

### Docstring Example

````python
async def send_command(self, command: str, timeout: float = 10.0) -> str:
    """Send a command to the NetworkHD device.

    Args:
        command: The command string to send to the device.
        timeout: Maximum time to wait for response in seconds.

    Returns:
        The response string from the device.

    Raises:
        ConnectionError: If not connected to the device.
        CommandError: If the command fails or times out.

    Example:
        ```python
        response = await client.send_command("matrix get")
        ```
    """
````

### Branch Naming Conventions

- `feature/description`: New features or enhancements
- `fix/description`: Bug fixes
- `docs/description`: Documentation updates
- `refactor/description`: Code refactoring without behavior changes
- `test/description`: Test improvements or additions

### Commit Message Format

Use [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Formatting changes (no code logic change)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**

```
feat(ssh): add support for custom SSH host key policies
fix(rs232): resolve connection timeout on slow devices
docs: update API examples in README
refactor(client): simplify connection state management
test: add unit tests for notification handlers
```

## 🐛 Bug Reports

### Before Reporting

- **Search existing issues** to avoid duplicates
- **Try the latest version** from the main branch
- **Create a minimal reproduction** to isolate the issue
- **Check the documentation** for known limitations

### Bug Report Template

When creating a bug report, please include:

```markdown
## Bug Description

Brief, clear description of the issue.

## Steps to Reproduce

1. Create client with these settings...
2. Execute this command...
3. Observe the error...

## Expected Behavior

What you expected to happen.

## Actual Behavior

What actually happened, including full error messages.

## Environment

- OS: [e.g., Ubuntu 22.04, Windows 11]
- Python Version: [e.g., 3.12.1]
- Package Version: [e.g., 1.2.3]
- Device Type: [e.g., NHD-400-TX, NHD-110-RX]

## Additional Context

- Log output (with DEBUG level if relevant)
- Device firmware version
- Network configuration details
```

## 💡 Feature Requests

### Before Requesting

- **Check existing issues** and discussions
- **Review the NetworkHD raw API documentation** to ensure the feature is supported by the device
- **Consider the scope** - does it fit the project's goals?
- **Think about backwards compatibility**

### Feature Request Template

```markdown
## Feature Description

Clear, concise description of the requested feature.

## Use Case

Specific scenario where this feature would be valuable.

## Proposed API

How you envision the feature would be used:

\`\`\`python

# Example of how the feature might work

api.new_feature.do_something(param1, param2) \`\`\`

## Implementation Notes

Any thoughts on how this might be implemented.

## Alternatives Considered

Other approaches you've considered or researched.
```

## 🔍 Code Review Process

### Pull Request Requirements

- **All tests must pass** (CI/CD checks)
- **Code coverage** should not decrease significantly
- **Documentation** updated for new features
- **Type hints** for all new code
- **Conventional commit** messages

### Review Criteria

- **Functionality**: Does the code work as intended?
- **Performance**: Are there any performance implications?
- **Security**: Are there security considerations?
- **Maintainability**: Is the code readable and well-organized?
- **Testing**: Are there adequate tests?
- **Documentation**: Is it properly documented?

## 🔧 Advanced Development

### Logging and Debugging

The package includes comprehensive logging for development and debugging:

#### Default Logging Configuration

- **Console output** at INFO level by default
- **Structured logging** with timestamps and module names
- **Configurable levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL

#### Customizing Logging During Development

```python
from wyrestorm_networkhd.logging_config import setup_logging

# Enable verbose debug logging
setup_logging(level="DEBUG")

# Log to file for analysis
setup_logging(
    level="DEBUG",
    log_file="logs/development.log"
)

# Custom format for development
setup_logging(
    level="DEBUG",
    log_format="%(asctime)s [%(levelname)8s] %(name)s: %(message)s"
)
```

#### Environment Variable Control

```bash
# Set log level via environment
export LOG_LEVEL=DEBUG
python your_development_script.py

# Enable all debug output during testing
LOG_LEVEL=DEBUG make test
```

#### What Gets Logged

- **DEBUG**: Command/response details, SSH operations, connection state changes
- **INFO**: Connection events, command execution, major operations
- **WARNING**: Recoverable issues, fallback behaviors
- **ERROR**: Connection failures, command errors, exceptions
- **CRITICAL**: System failures, unrecoverable errors

### Working with Real Devices

When developing with actual NetworkHD devices:

```python
# Enable detailed logging for device interaction
from wyrestorm_networkhd.logging_config import setup_logging
setup_logging(level="DEBUG")

# Test with real device
client = NetworkHDClientSSH(
    host="192.168.1.100",
    port=10022,
    username="wyrestorm",
    password="networkhd",
    ssh_host_key_policy="warn"  # Use "warn" for development
)

async with client:
    # Your development code here
    response = await client.send_command("help")
    print(f"Device response: {response}")
```

### Performance Considerations

- **Connection pooling**: Consider implications of multiple connections
- **Command batching**: Group related commands when possible
- **Resource cleanup**: Always use context managers (`async with`)
- **Error recovery**: Implement proper retry logic for network issues

### Architecture Guidelines

- **Separation of concerns**: Keep protocol handling separate from API logic
- **Type safety**: Use type hints and data classes extensively
- **Error handling**: Provide specific exception types
- **Async patterns**: Use proper async/await patterns throughout

## 🔒 Security Considerations

### Development Security

- **Never commit credentials** or device information
- **Use secure defaults** in examples and tests
- **Validate all inputs** especially those from devices
- **Handle sensitive data** (passwords, tokens) securely

### Reporting Security Issues

**DO NOT** create public issues for security vulnerabilities.

Instead, please email: 81762940+Matt-Hadley@users.noreply.github.com

- Subject: `[SECURITY] WyreStorm NetworkHD - [Brief Description]`
- Include detailed reproduction steps
- Provide suggested fixes if possible

## 📚 Documentation

### Documentation Standards

- **Clear, concise language** accessible to developers of all levels
- **Working code examples** that can be copy-pasted
- **Type hints** in all code examples
- **Error handling** shown in examples when relevant
- **Keep examples up-to-date** with API changes

### Building Documentation

```bash
# Build documentation locally
make docs

# Serve documentation with live reload
make docs-serve

# Clean documentation artifacts
make clean-docs
```

### Documentation Structure

- **Homepage**: Overview, installation, quick start
- **API Reference**: Auto-generated from docstrings
- **Resources**: NetworkHD raw API documentation
- **Contributing**: This guide
- **Changelog**: Release history

## 🚀 Release Process

### Versioning

- Uses **Semantic Versioning** (MAJOR.MINOR.PATCH)
- **Automated versioning** based on conventional commits
- **Release Please** manages releases automatically

### Release Workflow

1. **Conventional commits** trigger appropriate version bumps
2. **Release Please** creates release PR when ready
3. **Merging release PR** triggers:
   - PyPI package publication
   - GitHub release creation
   - Documentation site update
   - Coverage badge update

### Version Bump Examples

```bash
# Patch version (1.0.0 → 1.0.1)
git commit -m "fix: resolve SSH timeout issue"

# Minor version (1.0.0 → 1.1.0)
git commit -m "feat: add RS232 connection support"

# Major version (1.0.0 → 2.0.0)
git commit -m "feat!: redesign client API

BREAKING CHANGE: Client constructor now requires explicit protocol"
```

## 🤝 Community Guidelines

### Code of Conduct

- **Be respectful and inclusive** in all interactions
- **Focus on technical merit** in discussions
- **Welcome newcomers** and help them contribute
- **Provide constructive feedback** in reviews
- **Assume positive intent** from other contributors

### Getting Help

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and ideas
- **Documentation**: Check the docs site first
- **Code Examples**: Look at tests for usage patterns

### Recognition

Contributors are recognized in:

- **GitHub contributor graph**
- **Release notes** (automatic from conventional commits)
- **Package metadata** (for significant contributors)

## 📄 License

By contributing to this project, you agree that your contributions will be licensed under the **MIT License**.

---

## Need Help?

- 📖 **Documentation**: https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/blob/main/README.md
- 🐛 **Issues**: https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/issues
- 💬 **Discussions**: https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/discussions

**Thank you for contributing!** 🎉
