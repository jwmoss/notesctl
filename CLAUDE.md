# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Development Commands

```bash
# Install dependencies (including dev tools)
uv pip install -e ".[dev]"

# Run the CLI
uv run notesctl export -o ~/notes-backup
uv run notesctl list-notes
uv run notesctl list-folders
uv run notesctl stats

# Run tests
uv run pytest                           # all tests
uv run pytest tests/test_parser.py      # single file
uv run pytest -k "test_name"            # single test by name

# Linting and type checking
uv run ruff check src tests             # lint
uv run ruff format src tests            # format
uv run ty check                          # type check
```

## Architecture

This is a CLI tool (`notesctl`) that exports Apple Notes from the iCloud SQLite database to Markdown files.

### Data Flow

1. **Database Layer** (`database/`) - Safe read-only access to Apple Notes SQLite database
   - `SafeNotesDatabase` copies the database to a temp directory before reading (for safety)
   - Opens in read-only mode (`?mode=ro`) and only allows SELECT queries
   - `NotesQueries` provides typed queries returning `Note`, `Folder`, `Attachment` models

2. **Parser Layer** (`parser/`) - Extracts content from Notes' gzip-compressed protobuf format
   - `NoteParser` decompresses and parses protobuf data into `ParsedNote` structure
   - Handles text formatting (bold, italic, links), paragraph styles (headings, lists, checklists)
   - Protobuf definitions are in `parser/protobuf/` (auto-generated `_pb2.py` files)

3. **Converter Layer** (`converter/`) - Transforms parsed notes to Markdown
   - `MarkdownConverter` generates Markdown with optional YAML frontmatter
   - Handles inline formatting, lists, blockquotes, and attachment references

4. **Exporter** (`exporter.py`) - Orchestrates the full export pipeline
   - Coordinates database queries, parsing, conversion, and file writing
   - Copies attachments from `~/Library/Group Containers/group.com.apple.notes/`

5. **CLI** (`cli.py`) - Typer-based command interface with Rich output

### Key Safety Design

The tool is designed to never modify the original Notes database:
- Database files are copied to temp directory before reading
- SQLite connection uses URI mode=ro (read-only)
- Only SELECT queries are allowed (enforced in `SafeNotesDatabase.execute()`)

### Protobuf Files

The `parser/protobuf/notestore_pb2.py` is auto-generated and excluded from ty/ruff checks. The protobuf schema defines how Apple Notes stores note content (text, formatting, attachments).
