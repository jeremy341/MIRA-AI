# Security Policy

## Supported versions

Only the latest release on [PyPI](https://pypi.org/project/mira-ai/) receives fixes.

## Reporting a vulnerability

Please do not open a public issue for security problems. Use GitHub's private
reporting instead: **Security → Report a vulnerability** on this repository.

Include what you found, how to reproduce it, and the MIRA version. You can expect
a first reply within about a week. This is a student research project, so fixes
are made on a best-effort basis.

## Scope notes

The local dashboard (`mira dashboard`) is meant for `127.0.0.1` on your own
machine. It has no authentication, so do not expose it to an untrusted network.
