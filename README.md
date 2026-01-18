# notex

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
uv run notex export -o ~/notes-backup

# Export specific folder
uv run notex export --folder "Work" -o ~/work-notes

# Preview without writing (safe)
uv run notex export --dry-run

# List notes
uv run notex list-notes

# List folders
uv run notex list-folders

# Show statistics
uv run notex stats
```

## Safety

This tool prioritizes safety:

1. **Copy-first**: Database files are copied to temp directory before reading
2. **Read-only**: SQLite connection uses URI mode=ro
3. **SELECT only**: All queries are validated to be SELECT statements
4. **Dry-run mode**: Preview exports without writing files

## Development

```bash
# Install dev dependencies
uv pip install -e ".[dev]"

# Run tests
uv run pytest

# Run linter
uv run ruff check src tests

# Run type checker
uv run mypy src

# Format code
uv run ruff format src tests
```

## Requirements

- macOS with Apple Notes
- Python 3.11+
- uv (recommended) or pip
