# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-01-17

### Added

- Initial release
- `notex export` command to export notes to Markdown files
- `notex list-notes` command to list notes in the database
- `notex list-folders` command to list folders
- `notex stats` command to show database statistics
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

[Unreleased]: https://github.com/jwmoss/notex/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/jwmoss/notex/releases/tag/v0.1.0
