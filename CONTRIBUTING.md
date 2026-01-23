# Contributing to iOS Simulator MCP

First off, thank you for considering contributing to iOS Simulator MCP! It's people like you that make this tool better for everyone.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Pull Request Process](#pull-request-process)
- [Style Guidelines](#style-guidelines)

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

### Prerequisites

- macOS (Apple Silicon or Intel)
- Python 3.11 or higher
- Xcode with iOS Simulator
- Git

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/DAWNCR0W/ios-simulator-mcp.git
   cd ios-simulator-mcp
   ```

3. Add the upstream repository:
   ```bash
   git remote add upstream https://github.com/DAWNCR0W/ios-simulator-mcp.git
   ```

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates.

When creating a bug report, include:

- **Clear title** describing the issue
- **Steps to reproduce** the behavior
- **Expected behavior** vs **actual behavior**
- **Environment details**: macOS version, Python version, Xcode version
- **Screenshots or logs** if applicable

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion:

- Use a **clear and descriptive title**
- Provide a **detailed description** of the suggested enhancement
- Explain **why this enhancement would be useful**
- List **examples of how it would be used**

### Pull Requests

1. Create a new branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes

3. Write or update tests as needed

4. Ensure all tests pass:
   ```bash
   pytest
   ```

5. Commit your changes:
   ```bash
   git commit -m "feat: add your feature description"
   ```

6. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

7. Open a Pull Request

## Development Setup

### Setting Up the Development Environment

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install in editable mode
pip install -e .
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=lib

# Run specific test file
pytest tests/test_specific.py
```

### Running the Server Locally

```bash
# STDIO mode
python -m lib.main --transport stdio

# HTTP mode
python -m lib.main --transport http --port 3000
```

## Pull Request Process

1. **Update documentation**: If you're adding features, update the README or relevant docs
2. **Add tests**: New features should include appropriate tests
3. **Follow the style guide**: Ensure your code follows our coding standards
4. **Write clear commit messages**: Use conventional commit format
5. **Request review**: Tag maintainers for review once your PR is ready

### Commit Message Format

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Examples:
```
feat(ui): add support for landscape orientation
fix(tap): resolve coordinate calculation issue
docs: update installation instructions
```

## Style Guidelines

### Python Code Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use type hints for function parameters and return values
- Maximum line length: 100 characters
- Use docstrings for public functions and classes

### Code Organization

This project follows Clean Architecture principles:

```
lib/
├── core/           # Shared utilities
├── features/       # Feature modules
│   └── feature_name/
│       ├── data/           # Data layer
│       ├── domain/         # Business logic
│       └── presentation/   # Interface layer
└── main.py
```

### Documentation

- Update README.md for user-facing changes
- Add docstrings to new functions and classes
- Comment complex logic when necessary

## Questions?

Feel free to open an issue with the `question` label or start a discussion in the Discussions tab.

---

Thank you for contributing!
