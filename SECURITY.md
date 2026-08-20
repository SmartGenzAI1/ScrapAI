# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 2.x     | :white_check_mark: |
| < 2.0   | :x:                |

---

## Reporting a Vulnerability

We take the security of **ScrapAI** seriously. If you discover a security vulnerability, please do not report it in public GitHub issues.

### Reporting Procedure
1. Send an email describing the vulnerability, affected components, steps to reproduce, and potential impact.
2. Provide relevant logs or proof of concept code if available.
3. We will acknowledge receipt of your report within 48 hours and work with you to release a patch promptly.

### Security Best Practices for Deployments
- Always run the server behind a reverse proxy (e.g., NGINX, Cloudflare) with HTTPS enabled in production.
- Respect target website `robots.txt` policies and maintain reasonable `REQUEST_DELAY` settings.
- If exposing endpoints publicly, configure appropriate rate limiting and firewall rules.
