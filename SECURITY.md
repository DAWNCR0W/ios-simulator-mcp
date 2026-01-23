# Security Policy

## Supported Versions

We release patches for security vulnerabilities for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability, please report it responsibly.

### How to Report

1. **Do NOT** create a public GitHub issue for security vulnerabilities
2. Email the maintainers directly or use GitHub's private vulnerability reporting feature
3. Include as much detail as possible:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### What to Expect

- **Acknowledgment**: We will acknowledge receipt within 48 hours
- **Updates**: We will provide updates on the progress
- **Resolution**: We aim to resolve critical issues within 7 days
- **Credit**: We will credit reporters in the release notes (unless anonymity is requested)

## Security Best Practices

When using iOS Simulator MCP:

### Accessibility Permissions

This tool requires macOS Accessibility permissions to function. Be aware that:

- Only grant Accessibility permissions to trusted applications
- The tool can read and interact with any UI visible in the iOS Simulator
- Revoke permissions when not in use if desired

### Network Security

When running in HTTP mode:

- Bind only to `127.0.0.1` (localhost) unless remote access is explicitly needed
- Use firewall rules to restrict access if binding to `0.0.0.0`
- Consider using TLS/HTTPS for remote connections (not built-in; use a reverse proxy)

### Data Privacy

- UI tree data may contain sensitive information visible on screen
- Screenshots capture everything visible in the simulator
- Log files may contain UI element data; handle logs appropriately

## Security Features

### Input Validation

- All tool inputs are validated before processing
- Path traversal attempts are blocked for file operations

### Error Handling

- Sensitive information is not exposed in error messages
- Stack traces are only shown in DEBUG mode

## Scope

This security policy covers:

- The iOS Simulator MCP server code
- Official releases and packages

It does NOT cover:

- Third-party integrations or modifications
- Issues in dependencies (report those to respective projects)
- iOS Simulator or macOS security issues (report to Apple)

## Contact

For security-related inquiries, please use GitHub's security advisory feature or contact the maintainers directly.
