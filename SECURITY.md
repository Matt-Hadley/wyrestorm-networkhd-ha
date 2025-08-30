# 🔒 Security Policy

## Supported Versions

We release patches for security vulnerabilities. Which versions are eligible for receiving such patches depends on the
CVSS v3.0 Rating:

| Version | Supported | | ------- | ------------------ | | 1.0.x | :white_check_mark: | | < 1.0 | :x: |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via email.

You should receive a response within 48 hours. If for some reason you do not, please follow up via email to ensure we
received your original message.

Please include the requested information listed below (as much as you can provide) to help us better understand the
nature and scope of the possible issue:

- Type of issue (buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the vulnerability
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit it

This information will help us triage your report more quickly.

## Preferred Languages

We prefer all communications to be in English.

## Disclosure Policy

When we receive a security bug report, we will assign it to a primary handler. This person will coordinate the fix and
release process, involving the following steps:

1. Confirm the problem and determine the affected versions.
1. Audit code to find any similar problems.
1. Prepare fixes for all supported versions. These fixes will be released as fast as possible to the main branch.

## Comments on This Policy

If you have suggestions on how this process could be improved please submit a pull request.

## Security Best Practices

### For Users

- Always use the latest stable version
- Keep your dependencies updated
- Use environment variables for sensitive configuration
- Validate all user inputs
- Follow the principle of least privilege
- Monitor logs for suspicious activity

### For Developers

- Never commit secrets or credentials
- Use dependency scanning tools
- Implement proper input validation
- Follow secure coding practices
- Regular security audits
- Keep dependencies updated

## Security Advisories

Security advisories will be published on our
[GitHub Security Advisories](https://github.com/Matt-Hadley/wyrestorm-networkhd-ha/security/advisories) page.

## Acknowledgments

We would like to thank all security researchers and users who have responsibly disclosed security vulnerabilities to us.

## License

This security policy is licensed under the
[Creative Commons Attribution 4.0 License](https://creativecommons.org/licenses/by/4.0/).
