"""Tests for the command-line interface."""

from pathlib import Path
from typing import Any

from typer.testing import CliRunner

from notesctl.cli import app
from notesctl.exporter import ExportResult

runner = CliRunner()


def test_export_exits_nonzero_when_notes_fail(monkeypatch):
    """Export should fail automation when notes are skipped due to errors."""

    class StubExporter:
        def __init__(self, db_path: Path | None = None) -> None:
            self.db_path = db_path

        def export(self, *_args: Any) -> ExportResult:
            return ExportResult(
                total_notes=2,
                exported_notes=1,
                skipped_encrypted=0,
                skipped_errors=1,
                attachments_copied=0,
                output_path=Path("/tmp/notes-export"),
                exported_files=[],
                errors=["boom"],
            )

    monkeypatch.setattr("notesctl.cli.NotesExporter", StubExporter)

    result = runner.invoke(app, ["export"])

    assert result.exit_code == 1
    assert "Failed to export 1 notes" in result.output
    assert "boom" in result.output
