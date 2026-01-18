"""Tests for safe database connection."""

import sqlite3
from pathlib import Path

import pytest

from notesctl.database.connection import SafeNotesDatabase


class TestSafeNotesDatabase:
    """Tests for SafeNotesDatabase safety features."""

    @pytest.fixture
    def mock_db(self, tmp_path: Path) -> Path:
        """Create a mock SQLite database for testing."""
        db_path = tmp_path / "NoteStore.sqlite"
        conn = sqlite3.connect(db_path)
        conn.execute("""
            CREATE TABLE test_table (
                id INTEGER PRIMARY KEY,
                value TEXT
            )
        """)
        conn.execute("INSERT INTO test_table (value) VALUES ('test')")
        conn.commit()
        conn.close()
        return db_path

    def test_select_query_allowed(self, mock_db: Path):
        """Test that SELECT queries are allowed."""
        with SafeNotesDatabase(mock_db) as db:
            result = db.fetchall("SELECT * FROM test_table")
            assert len(result) == 1
            assert result[0]["value"] == "test"

    def test_insert_query_blocked(self, mock_db: Path):
        """Test that INSERT queries are blocked."""
        with SafeNotesDatabase(mock_db) as db:
            with pytest.raises(ValueError, match="Only SELECT queries"):
                db.execute("INSERT INTO test_table (value) VALUES ('bad')")

    def test_update_query_blocked(self, mock_db: Path):
        """Test that UPDATE queries are blocked."""
        with SafeNotesDatabase(mock_db) as db:
            with pytest.raises(ValueError, match="Only SELECT queries"):
                db.execute("UPDATE test_table SET value = 'bad'")

    def test_delete_query_blocked(self, mock_db: Path):
        """Test that DELETE queries are blocked."""
        with SafeNotesDatabase(mock_db) as db:
            with pytest.raises(ValueError, match="Only SELECT queries"):
                db.execute("DELETE FROM test_table")

    def test_drop_query_blocked(self, mock_db: Path):
        """Test that DROP queries are blocked."""
        with SafeNotesDatabase(mock_db) as db:
            with pytest.raises(ValueError, match="Only SELECT queries"):
                db.execute("DROP TABLE test_table")

    def test_database_not_found(self, tmp_path: Path):
        """Test error when database doesn't exist."""
        db_path = tmp_path / "nonexistent.sqlite"
        db = SafeNotesDatabase(db_path)
        with pytest.raises(FileNotFoundError):
            db.connect()

    def test_context_manager_cleanup(self, mock_db: Path):
        """Test that temp files are cleaned up."""
        db = SafeNotesDatabase(mock_db)
        with db:
            temp_dir = db._temp_dir
            assert temp_dir is not None
            temp_path = Path(temp_dir.name)
            assert temp_path.exists()

        # After context exit, temp dir should be cleaned up
        assert db._temp_dir is None
        assert db._connection is None

    def test_original_db_unchanged(self, mock_db: Path):
        """Test that original database is not modified."""
        # Get original checksum
        original_content = mock_db.read_bytes()

        with SafeNotesDatabase(mock_db) as db:
            # Attempt to modify (should fail)
            try:
                db.execute("INSERT INTO test_table (value) VALUES ('bad')")
            except ValueError:
                pass  # Expected

        # Verify original unchanged
        assert mock_db.read_bytes() == original_content
