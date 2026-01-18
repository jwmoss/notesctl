"""Note exporter that orchestrates the export process."""

import shutil
from dataclasses import dataclass
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, TaskID

from .converter.markdown import MarkdownConverter, MarkdownOptions
from .database import Note, NotesQueries, SafeNotesDatabase
from .parser import NoteParser, ParsedNote

console = Console()


@dataclass
class ExportResult:
    """Result of an export operation."""

    total_notes: int
    exported_notes: int
    skipped_encrypted: int
    skipped_errors: int
    attachments_copied: int
    output_path: Path
    exported_files: list[Path]
    errors: list[str]


@dataclass
class ExportOptions:
    """Options for export operation."""

    output_dir: Path
    folder_name: str | None = None
    include_trashed: bool = False
    include_frontmatter: bool = True
    dry_run: bool = False
    organize_by_folder: bool = True


class NotesExporter:
    """Exports Apple Notes to Markdown files."""

    def __init__(self, db_path: Path | None = None):
        """Initialize exporter with optional custom database path."""
        self.db_path = db_path
        self.parser = NoteParser()

    def export(
        self,
        options: ExportOptions,
        progress: Progress | None = None,
    ) -> ExportResult:
        """
        Export notes to Markdown files.

        Args:
            options: Export options
            progress: Optional Rich progress bar

        Returns:
            ExportResult with statistics
        """
        result = ExportResult(
            total_notes=0,
            exported_notes=0,
            skipped_encrypted=0,
            skipped_errors=0,
            attachments_copied=0,
            output_path=options.output_dir,
            exported_files=[],
            errors=[],
        )

        with SafeNotesDatabase(self.db_path) as db:
            queries = NotesQueries(db)

            # Get folder filter if specified
            folder_id = None
            if options.folder_name:
                folder = queries.get_folder_by_name(options.folder_name)
                if folder:
                    folder_id = folder.id
                else:
                    result.errors.append(f"Folder '{options.folder_name}' not found")
                    return result

            # Get notes
            notes = queries.get_notes(
                folder_id=folder_id,
                include_trashed=options.include_trashed,
            )
            result.total_notes = len(notes)

            if not notes:
                return result

            # Create output directory (unless dry run)
            if not options.dry_run:
                options.output_dir.mkdir(parents=True, exist_ok=True)

            # Set up progress tracking
            task: TaskID | None = None
            if progress:
                task = progress.add_task("Exporting notes...", total=len(notes))

            # Export each note
            converter = MarkdownConverter(
                MarkdownOptions(include_frontmatter=options.include_frontmatter)
            )

            for note in notes:
                try:
                    self._export_note(
                        note=note,
                        queries=queries,
                        converter=converter,
                        options=options,
                        result=result,
                    )
                except Exception as e:
                    result.skipped_errors += 1
                    result.errors.append(f"Error exporting '{note.title}': {e}")

                if progress and task is not None:
                    progress.update(task, advance=1)

        return result

    def _export_note(
        self,
        note: Note,
        queries: NotesQueries,
        converter: MarkdownConverter,
        options: ExportOptions,
        result: ExportResult,
    ) -> None:
        """Export a single note."""
        # Skip encrypted notes
        if note.is_encrypted:
            result.skipped_encrypted += 1
            return

        # Parse note content
        parsed: ParsedNote
        if note.content_data:
            parsed = self.parser.parse(note.content_data, note.title)
        else:
            parsed = ParsedNote(title=note.title)

        # Get attachments
        attachments = queries.get_note_attachments(note.id)
        note.attachments = attachments

        # Convert to Markdown
        markdown = converter.convert(note, parsed, attachments)

        # Determine output path
        if options.organize_by_folder:
            folder_dir = options.output_dir / self._safe_folder_name(note.folder)
        else:
            folder_dir = options.output_dir

        filename = f"{note.safe_filename}.md"
        output_file = folder_dir / filename

        # Handle duplicate filenames
        counter = 1
        while output_file.exists():
            output_file = folder_dir / f"{note.safe_filename}_{counter}.md"
            counter += 1

        if options.dry_run:
            result.exported_files.append(output_file)
            result.exported_notes += 1
            return

        # Create folder and write file
        folder_dir.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        result.exported_files.append(output_file)
        result.exported_notes += 1

        # Copy attachments
        for attachment in attachments:
            if attachment.media_path and attachment.media_path.exists():
                att_dir = folder_dir / "attachments" / attachment.identifier
                att_dir.mkdir(parents=True, exist_ok=True)
                dest = att_dir / (attachment.filename or attachment.media_path.name)
                if not dest.exists():
                    shutil.copy2(attachment.media_path, dest)
                    result.attachments_copied += 1

    def _safe_folder_name(self, name: str) -> str:
        """Create a safe folder name."""
        unsafe_chars = '<>:"/\\|?*'
        safe_name = name
        for char in unsafe_chars:
            safe_name = safe_name.replace(char, "_")
        return safe_name.strip() or "Notes"

    def list_notes(
        self,
        folder_name: str | None = None,
        include_trashed: bool = False,
    ) -> list[Note]:
        """List notes with optional folder filter."""
        with SafeNotesDatabase(self.db_path) as db:
            queries = NotesQueries(db)

            folder_id = None
            if folder_name:
                folder = queries.get_folder_by_name(folder_name)
                if folder:
                    folder_id = folder.id

            return queries.get_notes(
                folder_id=folder_id,
                include_trashed=include_trashed,
            )

    def list_folders(self) -> list[tuple[str, int]]:
        """List all folders with note counts."""
        with SafeNotesDatabase(self.db_path) as db:
            queries = NotesQueries(db)
            folders = queries.get_folders()

            # Count notes per folder
            folder_counts: dict[str, int] = {}
            notes = queries.get_notes()
            for note in notes:
                folder_counts[note.folder] = folder_counts.get(note.folder, 0) + 1

            return [(f.name, folder_counts.get(f.name, 0)) for f in folders]

    def get_stats(self) -> dict[str, int]:
        """Get database statistics."""
        with SafeNotesDatabase(self.db_path) as db:
            queries = NotesQueries(db)
            return {
                "total_notes": queries.get_note_count(),
                "encrypted_notes": queries.get_encrypted_note_count(),
            }
