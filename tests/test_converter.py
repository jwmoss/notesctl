"""Tests for Markdown converter."""

from datetime import datetime

import pytest

from notesctl.converter.markdown import MarkdownConverter, MarkdownOptions
from notesctl.database.models import Attachment, Note
from notesctl.parser.note_parser import Paragraph, ParsedNote, StyleType, TextRun


class TestMarkdownConverter:
    """Tests for MarkdownConverter."""

    @pytest.fixture
    def converter(self) -> MarkdownConverter:
        """Create a converter instance."""
        return MarkdownConverter()

    @pytest.fixture
    def sample_note(self) -> Note:
        """Create a sample note."""
        return Note(
            id=1,
            title="Test Note",
            created=datetime(2024, 1, 15, 10, 30, 0),
            modified=datetime(2024, 1, 15, 14, 22, 0),
            folder="Work",
        )

    def test_frontmatter_generation(self, converter: MarkdownConverter, sample_note: Note):
        """Test YAML frontmatter is generated correctly."""
        parsed = ParsedNote(title="Test Note")
        result = converter.convert(sample_note, parsed)

        assert "---" in result
        assert 'title: "Test Note"' in result
        assert "created: 2024-01-15T10:30:00" in result
        assert "modified: 2024-01-15T14:22:00" in result
        assert 'folder: "Work"' in result

    def test_no_frontmatter(self, sample_note: Note):
        """Test conversion without frontmatter."""
        converter = MarkdownConverter(MarkdownOptions(include_frontmatter=False))
        parsed = ParsedNote(title="Test Note")
        result = converter.convert(sample_note, parsed)

        assert "---" not in result

    def test_title_heading(self, converter: MarkdownConverter, sample_note: Note):
        """Test title is converted to heading."""
        parsed = ParsedNote(title="Test Note")
        result = converter.convert(sample_note, parsed)

        assert "# Test Note" in result

    def test_bold_formatting(self, converter: MarkdownConverter, sample_note: Note):
        """Test bold text formatting."""
        parsed = ParsedNote(
            title="Test",
            paragraphs=[Paragraph(runs=[TextRun(text="bold text", bold=True)])],
        )
        result = converter.convert(sample_note, parsed)

        assert "**bold text**" in result

    def test_italic_formatting(self, converter: MarkdownConverter, sample_note: Note):
        """Test italic text formatting."""
        parsed = ParsedNote(
            title="Test",
            paragraphs=[Paragraph(runs=[TextRun(text="italic text", italic=True)])],
        )
        result = converter.convert(sample_note, parsed)

        assert "*italic text*" in result

    def test_strikethrough_formatting(self, converter: MarkdownConverter, sample_note: Note):
        """Test strikethrough text formatting."""
        parsed = ParsedNote(
            title="Test",
            paragraphs=[Paragraph(runs=[TextRun(text="deleted", strikethrough=True)])],
        )
        result = converter.convert(sample_note, parsed)

        assert "~~deleted~~" in result

    def test_link_formatting(self, converter: MarkdownConverter, sample_note: Note):
        """Test link formatting."""
        parsed = ParsedNote(
            title="Test",
            paragraphs=[Paragraph(runs=[TextRun(text="click here", link="https://example.com")])],
        )
        result = converter.convert(sample_note, parsed)

        assert "[click here](https://example.com)" in result

    def test_bullet_list(self, converter: MarkdownConverter, sample_note: Note):
        """Test bullet list formatting."""
        parsed = ParsedNote(
            title="Test",
            paragraphs=[
                Paragraph(
                    runs=[TextRun(text="Item 1")],
                    style=StyleType.DOTTED_LIST,
                ),
                Paragraph(
                    runs=[TextRun(text="Item 2")],
                    style=StyleType.DOTTED_LIST,
                ),
            ],
        )
        result = converter.convert(sample_note, parsed)

        assert "- Item 1" in result
        assert "- Item 2" in result

    def test_numbered_list(self, converter: MarkdownConverter, sample_note: Note):
        """Test numbered list formatting."""
        parsed = ParsedNote(
            title="Test",
            paragraphs=[
                Paragraph(
                    runs=[TextRun(text="First")],
                    style=StyleType.NUMBERED_LIST,
                    list_item_number=1,
                ),
                Paragraph(
                    runs=[TextRun(text="Second")],
                    style=StyleType.NUMBERED_LIST,
                    list_item_number=2,
                ),
            ],
        )
        result = converter.convert(sample_note, parsed)

        assert "1. First" in result
        assert "2. Second" in result

    def test_checklist(self, converter: MarkdownConverter, sample_note: Note):
        """Test checklist formatting."""
        parsed = ParsedNote(
            title="Test",
            paragraphs=[
                Paragraph(
                    runs=[TextRun(text="Todo item")],
                    is_checklist=True,
                    checklist_checked=False,
                ),
                Paragraph(
                    runs=[TextRun(text="Done item")],
                    is_checklist=True,
                    checklist_checked=True,
                ),
            ],
        )
        result = converter.convert(sample_note, parsed)

        assert "- [ ] Todo item" in result
        assert "- [x] Done item" in result

    def test_heading_styles(self, converter: MarkdownConverter, sample_note: Note):
        """Test heading style conversion."""
        parsed = ParsedNote(
            title="Test",
            paragraphs=[
                Paragraph(
                    runs=[TextRun(text="Title")],
                    style=StyleType.TITLE,
                ),
                Paragraph(
                    runs=[TextRun(text="Heading")],
                    style=StyleType.HEADING,
                ),
                Paragraph(
                    runs=[TextRun(text="Subheading")],
                    style=StyleType.SUBHEADING,
                ),
            ],
        )
        result = converter.convert(sample_note, parsed)

        assert "# Title" in result
        assert "## Heading" in result
        assert "### Subheading" in result

    def test_blockquote(self, converter: MarkdownConverter, sample_note: Note):
        """Test blockquote formatting."""
        parsed = ParsedNote(
            title="Test",
            paragraphs=[
                Paragraph(
                    runs=[TextRun(text="Quoted text")],
                    is_blockquote=True,
                ),
            ],
        )
        result = converter.convert(sample_note, parsed)

        assert "> Quoted text" in result

    def test_image_attachment(self, converter: MarkdownConverter, sample_note: Note):
        """Test image attachment formatting."""
        attachment = Attachment(
            identifier="abc123",
            filename="photo.jpg",
            mime_type="image/jpeg",
            media_path=None,
            note_id=1,
        )
        parsed = ParsedNote(
            title="Test",
            paragraphs=[Paragraph(runs=[TextRun(text="", attachment_id="abc123")])],
        )
        result = converter.convert(sample_note, parsed, [attachment])

        assert "![photo.jpg](attachments/abc123/photo.jpg)" in result
