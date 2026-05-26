# vid2llm — Engineering Standards

> Non-negotiable technical standards for every line of code, test, and document.
> Every implementation prompt references this document. Deviations require PO approval.

**Status:** Active
**Last updated:** 2026-05-25
**Governs:** All source code, tests, configuration, and developer-facing documentation.

---

## 1. Code Style

### 1.1 Formatting and linting

- **`ruff format`** is the sole formatter. Line length: **100**.
- **`ruff check`** is the sole linter. Configuration in `pyproject.toml` under `[tool.ruff]`.
- Enabled rule sets: `E`, `W`, `F`, `I`, `N`, `D`, `UP`, `B`, `A`, `C4`, `RET`, `SIM`, `TCH`, `PTH`, `RUF`.
- Disabled rules must be justified by an inline comment.

### 1.2 Imports

- Absolute imports for all `vid2llm` internals.
- Imports sorted by `ruff` (isort-compatible).
- No wildcard imports (`from x import *`).
- Type-only imports placed under `if TYPE_CHECKING:` blocks.

### 1.3 Naming

- `snake_case` for functions, methods, variables, modules.
- `PascalCase` for classes, type aliases, TypedDicts.
- `UPPER_SNAKE_CASE` for module-level constants.
- Private members prefixed with single underscore.
- No double-underscore names except dunder methods.

## 2. Type Safety

### 2.1 Coverage

- **Every public function, method, and class must be fully type-annotated.** No exceptions.
- Internal helpers may omit annotations only when types are trivially inferable.
- `mypy --strict` must pass with zero errors on every commit.

### 2.2 Style

- Use built-in generics (`list[str]`, `dict[str, int]`) — never `List`, `Dict` from `typing`.
- Use `X | None` instead of `Optional[X]`.
- Use `X | Y` instead of `Union[X, Y]`.
- Use `typing.Protocol` for structural typing of backends and adapters.
- Use `typing.Literal` for constrained string enums when an `Enum` is overkill.
- Use `dataclasses` for plain data containers; `pydantic` is reserved for boundaries (CLI input, API surfaces) — not for internal types.

### 2.3 Public API marker

- `src/vid2llm/py.typed` must exist (PEP 561 marker for type-aware consumers).

## 3. Documentation

### 3.1 Docstrings

- Every public module, class, function, and method has a docstring.
- Format: **Google style** (sections: `Args`, `Returns`, `Raises`, `Examples`).
- First line: imperative mood, single sentence, ends with period.
- Examples in docstrings must be valid Python and runnable.

### 3.2 Inline comments

- Comments explain **why**, not **what**.
- No commented-out code in `main`.
- No `TODO` comments without an associated GitHub issue number: `# TODO(#42): description`.
- No AI self-attribution in any comment, ever.

### 3.3 Public documentation

- Lives in `docs/`, rendered by `mkdocs-material`.
- Code examples in docs are tested via `pytest --doctest-glob='*.md'` when feasible.

## 4. Testing

### 4.1 Framework and structure

- `pytest` is the sole test runner.
- Tests live under `tests/`, split into `tests/unit/` and `tests/integration/`.
- Test files mirror source structure: `src/vid2llm/core/extractor.py` → `tests/unit/core/test_extractor.py`.
- Shared fixtures in `tests/conftest.py`.

### 4.2 Coverage

- Minimum **80% line coverage** for `main` branch.
- Coverage measured by `pytest-cov`, enforced in CI.
- Coverage report uploaded to Codecov (or equivalent) on each CI run.

### 4.3 Style

- One assertion per test when reasonable; multi-assertion tests must use `pytest.raises` or describe a single behavior.
- Test names are descriptive sentences: `test_extractor_raises_when_video_file_missing`.
- Use `pytest.parametrize` for input variations rather than loops.
- No sleeping, no network calls, no real file I/O outside `tests/fixtures/` in unit tests.

### 4.4 Fixtures

- Test videos live in `tests/fixtures/` and are kept **small** (under 1 MB each).
- Generated fixtures (synthetic videos) are preferred over real ones.

## 5. Error Handling

### 5.1 Exceptions

- All custom exceptions inherit from a base `Vid2LLMError` defined in `src/vid2llm/exceptions.py`.
- Exception hierarchy is shallow and meaningful: `BackendNotAvailableError`, `UnsupportedFormatError`, `ExtractionError`, `ProviderError`.
- Never raise bare `Exception` or `RuntimeError` in library code.
- Never `except` without specifying the exception type.
- Never silently swallow exceptions; if catching, log or re-raise.

### 5.2 User-facing errors

- CLI errors are caught at the entry point and rendered with `rich` (red, no traceback in default mode).
- Library errors propagate normally; consumers handle them.
- `--verbose` flag in CLI enables full traceback.

## 6. Logging

- Standard `logging` module, configured once at the CLI entry point with `rich.logging.RichHandler`.
- Library code never calls `logging.basicConfig`.
- Library modules use `logger = logging.getLogger(__name__)`.
- Log levels: `DEBUG` for internal trace, `INFO` for milestones, `WARNING` for recoverable issues, `ERROR` for failures.
- No `print()` statements in library or CLI code outside of explicit user-facing output via `rich`.

## 7. Dependencies

### 7.1 Policy

- Every runtime dependency must be justified in `pyproject.toml` with a brief comment.
- Optional dependencies grouped via PEP 621 `optional-dependencies`: `cv`, `pyav`, `ocr`, `detection`, `providers`, `all`.
- Dev dependencies in `[dependency-groups]` (PEP 735) `dev`, `docs`, `test`.
- No unpinned dependencies in `pyproject.toml`; use `>=X,<Y` ranges.
- Lockfile (`uv.lock`) committed to repository.

### 7.2 Prohibited

- No dependencies with known security advisories (enforced by `pip-audit` in CI).
- No dependencies with restrictive licenses (GPL, AGPL) in runtime path.
- No dependencies under 1.0.0 unless no alternative exists and risk is documented.

## 8. Git and Commits

### 8.1 Commit messages

- **Conventional Commits** format: `<type>(<scope>): <description>`.
- Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`.
- Description in **imperative mood**, lowercase, no trailing period, under 72 characters.
- Body wrapped at 100 characters, separated from description by blank line.
- Footer for breaking changes: `BREAKING CHANGE: <description>`.
- **No AI self-attribution in any commit message, trailer, or body.**

### 8.2 Branching

- Trunk-based development.
- `main` is the only long-lived branch.
- Feature branches: `feat/<short-description>`, `fix/<short-description>`, `docs/<short-description>`, etc.
- Feature branches live no longer than 3 days.
- All changes land via Pull Request, even by the sole maintainer.
- Squash-merge by default; merge commits reserved for releases.

### 8.3 Branch protection (`main`)

- Require PR before merge.
- Require status checks (CI green) before merge.
- Require linear history.
- No force pushes.
- No deletions.

## 9. Releases

- Semantic Versioning 2.0.0 (`MAJOR.MINOR.PATCH`).
- Releases triggered by git tag: `v<MAJOR>.<MINOR>.<PATCH>`.
- Tag format enforced by `release.yml` workflow.
- `CHANGELOG.md` generated by `git-cliff` from Conventional Commits between tags.
- PyPI publication automated via trusted publishing (OIDC), no API tokens stored.
- GitHub Releases created automatically with release notes from changelog.

## 10. CI/CD

### 10.1 Required checks on every PR

- `ruff format --check`
- `ruff check`
- `mypy --strict`
- `pytest` across Python 3.11, 3.12, 3.13 on Ubuntu, macOS, Windows.
- `pip-audit` security scan.
- Coverage report.

### 10.2 Required checks on `main` push

- All of the above.
- Docs build (`mkdocs build --strict`).

### 10.3 Release workflow

- Triggered by tag push matching `v*.*.*`.
- Builds wheel and sdist with `uv build`.
- Publishes to PyPI via OIDC trusted publishing.
- Creates GitHub Release with auto-generated notes.

## 11. Documentation Standards

### 11.1 README

- Opens with a single tagline.
- Followed by badges (PyPI version, Python versions, CI status, coverage, license).
- Followed by a 30-second pitch.
- Followed by installation in one line.
- Followed by a minimal working example (≤10 lines).
- Followed by feature highlights (no walls of text).
- Followed by links to full docs, contributing, license.

### 11.2 mkdocs site

- Navigation: Home, Getting Started, Guides, API Reference, Contributing, Changelog.
- API Reference auto-generated by `mkdocstrings` from docstrings.
- Every page renders cleanly on mobile.

## 12. Security

- `SECURITY.md` defines vulnerability disclosure policy.
- Secrets never committed; `.env*` in `.gitignore`.
- Dependency scanning via `pip-audit` in CI.
- Code scanning via GitHub's CodeQL (default Python config).

## 13. Performance

- Public functions that process video must support **streaming** (no full-video memory load) when the backend allows it.
- Benchmarks live in `benchmarks/` and are reproducible.
- Performance regressions in benchmarks block release.

## 14. Public API Stability

- Anything under `vid2llm.<name>` exported in `src/vid2llm/__init__.py` is **public API** and follows semver.
- Anything starting with underscore or living in an underscored module is **internal** and may change without notice.
- Deprecations: emit `DeprecationWarning` for one minor version before removal.

## 15. Anti-Patterns (Forbidden)

- Mutable default arguments.
- Global mutable state.
- Monkey-patching third-party libraries.
- `eval`, `exec` on user input.
- Bare `try` / `except`.
- Hardcoded paths, credentials, or URLs in source.
- AI self-attribution anywhere in the codebase or its metadata.
- Em-dashes in any documentation, comment, or string literal authored for the project.
- Markdown tables generated as pretty-printed alternatives to actual data structures.
