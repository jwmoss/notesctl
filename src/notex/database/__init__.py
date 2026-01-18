"""Database access layer for Apple Notes SQLite database."""

from .connection import SafeNotesDatabase
from .models import Attachment, Folder, Note
from .queries import NotesQueries

__all__ = ["Attachment", "Folder", "Note", "NotesQueries", "SafeNotesDatabase"]
