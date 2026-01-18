"""Parser for Apple Notes gzip-compressed protobuf content."""

from __future__ import annotations

import gzip
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any

from .protobuf.notestore_pb2 import NoteStoreProto  # type: ignore[attr-defined]


class StyleType(IntEnum):
    """Paragraph style types in Apple Notes."""

    TITLE = 0
    HEADING = 1
    SUBHEADING = 2
    MONOSPACED = 4
    DOTTED_LIST = 100  # Bullet list
    DASHED_LIST = 101
    NUMBERED_LIST = 102
    CHECKLIST = 103


@dataclass
class TextRun:
    """A run of text with consistent formatting."""

    text: str
    bold: bool = False
    italic: bool = False
    underline: bool = False
    strikethrough: bool = False
    monospace: bool = False
    link: str | None = None
    attachment_id: str | None = None


@dataclass
class Paragraph:
    """A paragraph with its style and text runs."""

    runs: list[TextRun] = field(default_factory=list)
    style: StyleType | None = None
    indent: int = 0
    is_checklist: bool = False
    checklist_checked: bool = False
    is_blockquote: bool = False
    list_item_number: int | None = None  # For numbered lists

    @property
    def plain_text(self) -> str:
        """Get plain text content without formatting."""
        return "".join(run.text for run in self.runs)


@dataclass
class ParsedNote:
    """Parsed note content ready for conversion."""

    title: str
    paragraphs: list[Paragraph] = field(default_factory=list)
    attachment_ids: list[str] = field(default_factory=list)

    @property
    def plain_text(self) -> str:
        """Get full plain text content."""
        return "\n".join(p.plain_text for p in self.paragraphs)


class NoteParser:
    """Parser for Apple Notes protobuf content."""

    def __init__(self) -> None:
        """Initialize the parser."""
        self._numbered_list_counters: dict[int, int] = {}

    def parse(self, data: bytes, title: str = "Untitled") -> ParsedNote:
        """
        Parse gzip-compressed protobuf note data.

        Args:
            data: Gzip-compressed protobuf data
            title: Note title (from database)

        Returns:
            ParsedNote with parsed content
        """
        if not data:
            return ParsedNote(title=title)

        # Decompress gzip data
        try:
            decompressed = gzip.decompress(data)
        except gzip.BadGzipFile:
            # Data might not be gzipped, try raw protobuf
            decompressed = data

        # Parse protobuf
        try:
            proto = NoteStoreProto()
            proto.ParseFromString(decompressed)
        except Exception:
            # If parsing fails, return empty note
            return ParsedNote(title=title)

        return self._parse_proto(proto, title)

    def _parse_proto(self, proto: Any, title: str) -> ParsedNote:
        """Parse the protobuf message into structured content."""
        note = ParsedNote(title=title)

        if not proto.HasField("document") or not proto.document.HasField("note"):
            return note

        note_proto = proto.document.note
        text = note_proto.note_text

        # Reset numbered list counters for this note
        self._numbered_list_counters = {}

        # Process attribute runs
        position = 0
        current_paragraph = Paragraph()
        paragraphs: list[Paragraph] = []

        for attr_run in note_proto.attribute_run:
            run_length = attr_run.length
            run_text = text[position : position + run_length]
            position += run_length

            # Get paragraph style if present
            style = None
            indent = 0
            is_checklist = False
            checklist_checked = False
            is_blockquote = False

            if attr_run.HasField("paragraph_style"):
                ps = attr_run.paragraph_style
                if ps.HasField("style_type"):
                    try:
                        style = StyleType(ps.style_type)
                    except ValueError:
                        pass

                if ps.HasField("indent_amount"):
                    indent = ps.indent_amount

                if ps.HasField("checklist"):
                    is_checklist = True
                    if ps.checklist.HasField("done"):
                        checklist_checked = bool(ps.checklist.done)

                if ps.HasField("block_quote"):
                    is_blockquote = bool(ps.block_quote)

            # Get font hints for italic detection
            is_italic = False
            if attr_run.HasField("font"):
                # Font hints: 1 = italic
                if attr_run.font.HasField("font_hints"):
                    is_italic = (attr_run.font.font_hints & 1) != 0

            # Create text run with formatting
            text_run = TextRun(
                text=run_text,
                bold=attr_run.HasField("font_weight") and attr_run.font_weight > 0,
                italic=is_italic,
                underline=attr_run.HasField("underlined") and attr_run.underlined > 0,
                strikethrough=attr_run.HasField("strikethrough") and attr_run.strikethrough > 0,
                monospace=style == StyleType.MONOSPACED if style else False,
                link=attr_run.link if attr_run.HasField("link") else None,
            )

            # Check for attachment
            if attr_run.HasField("attachment_info"):
                if attr_run.attachment_info.HasField("attachment_identifier"):
                    att_id = attr_run.attachment_info.attachment_identifier
                    text_run.attachment_id = att_id
                    note.attachment_ids.append(att_id)

            # Split by newlines to create paragraphs
            lines = run_text.split("\n")
            for i, line in enumerate(lines):
                if i > 0:
                    # New paragraph on newline
                    if current_paragraph.runs or current_paragraph.style:
                        paragraphs.append(current_paragraph)
                    current_paragraph = Paragraph()

                if line or i == len(lines) - 1:
                    line_run = TextRun(
                        text=line,
                        bold=text_run.bold,
                        italic=text_run.italic,
                        underline=text_run.underline,
                        strikethrough=text_run.strikethrough,
                        monospace=text_run.monospace,
                        link=text_run.link,
                        attachment_id=text_run.attachment_id if i == 0 else None,
                    )
                    current_paragraph.runs.append(line_run)

                # Apply paragraph style to first line of this run
                if i == 0:
                    if style is not None:
                        current_paragraph.style = style
                    current_paragraph.indent = indent
                    current_paragraph.is_checklist = is_checklist
                    current_paragraph.checklist_checked = checklist_checked
                    current_paragraph.is_blockquote = is_blockquote

                    # Track numbered list items
                    if style == StyleType.NUMBERED_LIST:
                        counter_key = indent
                        self._numbered_list_counters[counter_key] = (
                            self._numbered_list_counters.get(counter_key, 0) + 1
                        )
                        current_paragraph.list_item_number = self._numbered_list_counters[
                            counter_key
                        ]

        # Add final paragraph
        if current_paragraph.runs:
            paragraphs.append(current_paragraph)

        note.paragraphs = paragraphs
        return note
