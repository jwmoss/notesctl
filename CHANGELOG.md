# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.2] - 2026-01-17

### Fixed

- Fixed duplicate title headers appearing in exported markdown files
- Apple Notes stores the note title as the first paragraph with `StyleType.TITLE`, causing the title to render twice when `include_title_heading` is enabled
- Skip the first paragraph when it matches the note title to eliminate duplication

## [1.0.1] - 2026-01-17

### Fixed

- Fixed mypy strict type checking errors across database and parser modules
- Added proper type annotations for tuple parameters and return types
- Fixed type-checking imports to satisfy ruff TC rules

## [1.0.0] - 2026-01-17

### Added

- Initial stable release
- `notesctl export` command to export notes to Markdown files
- `notesctl list-notes` command to list notes in the database
- `notesctl list-folders` command to list folders
- `notesctl stats` command to show database statistics
- Safe database access with copy-first approach
- Read-only SQLite connection (mode=ro)
- SELECT-only query validation
- Dry-run mode for previewing exports
- YAML frontmatter with metadata (title, created, modified, folder)
- Support for text formatting (bold, italic, strikethrough, links)
- Support for lists (bullet, numbered, checklists)
- Support for headings and blockquotes
- Image and attachment export
- Folder-based organization of exported notes
- Encrypted note detection (skipped with warning)

### Security

- Database files are copied to temp directory before reading
- Original Notes database is never modified
- All queries validated to be SELECT statements only

[Unreleased]: https://github.com/jwmoss/notesctl/compare/v1.0.2...HEAD
[1.0.2]: https://github.com/jwmoss/notesctl/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/jwmoss/notesctl/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/jwmoss/notesctl/releases/tag/v1.0.0
