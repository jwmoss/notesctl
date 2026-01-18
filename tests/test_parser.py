"""Tests for note parser."""

import gzip

import pytest

from notesctl.parser.note_parser import NoteParser, ParsedNote, StyleType


class TestNoteParser:
    """Tests for NoteParser."""

    @pytest.fixture
    def parser(self) -> NoteParser:
        """Create a parser instance."""
        return NoteParser()

    def test_parse_empty_data(self, parser: NoteParser):
        """Test parsing empty data returns empty note."""
        result = parser.parse(b"", "Test")
        assert result.title == "Test"
        assert len(result.paragraphs) == 0

    def test_parse_none_data(self, parser: NoteParser):
        """Test parsing None data returns empty note."""
        result = parser.parse(None, "Test")  # type: ignore
        assert result.title == "Test"
        assert len(result.paragraphs) == 0

    def test_parse_invalid_gzip(self, parser: NoteParser):
        """Test parsing invalid gzip falls back to raw protobuf."""
        # Invalid data should return empty note
        result = parser.parse(b"not gzip or protobuf", "Test")
        assert result.title == "Test"

    def test_parse_invalid_protobuf(self, parser: NoteParser):
        """Test parsing valid gzip but invalid protobuf."""
        data = gzip.compress(b"not valid protobuf")
        result = parser.parse(data, "Test")
        assert result.title == "Test"

    def test_parsed_note_plain_text(self):
        """Test ParsedNote plain_text property."""
        from notesctl.parser.note_parser import Paragraph, TextRun

        note = ParsedNote(
            title="Test",
            paragraphs=[
                Paragraph(runs=[TextRun(text="Hello ")]),
                Paragraph(runs=[TextRun(text="World")]),
            ],
        )
        assert note.plain_text == "Hello \nWorld"


class TestStyleType:
    """Tests for StyleType enum."""

    def test_style_values(self):
        """Test style type values match Apple Notes format."""
        assert StyleType.TITLE == 0
        assert StyleType.HEADING == 1
        assert StyleType.SUBHEADING == 2
        assert StyleType.MONOSPACED == 4
        assert StyleType.DOTTED_LIST == 100
        assert StyleType.DASHED_LIST == 101
        assert StyleType.NUMBERED_LIST == 102
        assert StyleType.CHECKLIST == 103
