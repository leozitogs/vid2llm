# vid2llm — Project Brief

> Single source of truth for the vision, scope, and decisions behind `vid2llm`.
> This document governs every implementation choice. When in doubt, this wins.

**Author:** Leonardo Gonçalves Sobral
**Studio:** Leovox Studios
**License:** Apache License 2.0
**Status:** Pre-release (Phase 0 — Foundation)
**Last updated:** 2026-05-25

---

## 1. One-liner

`vid2llm` turns any video into LLM-ready frames. Smart sampling, scene detection, OCR, and SDK-ready output for Claude, GPT-4o, and Gemini.

## 2. Problem

Large Language Models are increasingly multimodal, but feeding video to them is still painful:

- Sending entire videos is expensive, slow, and often unsupported.
- Naive frame extraction (every Nth frame) wastes tokens on redundant content.
- Each provider (Anthropic, OpenAI, Google) has a different image format, token accounting model, and message shape.
- There is no idiomatic Python tool that bridges raw video and modern LLM SDKs.

Developers building agents, content analysis pipelines, accessibility tools, video search, or multimodal RAG end up rewriting the same pre-processing layer.

## 3. Solution

A focused Python library and CLI that:

1. Extracts frames from videos using pluggable backends (OpenCV, PyAV, ffmpeg).
2. Selects frames intelligently via multiple strategies (uniform, scene-based, motion-based, semantic similarity).
3. Optionally enriches frames with OCR and object detection.
4. Outputs results in formats ready to paste into LLM SDK calls (Anthropic, OpenAI, Google).
5. Estimates token cost before the user spends a cent.

## 4. Target Users

- **AI engineers** building multimodal agents that need to reason about video.
- **Data scientists** preparing video datasets for fine-tuning or RAG.
- **Content tooling developers** building products around video understanding.
- **Researchers** needing reproducible video sampling pipelines.

## 5. Positioning

**`vid2llm` is to video what `marker` is to PDF, what `crawl4ai` is to scraping, and what `instructor` is to structured output.** A specialized, opinionated, well-engineered bridge between raw input and modern LLMs.

We are **not** competing with:
- General-purpose video editing libraries (MoviePy, vidgear).
- Scene detection libraries (PySceneDetect — we integrate with it).
- Hosted video understanding APIs (Twelve Labs — we are the open, local alternative).

## 6. Non-Goals

To stay focused, `vid2llm` explicitly does **not** aim to:

- Edit, transcode, or transform video for human consumption.
- Replace dedicated computer vision frameworks (OpenCV, PyTorch).
- Provide a hosted service in the open-source repo.
- Support audio extraction or transcription as a first-class feature (may come later, not in v1.0).
- Embed proprietary or closed-source models.

## 7. Product Surface

| Surface | Purpose | Status |
|---|---|---|
| Python library (`vid2llm`) | Programmatic API for integration into pipelines | Phase 0–1 |
| Command-line interface (`vid2llm` command) | One-shot usage for scripts and exploration | Phase 0–1 |
| GitHub Action | Run `vid2llm` in CI on video assets in repos | Phase 4 |

## 8. Phased Roadmap

| Phase | Focus | Outcome |
|---|---|---|
| **0. Foundation** | Engineering baseline, repo scaffolding, CI/CD, docs skeleton | Empty but professional repo, ready to accept features |
| **1. Turbo Extractor** | Pluggable backends, streaming, parallelism, polished CLI | `v0.1.0` — useful frame extraction tool |
| **2. Intelligence** | Smart sampling strategies (scene, motion, semantic similarity), OCR, object detection | `v0.5.0` — differentiated tool |
| **3. LLM Layer** | Provider adapters (Anthropic, OpenAI, Google), token estimation, SDK-ready output, `analyze_video()` high-level API | `v1.0.0` — the killer feature, public launch |
| **4. Growth** | GitHub Action, integrations (LangChain, LlamaIndex), benchmarks, cookbooks, community | Sustained traction |

## 9. Locked Technical Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Minimum Python | 3.11+ | Performance improvements, modern typing, still broadly available |
| Build backend | `hatchling` | PyPA recommended, simple, fast |
| Package manager (dev) | `uv` | 10–100x faster than pip, modern lockfile |
| Project layout | `src/` | Industry standard, prevents accidental imports during tests |
| Linter/formatter | `ruff` | Single tool, replaces black + isort + flake8 |
| Type checker | `mypy` in strict mode | Senior-grade type safety |
| Test framework | `pytest` + `pytest-cov` + `pytest-xdist` | Standard, parallel test execution |
| CLI framework | `typer` | Modern, type-safe, integrates with `rich` |
| Terminal UI | `rich` | Progress bars, tables, logs |
| Docs framework | `mkdocs-material` | Best-in-class, used by FastAPI, Pydantic |
| CI/CD | GitHub Actions | Native to platform |
| Pre-commit | `pre-commit` framework | Catches issues before commit |
| Versioning | `hatch-vcs` (tag-based) | Single source of truth: git tags |
| Commit convention | Conventional Commits | Enables automated changelog |
| Changelog generator | `git-cliff` | Reads conventional commits, generates `CHANGELOG.md` |
| Branching strategy | Trunk-based | `main` always green, short feature branches, PR-based |
| License | Apache 2.0 | Permissive use, explicit patent grant, industry standard for AI projects |
| Public language | English | Code, docs, commits, issues — to attract global community |
| Internal language | Portuguese (BR) | Communication between PO and Designer |

## 10. Brand and Voice

`vid2llm` is presented as a **professional, focused, opinionated open-source project**. Tone for all public-facing content:

- **Confident, not boastful.** State what it does. Show benchmarks.
- **Direct, not verbose.** Short sentences. Concrete examples first.
- **Technical, not academic.** Code samples over prose explanations.
- **Modern, not trendy.** No emojis in serious docs. No buzzwords.

The README opens with a one-line value proposition, a minimal install command, and a five-line usage example. Anything else comes after.

## 11. Success Metrics

The project is considered successful when:

- **v1.0.0** is published on PyPI.
- The repository has **1,000+ GitHub stars**.
- It is referenced in at least one widely-read newsletter or blog (TLDR, Bytes, Hacker News front page, r/MachineLearning top post).
- At least **5 external contributors** have merged PRs.
- It is integrated into at least one downstream project (LangChain integration, mention in a major framework's docs, etc.).

## 12. Operating Model

This project operates with three roles:

- **Product Owner (Leonardo):** Defines vision, sets priorities, validates deliverables.
- **Product Designer + Prompt Architect (Claude, conversational):** Designs architecture, defines contracts, writes precise specifications and prompts.
- **Developer (Claude Code):** Executes specifications. Produces code, tests, and documentation.

Every deliverable from the Developer is bundled as a `.zip`. No pushes, no deploys, no third-party publishing without explicit PO approval. The PO performs all git operations and is the sole human author of record.

## 13. Authorship and Anti-Attribution

This project is authored by **Leonardo Gonçalves Sobral**, founder of **Leovox Studios**. All commits, code comments, docstrings, issues, and PRs are written without any AI self-attribution. There must be no:

- `Co-Authored-By: Claude` or similar trailers in commits.
- "Generated with [tool]" footers.
- AI-tool comments or markers in source files.
- References to AI tooling in documentation written for end users.

This is a non-negotiable project standard and applies to every artifact produced.
