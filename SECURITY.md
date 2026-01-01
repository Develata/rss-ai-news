# Security Policy

## Supported Versions

We release patches for security vulnerabilities. Currently supported versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

**Please do NOT report security vulnerabilities through public GitHub issues.**

If you discover a security vulnerability, please send an email to:

📧 **[Your Email Address]** (or create a private security advisory on GitHub)

Please include:

- Type of vulnerability (e.g., SQL injection, XSS, authentication bypass)
- Full paths of source file(s) related to the manifestation of the vulnerability
- Location of the affected source code (tag/branch/commit or direct URL)
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact assessment (e.g., what an attacker could do)

### What to expect

- **Acknowledgment**: Within 48 hours
- **Initial assessment**: Within 7 days
- **Fix timeline**: Critical issues within 30 days, others within 90 days
- **Disclosure**: Coordinated with reporter before public disclosure

## Security Best Practices

When deploying this project:

1. **Never commit `.env` files** containing real credentials
2. **Use strong, unique passwords** for all services (DB, SMTP, API keys)
3. **Enable TLS/SSL** for database connections in production
4. **Rotate API keys** periodically
5. **Run containers as non-root** (already configured in Dockerfile)
6. **Keep dependencies updated**: Run `pip list --outdated` regularly
7. **Use secrets management**: Consider HashiCorp Vault or AWS Secrets Manager for production

## Known Security Considerations

- **API Key Exposure**: Ensure `.env` file permissions are restrictive (`chmod 600 .env`)
- **SQLite in Production**: Not recommended for multi-user scenarios (use PostgreSQL)
- **Proxy Configuration**: Validate proxy URL to prevent SSRF attacks
- **RSS Feed Parsing**: Trafilatura library handles XSS mitigation, but always validate external content

## Disclosure Policy

We follow **Responsible Disclosure** principles:

- Security researchers will be credited in release notes (unless anonymity is requested)
- Vulnerabilities will be patched before public disclosure
- CVE IDs will be requested for critical vulnerabilities

Thank you for helping keep RSS AI News and our users safe!
