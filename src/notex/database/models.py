"""Data models for Apple Notes database entities."""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class Attachment:
    """Represents a media attachment in a note."""

    identifier: str
    filename: str | None
    mime_type: str | None
    media_path: Path | None
    note_id: int

    @property
    def is_image(self) -> bool:
        """Check if attachment is an image."""
        if self.mime_type:
            # Handle both MIME types and UTIs
            # UTIs: public.jpeg, public.png, public.heic, public.image, etc.
            # MIME: image/jpeg, image/png, etc.
            uti_lower = self.mime_type.lower()
            if uti_lower.startswith("image/"):
                return True
            if uti_lower.startswith("public."):
                image_utis = {"jpeg", "png", "gif", "heic", "heif", "tiff", "bmp", "image"}
                uti_type = uti_lower.replace("public.", "")
                return uti_type in image_utis
        if self.filename:
            return self.filename.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".heic"))
        return False


@dataclass
class Folder:
    """Represents a Notes folder."""

    id: int
    name: str
    parent_id: int | None = None
    identifier: str | None = None


@dataclass
class Note:
    """Represents an Apple Note with its content and metadata."""

    id: int
    title: str
    created: datetime
    modified: datetime
    folder: str
    folder_id: int | None = None
    content_data: bytes | None = None
    is_encrypted: bool = False
    is_pinned: bool = False
    is_trashed: bool = False
    identifier: str | None = None
    attachments: list[Attachment] = field(default_factory=list)

    @property
    def safe_filename(self) -> str:
        """Generate a safe filename from the note title."""
        # Remove or replace characters that are problematic in filenames
        unsafe_chars = '<>:"/\\|?*'
        safe_title = self.title
        for char in unsafe_chars:
            safe_title = safe_title.replace(char, "_")
        # Limit length and strip whitespace
        safe_title = safe_title.strip()[:100]
        return safe_title or "untitled"
