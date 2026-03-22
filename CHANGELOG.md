# Changelog

All notable changes to this project will be documented in this file.

## [0.2.0] - 2026-03-23

### Fixed

- Prevent orphaned headings at page breaks — headings no longer render alone at the bottom of a page with their content flowing to the next page. Uses `CondPageBreak`, `KeepTogether`, and `keepWithNext` for robust prevention. Thanks to [@0xlaveen](https://github.com/0xlaveen) for identifying this issue and proposing the fix in [#1](https://github.com/araa47/markpdf/pull/1).

### Added

- Tests for heading orphan prevention (structural and integration).

## [0.1.0] - 2026-03-22

### Added

- Initial release: markdown to PDF with light/dark themes, code blocks, tables, lists, images, blockquotes, task lists, extended formatting, and async remote image fetching.
