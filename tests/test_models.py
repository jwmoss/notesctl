"""Tests for data models."""

from datetime import datetime

from notesctl.database.models import Attachment, Folder, Note


class TestNote:
    """Tests for Note model."""

    def test_safe_filename_simple(self):
        """Test safe filename with simple title."""
        note = Note(
            id=1,
            title="My Note",
            created=datetime.now(),
            modified=datetime.now(),
            folder="Notes",
        )
        assert note.safe_filename == "My Note"

    def test_safe_filename_with_special_chars(self):
        """Test safe filename removes unsafe characters."""
        note = Note(
            id=1,
            title='Note: "Test" <file>',
            created=datetime.now(),
            modified=datetime.now(),
            folder="Notes",
        )
        assert note.safe_filename == "Note_ _Test_ _file_"

    def test_safe_filename_empty(self):
        """Test safe filename with empty title."""
        note = Note(
            id=1,
            title="",
            created=datetime.now(),
            modified=datetime.now(),
            folder="Notes",
        )
        assert note.safe_filename == "untitled"

    def test_safe_filename_long(self):
        """Test safe filename truncates long titles."""
        note = Note(
            id=1,
            title="A" * 150,
            created=datetime.now(),
            modified=datetime.now(),
            folder="Notes",
        )
        assert len(note.safe_filename) == 100


class TestAttachment:
    """Tests for Attachment model."""

    def test_is_image_by_mime_type(self):
        """Test image detection by MIME type."""
        attachment = Attachment(
            identifier="test",
            filename="photo.jpg",
            mime_type="image/jpeg",
            media_path=None,
            note_id=1,
        )
        assert attachment.is_image is True

    def test_is_image_by_extension(self):
        """Test image detection by file extension."""
        attachment = Attachment(
            identifier="test",
            filename="photo.PNG",
            mime_type=None,
            media_path=None,
            note_id=1,
        )
        assert attachment.is_image is True

    def test_not_image(self):
        """Test non-image detection."""
        attachment = Attachment(
            identifier="test",
            filename="document.pdf",
            mime_type="application/pdf",
            media_path=None,
            note_id=1,
        )
        assert attachment.is_image is False


class TestFolder:
    """Tests for Folder model."""

    def test_folder_creation(self):
        """Test folder creation."""
        folder = Folder(id=1, name="Work", parent_id=None)
        assert folder.id == 1
        assert folder.name == "Work"
        assert folder.parent_id is None
