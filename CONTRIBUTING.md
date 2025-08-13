# Contributing to BlackboxProgramming

Thank you for your interest in contributing! This project welcomes contributions from everyone. To keep things simple, please follow the guidelines below.

## Getting Started

1. Fork the repository on GitHub and clone your fork locally.
2. Install dependencies:
   ```bash
   python -m venv venv && source venv/bin/activate
   pip install -r requirements.txt
   ```
3. If you're working on the front‑end, install Node dependencies:
   ```bash
   cd src/frontend
   npm install
   ```

## Development Workflow

- Branch off from `main` and name your branch clearly, e.g. `feature/add-auth` or `bugfix/fix-lint-errors`.
- Before pushing, run the test suite and the linter:
   ```bash
   pytest
   pre-commit run --all-files
   ```
  The pre‑commit configuration includes `black`, `ruff`, `isort` and `detect‑secrets`.
- Make sure new code is covered by tests. If you’re adding a new route, add a corresponding test in `tests/`.

## Commit Messages

Use clear, concise commit messages following the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) style:

```
feat(component): add greeting API
fix(agent): handle missing input
docs: update README usage section
```

## Pull Requests

1. Ensure your branch is up to date with `main`.
2. Open a pull request. Include a description of the changes you’ve made and link any relevant issues.
3. A maintainer will review your PR. Please respond to feedback and make adjustments if requested.

## Code of Conduct

Please note that this project is governed by a [Code of Conduct](./CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Security

If you discover a security vulnerability, please follow the process described in [SECURITY.md](./SECURITY.md) rather than filing a public issue.

We appreciate your contributions! ✨
