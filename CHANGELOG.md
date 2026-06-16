# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Frame extraction orchestrator with streaming `extract_frames` and collecting `extract_to_list`.
- Frame to disk serialization supporting jpg, png, and webp via Pillow.
- Functional CLI with `extract` and `probe` commands.
- Three pluggable backends (opencv, pyav, ffmpeg) with automatic selection.

## [0.1.1] - 2026-06-16

### Changed
- Corrected the published package description and project metadata on PyPI to reflect the shipped v0.1.0 functionality.

### Deprecated

### Removed

### Fixed

### Security
