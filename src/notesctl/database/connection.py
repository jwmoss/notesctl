"""Safe read-only database connection for Apple Notes."""

from __future__ import annotations

import shutil
import sqlite3
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any

from rich.console import Console

if TYPE_CHECKING:
    from collections.abc import Iterator

console = Console()

# Default location of the Apple Notes database
DEFAULT_NOTES_DB = Path.home() / "Library/Group Containers/group.com.apple.notes/NoteStore.sqlite"


class SafeNotesDatabase:
    """
    Safe read-only access to Apple Notes SQLite database.

    Safety measures:
    1. Copies database + WAL + SHM to temp directory before reading
    2. Opens database in read-only mode using SQLite URI
    3. All queries are SELECT-only (enforced by this class)
    """

    def __init__(self, db_path: Path | None = None):
        """
        Initialize the database connection wrapper.

        Args:
            db_path: Path to the NoteStore.sqlite file. Uses default if not provided.
        """
        self.source_path = db_path or DEFAULT_NOTES_DB
        self._temp_dir: tempfile.TemporaryDirectory[str] | None = None
        self._temp_db_path: Path | None = None
        self._connection: sqlite3.Connection | None = None

    def _verify_source_exists(self) -> None:
        """Verify the source database exists."""
        if not self.source_path.exists():
            raise FileNotFoundError(
                f"Notes database not found at {self.source_path}. "
                "Make sure you have Apple Notes installed and have created at least one note."
            )

    def _copy_database_files(self) -> Path:
        """
        Copy database and associated files to temp directory.

        Returns:
            Path to the copied database file.
        """
        self._temp_dir = tempfile.TemporaryDirectory(prefix="notes_export_")
        temp_path = Path(self._temp_dir.name)

        # Copy main database file
        db_name = self.source_path.name
        dest_db = temp_path / db_name
        shutil.copy2(self.source_path, dest_db)

        # Copy WAL and SHM files if they exist (important for transaction consistency)
        for suffix in ["-wal", "-shm"]:
            wal_file = self.source_path.parent / f"{db_name}{suffix}"
            if wal_file.exists():
                shutil.copy2(wal_file, temp_path / f"{db_name}{suffix}")

        return dest_db

    def connect(self) -> None:
        """
        Establish a safe read-only connection to the database.

        This copies the database to a temp directory and opens it read-only.
        """
        self._verify_source_exists()
        self._temp_db_path = self._copy_database_files()

        # Open in read-only mode using SQLite URI
        # The mode=ro parameter ensures SQLite won't write to the file
        uri = f"file:{self._temp_db_path}?mode=ro"
        self._connection = sqlite3.connect(uri, uri=True)
        self._connection.row_factory = sqlite3.Row

    def close(self) -> None:
        """Close the database connection and clean up temp files."""
        if self._connection:
            self._connection.close()
            self._connection = None
        if self._temp_dir:
            self._temp_dir.cleanup()
            self._temp_dir = None
            self._temp_db_path = None

    @property
    def connection(self) -> sqlite3.Connection:
        """Get the active database connection."""
        if self._connection is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._connection

    def execute(self, query: str, params: tuple[Any, ...] = ()) -> sqlite3.Cursor:
        """
        Execute a SELECT query safely.

        Args:
            query: SQL query (must be SELECT only)
            params: Query parameters

        Returns:
            Cursor with query results

        Raises:
            ValueError: If query is not a SELECT statement
        """
        # Safety check: only allow SELECT queries
        normalized = query.strip().upper()
        if not normalized.startswith("SELECT"):
            raise ValueError("Only SELECT queries are allowed for safety")

        return self.connection.execute(query, params)

    def fetchall(self, query: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
        """Execute a query and fetch all results."""
        return list(self.execute(query, params).fetchall())

    def fetchone(self, query: str, params: tuple[Any, ...] = ()) -> sqlite3.Row | None:
        """Execute a query and fetch one result."""
        result: sqlite3.Row | None = self.execute(query, params).fetchone()
        return result

    def __enter__(self) -> SafeNotesDatabase:
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Context manager exit."""
        self.close()


@contextmanager
def get_notes_database(db_path: Path | None = None) -> Iterator[SafeNotesDatabase]:
    """
    Context manager for safe database access.

    Usage:
        with get_notes_database() as db:
            notes = db.fetchall("SELECT * FROM notes")
    """
    db = SafeNotesDatabase(db_path)
    try:
        db.connect()
        yield db
    finally:
        db.close()
