# Security Guidelines

This repository contains cybersecurity and development portfolio code. The following security measures have been implemented:

## Environment Variables
- All sensitive configuration values use environment variables
- Never commit `.env` files to version control
- Use the provided `env.example` files as templates

## Secrets Management
- No hardcoded API keys, passwords, or secrets
- Database files are excluded from version control
- Virtual environments and build artifacts are gitignored

## Flask Application Security
- Secret keys are loaded from environment variables
- Database URLs are configurable via environment variables
- Password hashing is implemented using Werkzeug security functions

## Before Deployment
1. Generate strong random secret keys
2. Use secure database connections in production
3. Set `FLASK_ENV=production` and `FLASK_DEBUG=False`
4. Review all environment variables for sensitive data

## Files Excluded from Git
- Virtual environments (`env/`, `venv/`)
- Database files (`*.db`, `*.sqlite`)
- Environment files (`.env`)
- Cache and build directories
- IDE configuration files
- Terraform state files
- Ansible vault files

## Portfolio Overview
This repository demonstrates:
- Secure coding practices
- Environment variable management
- Proper gitignore configuration
- Infrastructure as Code (Terraform)
- Configuration Management (Ansible)
- SOC automation and incident response
- Python design patterns for security
