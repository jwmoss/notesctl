# notesctl

Export Apple iCloud Notes to Markdown files safely.

## Features

- **Safe**: Copies database before reading, uses read-only mode
- **Complete**: Exports text, formatting, and attachments
- **Organized**: Groups notes by folder with YAML frontmatter

## Installation

```bash
# Using uv (recommended)
uv pip install .

# Or install in development mode
uv pip install -e ".[dev]"
```

## Usage

```bash
# Export all notes
uv run notesctl export -o ~/notes-backup

# Export specific folder
uv run notesctl export --folder "Work" -o ~/work-notes

# Preview without writing (safe)
uv run notesctl export --dry-run

# List notes
uv run notesctl list-notes

# List folders
uv run notesctl list-folders

# Show statistics
uv run notesctl stats
```

## Safety

This tool prioritizes safety:

1. **Copy-first**: Database files are copied to temp directory before reading
2. **Read-only**: SQLite connection uses URI mode=ro
3. **SELECT only**: All queries are validated to be SELECT statements
4. **Dry-run mode**: Preview exports without writing files

## Development

```bash
make check # lint, format, types, lock, package build
make test  # real local Apple Notes reads
```

Live checks require a populated Apple Notes database and macOS file access. They
read database copies and preview a Markdown export through the installed CLI.
They never write to Apple Notes or save exported notes.
CI runs static and package checks. The project has no unit or mock test suite.

Use `notesctl --version` or `notesctl version` for the package version.
Use `notesctl doctor --json` to verify database access and read note counts.
Command errors use stderr; data and tables use stdout.


## Requirements

- macOS with Apple Notes
- Python 3.11+
- uv (recommended) or pip
