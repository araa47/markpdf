# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Changed

- **Drop Python 3.10 support** (`requires-python >=3.11`). Pillow 13.0.0 fixes 41 known vulnerabilities (5 critical) but requires Python 3.11+, so the lockfile's Python 3.10 fork was stuck on the vulnerable Pillow 12.3.0. Python 3.10 reached end of life in October 2026.
- Refresh dependencies (lockfile, pre-commit hooks, GitHub Actions) and drop the `pytest-asyncio<0.23` pin.
- Narrow workflow token permissions to `contents: read` (removed unused `id-token: write`).

## [0.2.0] - 2026-03-23

### Fixed

- Prevent orphaned headings at page breaks — headings no longer render alone at the bottom of a page with their content flowing to the next page. Uses `CondPageBreak`, `KeepTogether`, and `keepWithNext` for robust prevention. Thanks to [@0xlaveen](https://github.com/0xlaveen) for identifying this issue and proposing the fix in [#1](https://github.com/araa47/markpdf/pull/1).

### Added

- Tests for heading orphan prevention (structural and integration).

## [0.1.0] - 2026-03-22

### Added

- Initial release: markdown to PDF with light/dark themes, code blocks, tables, lists, images, blockquotes, task lists, extended formatting, and async remote image fetching.
