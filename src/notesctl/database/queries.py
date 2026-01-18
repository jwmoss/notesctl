"""SQL queries for reading Apple Notes data (SELECT only)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .models import Attachment, Folder, Note

if TYPE_CHECKING:
    from .connection import SafeNotesDatabase

# Apple's Core Data timestamp epoch (2001-01-01 00:00:00 UTC)
APPLE_EPOCH = datetime(2001, 1, 1, tzinfo=UTC)


def apple_timestamp_to_datetime(timestamp: float | None) -> datetime:
    """Convert Apple Core Data timestamp to Python datetime."""
    if timestamp is None:
        return datetime.now(tz=UTC)
    # Apple timestamps are seconds since 2001-01-01
    return datetime.fromtimestamp(timestamp + APPLE_EPOCH.timestamp(), tz=UTC)


class NotesQueries:
    """Query class for extracting notes data from Apple Notes database."""

    # Path to media attachments relative to Notes container
    MEDIA_BASE = Path.home() / "Library/Group Containers/group.com.apple.notes"

    def __init__(self, db: SafeNotesDatabase):
        """Initialize with database connection."""
        self.db = db

    def get_folders(self) -> list[Folder]:
        """
        Get all non-system folders.

        Returns:
            List of Folder objects
        """
        query = """
        SELECT
            Z_PK as id,
            ZTITLE2 as name,
            ZPARENT as parent_id,
            ZIDENTIFIER as identifier
        FROM ZICCLOUDSYNCINGOBJECT
        WHERE ZTITLE2 IS NOT NULL
          AND ZMARKEDFORDELETION != 1
        ORDER BY ZTITLE2
        """
        rows = self.db.fetchall(query)
        return [
            Folder(
                id=row["id"],
                name=row["name"],
                parent_id=row["parent_id"],
                identifier=row["identifier"],
            )
            for row in rows
        ]

    def get_folder_by_name(self, name: str) -> Folder | None:
        """Get a folder by its name."""
        query = """
        SELECT
            Z_PK as id,
            ZTITLE2 as name,
            ZPARENT as parent_id,
            ZIDENTIFIER as identifier
        FROM ZICCLOUDSYNCINGOBJECT
        WHERE ZTITLE2 = ?
          AND ZMARKEDFORDELETION != 1
        LIMIT 1
        """
        row = self.db.fetchone(query, (name,))
        if row:
            return Folder(
                id=row["id"],
                name=row["name"],
                parent_id=row["parent_id"],
                identifier=row["identifier"],
            )
        return None

    def get_notes(
        self,
        folder_id: int | None = None,
        include_trashed: bool = False,
    ) -> list[Note]:
        """
        Get all notes, optionally filtered by folder.

        Args:
            folder_id: Optional folder ID to filter by
            include_trashed: Whether to include trashed notes

        Returns:
            List of Note objects with basic metadata (content loaded separately)
        """
        query = """
        SELECT
            n.Z_PK as id,
            n.ZTITLE1 as title,
            n.ZCREATIONDATE3 as created,
            n.ZMODIFICATIONDATE1 as modified,
            n.ZFOLDER as folder_id,
            n.ZIDENTIFIER as identifier,
            n.ZISPASSWORDPROTECTED as is_encrypted,
            n.ZISPINNED as is_pinned,
            n.ZMARKEDFORDELETION as is_trashed,
            f.ZTITLE2 as folder_name,
            d.ZDATA as content_data
        FROM ZICCLOUDSYNCINGOBJECT n
        LEFT JOIN ZICCLOUDSYNCINGOBJECT f ON n.ZFOLDER = f.Z_PK
        LEFT JOIN ZICNOTEDATA d ON n.ZNOTEDATA = d.Z_PK
        WHERE n.ZTITLE1 IS NOT NULL
        """

        params: list[Any] = []

        if folder_id is not None:
            query += " AND n.ZFOLDER = ?"
            params.append(folder_id)

        if not include_trashed:
            query += " AND (n.ZMARKEDFORDELETION IS NULL OR n.ZMARKEDFORDELETION != 1)"

        query += " ORDER BY n.ZMODIFICATIONDATE1 DESC"

        rows = self.db.fetchall(query, tuple(params))

        notes = []
        for row in rows:
            note = Note(
                id=row["id"],
                title=row["title"] or "Untitled",
                created=apple_timestamp_to_datetime(row["created"]),
                modified=apple_timestamp_to_datetime(row["modified"]),
                folder=row["folder_name"] or "Notes",
                folder_id=row["folder_id"],
                content_data=row["content_data"],
                is_encrypted=bool(row["is_encrypted"]),
                is_pinned=bool(row["is_pinned"]),
                is_trashed=bool(row["is_trashed"]),
                identifier=row["identifier"],
            )
            notes.append(note)

        return notes

    def get_note_attachments(self, note_id: int) -> list[Attachment]:
        """
        Get attachments for a specific note.

        Args:
            note_id: The note's primary key

        Returns:
            List of Attachment objects
        """
        query = """
        SELECT
            a.Z_PK as id,
            a.ZIDENTIFIER as identifier,
            a.ZFILENAME as filename,
            a.ZTYPEUTI as type_uti,
            a.ZMEDIA as media_id,
            m.ZFILENAME as media_filename,
            m.ZIDENTIFIER as media_identifier
        FROM ZICCLOUDSYNCINGOBJECT a
        LEFT JOIN ZICCLOUDSYNCINGOBJECT m ON a.ZMEDIA = m.Z_PK
        WHERE a.ZNOTE = ?
          AND a.ZTYPEUTI IS NOT NULL
        """
        rows = self.db.fetchall(query, (note_id,))

        attachments = []
        for row in rows:
            # Try to find the media file path
            media_path = None
            if row["media_identifier"]:
                # Look in the Media folder structure
                media_path = self._find_media_file(row["media_identifier"])

            attachment = Attachment(
                identifier=row["identifier"] or str(row["id"]),
                filename=row["filename"] or row["media_filename"],
                mime_type=row["type_uti"],  # ZTYPEUTI stores the UTI (e.g., public.jpeg)
                media_path=media_path,
                note_id=note_id,
            )
            attachments.append(attachment)

        return attachments

    def _find_media_file(self, identifier: str) -> Path | None:
        """
        Find the actual media file on disk.

        Args:
            identifier: The media identifier

        Returns:
            Path to the media file if found
        """
        # Media files are stored in Accounts/<UUID>/Media/<identifier>/
        accounts_path = self.MEDIA_BASE / "Accounts"
        if not accounts_path.exists():
            return None

        for account_dir in accounts_path.iterdir():
            if not account_dir.is_dir():
                continue
            media_dir = account_dir / "Media" / identifier
            if media_dir.exists():
                # Return the first file found in the directory
                for file in media_dir.iterdir():
                    if file.is_file() and not file.name.startswith("."):
                        return file
        return None

    def get_note_count(self) -> int:
        """Get total number of non-trashed notes."""
        query = """
        SELECT COUNT(*) as count
        FROM ZICCLOUDSYNCINGOBJECT
        WHERE ZTITLE1 IS NOT NULL
          AND (ZMARKEDFORDELETION IS NULL OR ZMARKEDFORDELETION != 1)
        """
        row = self.db.fetchone(query)
        return row["count"] if row else 0

    def get_encrypted_note_count(self) -> int:
        """Get number of encrypted notes."""
        query = """
        SELECT COUNT(*) as count
        FROM ZICCLOUDSYNCINGOBJECT
        WHERE ZTITLE1 IS NOT NULL
          AND ZISPASSWORDPROTECTED = 1
          AND (ZMARKEDFORDELETION IS NULL OR ZMARKEDFORDELETION != 1)
        """
        row = self.db.fetchone(query)
        return row["count"] if row else 0
