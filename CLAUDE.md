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

# Static checks and package build
make check

# Actual local Apple Notes reads (requires macOS database access)
make test
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

Keep only real end-to-end CLI tests and static checks. Do not add unit or mock tests.
Live checks must not write to the source Notes database.
