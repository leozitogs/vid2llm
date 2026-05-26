# Contributing to vid2llm

Thanks for your interest in contributing. This document explains how to set up a local
development environment and the conventions every contribution must follow.

## Development workflow

This project uses **trunk-based development**.

- `main` is the only long-lived branch and must always be green.
- Feature branches are short-lived (under 3 days) and prefixed by type:
  - `feat/<short-description>`
  - `fix/<short-description>`
  - `docs/<short-description>`
  - `refactor/<short-description>`
  - `test/<short-description>`
  - `chore/<short-description>`
- All changes land via Pull Request, squash-merged by default.

## Commit messages

This repository follows the [Conventional Commits](https://www.conventionalcommits.org/)
specification. Format:

```
<type>(<scope>): <description>
```

- Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`,
  `chore`, `revert`.
- Description: imperative mood, lowercase, no trailing period, under 72 characters.
- Body wrapped at 100 characters, separated from the description by a blank line.
- Breaking changes use the `BREAKING CHANGE:` footer.

## Local setup

Requires Python 3.11 or newer and [uv](https://github.com/astral-sh/uv).

```bash
uv sync --all-extras --dev
uv run pre-commit install
```

## Running checks

Run each check before opening a PR. CI runs the same set on every push.

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy src tests
uv run pytest
```

## Coverage

Minimum line coverage on `main` is 80 percent. Coverage is enforced in CI.

## Reporting bugs and requesting features

Use the GitHub issue templates under `.github/ISSUE_TEMPLATE/`.

## Code of conduct

By participating, you agree to abide by the [Code of Conduct](CODE_OF_CONDUCT.md).

## Security

Do not file security issues in the public tracker. See [SECURITY.md](SECURITY.md).
