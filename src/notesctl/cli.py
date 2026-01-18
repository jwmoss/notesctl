"""Command-line interface for notesctl."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from .exporter import ExportOptions, NotesExporter

app = typer.Typer(
    name="notesctl",
    help="Export Apple iCloud Notes to Markdown files.",
    no_args_is_help=True,
)
console = Console()


@app.command()
def export(
    output: Annotated[
        Path,
        typer.Option(
            "-o",
            "--output",
            help="Output directory for exported notes",
        ),
    ] = Path("./notes-export"),
    folder: Annotated[
        str | None,
        typer.Option(
            "--folder",
            "-f",
            help="Only export notes from this folder",
        ),
    ] = None,
    include_trashed: Annotated[
        bool,
        typer.Option(
            "--include-trashed",
            help="Include notes in trash",
        ),
    ] = False,
    no_frontmatter: Annotated[
        bool,
        typer.Option(
            "--no-frontmatter",
            help="Don't include YAML frontmatter",
        ),
    ] = False,
    flat: Annotated[
        bool,
        typer.Option(
            "--flat",
            help="Don't organize by folder",
        ),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            "-n",
            help="Preview what would be exported without writing files",
        ),
    ] = False,
    db_path: Annotated[
        Path | None,
        typer.Option(
            "--db",
            help="Path to NoteStore.sqlite (uses default if not specified)",
            hidden=True,
        ),
    ] = None,
) -> None:
    """Export Apple Notes to Markdown files."""
    exporter = NotesExporter(db_path)

    options = ExportOptions(
        output_dir=output.expanduser().resolve(),
        folder_name=folder,
        include_trashed=include_trashed,
        include_frontmatter=not no_frontmatter,
        dry_run=dry_run,
        organize_by_folder=not flat,
    )

    if dry_run:
        console.print("[yellow]DRY RUN[/yellow] - No files will be written\n")

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            result = exporter.export(options, progress)
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from None
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from None

    # Print results
    console.print()
    if dry_run:
        console.print(f"[bold]Would export {result.exported_notes} notes[/bold]")
        if result.exported_files:
            console.print("\nFiles that would be created:")
            for f in result.exported_files[:20]:
                console.print(f"  {f}")
            if len(result.exported_files) > 20:
                console.print(f"  ... and {len(result.exported_files) - 20} more")
    else:
        console.print(f"[green]Exported {result.exported_notes} notes[/green]")
        console.print(f"  Output: {result.output_path}")
        console.print(f"  Attachments copied: {result.attachments_copied}")

    if result.skipped_encrypted:
        console.print(f"[yellow]Skipped {result.skipped_encrypted} encrypted notes[/yellow]")

    if result.skipped_errors:
        console.print(f"[red]Failed to export {result.skipped_errors} notes[/red]")

    if result.errors:
        console.print("\n[red]Errors:[/red]")
        for error in result.errors[:10]:
            console.print(f"  {error}")


@app.command("list-notes")
def list_notes(
    folder: Annotated[
        str | None,
        typer.Option(
            "--folder",
            "-f",
            help="Only list notes from this folder",
        ),
    ] = None,
    include_trashed: Annotated[
        bool,
        typer.Option(
            "--include-trashed",
            help="Include notes in trash",
        ),
    ] = False,
    limit: Annotated[
        int,
        typer.Option(
            "--limit",
            "-l",
            help="Maximum number of notes to show",
        ),
    ] = 50,
    db_path: Annotated[
        Path | None,
        typer.Option(
            "--db",
            help="Path to NoteStore.sqlite",
            hidden=True,
        ),
    ] = None,
) -> None:
    """List notes in the database."""
    exporter = NotesExporter(db_path)

    try:
        notes = exporter.list_notes(folder, include_trashed)
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from None
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from None

    if not notes:
        console.print("No notes found.")
        return

    table = Table(title=f"Notes ({len(notes)} total)")
    table.add_column("Title", style="cyan", no_wrap=True, max_width=50)
    table.add_column("Folder", style="green")
    table.add_column("Modified", style="yellow")
    table.add_column("Status", style="dim")

    for note in notes[:limit]:
        status_parts = []
        if note.is_encrypted:
            status_parts.append("🔒")
        if note.is_pinned:
            status_parts.append("📌")
        if note.is_trashed:
            status_parts.append("🗑️")

        table.add_row(
            note.title[:50],
            note.folder,
            note.modified.strftime("%Y-%m-%d %H:%M"),
            " ".join(status_parts),
        )

    console.print(table)

    if len(notes) > limit:
        console.print(
            f"\n[dim]Showing {limit} of {len(notes)} notes. Use --limit to see more.[/dim]"
        )


@app.command("list-folders")
def list_folders(
    db_path: Annotated[
        Path | None,
        typer.Option(
            "--db",
            help="Path to NoteStore.sqlite",
            hidden=True,
        ),
    ] = None,
) -> None:
    """List all folders in Notes."""
    exporter = NotesExporter(db_path)

    try:
        folders = exporter.list_folders()
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from None
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from None

    if not folders:
        console.print("No folders found.")
        return

    table = Table(title="Notes Folders")
    table.add_column("Folder", style="cyan")
    table.add_column("Notes", style="green", justify="right")

    for name, count in sorted(folders, key=lambda x: x[0].lower()):
        table.add_row(name, str(count))

    console.print(table)


@app.command("stats")
def stats(
    db_path: Annotated[
        Path | None,
        typer.Option(
            "--db",
            help="Path to NoteStore.sqlite",
            hidden=True,
        ),
    ] = None,
) -> None:
    """Show statistics about your Notes database."""
    exporter = NotesExporter(db_path)

    try:
        db_stats = exporter.get_stats()
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from None
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from None

    console.print("[bold]Notes Database Statistics[/bold]\n")
    console.print(f"  Total notes: {db_stats['total_notes']}")
    console.print(f"  Encrypted notes: {db_stats['encrypted_notes']}")
    console.print(f"  Exportable: {db_stats['total_notes'] - db_stats['encrypted_notes']}")


def main() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
