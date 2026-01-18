"""Convert parsed notes to Markdown format."""

from dataclasses import dataclass
from datetime import datetime

from ..database.models import Attachment, Note
from ..parser.note_parser import Paragraph, ParsedNote, StyleType, TextRun


@dataclass
class MarkdownOptions:
    """Options for Markdown conversion."""

    include_frontmatter: bool = True
    include_title_heading: bool = True
    attachment_folder: str = "attachments"


class MarkdownConverter:
    """Convert parsed notes to Markdown format."""

    def __init__(self, options: MarkdownOptions | None = None):
        """Initialize converter with options."""
        self.options = options or MarkdownOptions()

    def convert(
        self,
        note: Note,
        parsed: ParsedNote,
        attachments: list[Attachment] | None = None,
    ) -> str:
        """
        Convert a parsed note to Markdown.

        Args:
            note: Note metadata from database
            parsed: Parsed note content
            attachments: Optional list of attachments

        Returns:
            Markdown string
        """
        parts: list[str] = []

        # YAML frontmatter
        if self.options.include_frontmatter:
            parts.append(self._generate_frontmatter(note))
            parts.append("")  # Blank line after frontmatter

        # Title as heading
        if self.options.include_title_heading:
            parts.append(f"# {note.title}")
            parts.append("")

        # Filter out duplicate title paragraph if we're already including the title
        paragraphs_to_convert = parsed.paragraphs
        if self.options.include_title_heading and paragraphs_to_convert:
            first_para = paragraphs_to_convert[0]
            # Skip first paragraph if it's a title that matches the note title
            if (
                first_para.style == StyleType.TITLE
                and first_para.plain_text.strip() == note.title.strip()
            ):
                paragraphs_to_convert = paragraphs_to_convert[1:]

        # Convert paragraphs
        attachment_map = {a.identifier: a for a in (attachments or [])}
        converted_paragraphs = self._convert_paragraphs(paragraphs_to_convert, attachment_map)
        parts.extend(converted_paragraphs)

        return "\n".join(parts)

    def _generate_frontmatter(self, note: Note) -> str:
        """Generate YAML frontmatter."""
        lines = ["---"]
        lines.append(f'title: "{self._escape_yaml_string(note.title)}"')
        lines.append(f"created: {self._format_datetime(note.created)}")
        lines.append(f"modified: {self._format_datetime(note.modified)}")
        lines.append(f'folder: "{self._escape_yaml_string(note.folder)}"')

        if note.is_pinned:
            lines.append("pinned: true")

        lines.append("---")
        return "\n".join(lines)

    def _escape_yaml_string(self, s: str) -> str:
        """Escape a string for YAML."""
        return s.replace("\\", "\\\\").replace('"', '\\"')

    def _format_datetime(self, dt: datetime) -> str:
        """Format datetime for frontmatter."""
        return dt.strftime("%Y-%m-%dT%H:%M:%S")

    def _convert_paragraphs(
        self,
        paragraphs: list[Paragraph],
        attachment_map: dict[str, Attachment],
    ) -> list[str]:
        """Convert paragraphs to Markdown lines."""
        lines: list[str] = []
        prev_style: StyleType | None = None
        in_list = False

        for para in paragraphs:
            # Handle list transitions - add blank line before new list
            is_list = (
                para.style
                in (
                    StyleType.DOTTED_LIST,
                    StyleType.DASHED_LIST,
                    StyleType.NUMBERED_LIST,
                    StyleType.CHECKLIST,
                )
                or para.is_checklist
            )

            should_add_blank = (is_list and not in_list and lines and lines[-1]) or (
                not is_list and in_list and lines and lines[-1]
            )
            if should_add_blank:
                lines.append("")

            in_list = is_list

            # Skip empty paragraphs but preserve blank lines
            # But don't skip paragraphs with attachments
            has_attachment = any(run.attachment_id for run in para.runs)
            if not para.runs or (not para.plain_text.strip() and not has_attachment):
                if lines and lines[-1] != "":
                    lines.append("")
                continue

            line = self._convert_paragraph(para, attachment_map, prev_style)
            lines.append(line)
            prev_style = para.style

        # Clean up trailing empty lines
        while lines and lines[-1] == "":
            lines.pop()

        return lines

    def _convert_paragraph(
        self,
        para: Paragraph,
        attachment_map: dict[str, Attachment],
        prev_style: StyleType | None,  # noqa: ARG002
    ) -> str:
        """Convert a single paragraph to Markdown."""
        # Get formatted text content
        text = self._format_runs(para.runs, attachment_map)

        # Apply paragraph-level formatting
        if para.style == StyleType.TITLE:
            return f"# {text}"
        if para.style == StyleType.HEADING:
            return f"## {text}"
        if para.style == StyleType.SUBHEADING:
            return f"### {text}"
        if para.style == StyleType.MONOSPACED:
            return f"`{text}`"
        if para.style in {StyleType.DOTTED_LIST, StyleType.DASHED_LIST}:
            indent = "  " * para.indent
            return f"{indent}- {text}"
        if para.style == StyleType.NUMBERED_LIST:
            indent = "  " * para.indent
            num = para.list_item_number or 1
            return f"{indent}{num}. {text}"
        if para.is_checklist or para.style == StyleType.CHECKLIST:
            indent = "  " * para.indent
            checkbox = "[x]" if para.checklist_checked else "[ ]"
            return f"{indent}- {checkbox} {text}"
        if para.is_blockquote:
            return f"> {text}"
        return text

    def _format_runs(
        self,
        runs: list[TextRun],
        attachment_map: dict[str, Attachment],
    ) -> str:
        """Format text runs with inline Markdown."""
        parts: list[str] = []

        for run in runs:
            text = run.text

            # Handle attachment
            if run.attachment_id:
                attachment = attachment_map.get(run.attachment_id)
                if attachment and attachment.is_image:
                    # Use relative path for images
                    filename = attachment.filename or f"{run.attachment_id}.jpg"
                    img_path = f"{self.options.attachment_folder}/{run.attachment_id}/{filename}"
                    parts.append(f"![{filename}]({img_path})")
                    continue
                if attachment:
                    # Non-image attachment
                    filename = attachment.filename or run.attachment_id
                    att_path = f"{self.options.attachment_folder}/{run.attachment_id}/{filename}"
                    parts.append(f"[{filename}]({att_path})")
                    continue

            # Skip empty text
            if not text:
                continue

            # Apply inline formatting (order matters for nesting)
            formatted = text

            # Escape Markdown special characters in regular text
            if not run.monospace:
                formatted = self._escape_markdown(formatted)

            # Apply formatting
            if run.monospace:
                formatted = f"`{formatted}`"
            if run.bold:
                formatted = f"**{formatted}**"
            if run.italic:
                formatted = f"*{formatted}*"
            if run.strikethrough:
                formatted = f"~~{formatted}~~"
            if run.underline:
                # Markdown doesn't have native underline, use HTML
                formatted = f"<u>{formatted}</u>"
            if run.link:
                formatted = f"[{formatted}]({run.link})"

            parts.append(formatted)

        return "".join(parts)

    def _escape_markdown(self, text: str) -> str:
        """Escape Markdown special characters."""
        # Only escape characters that would be interpreted as Markdown
        # Be conservative to avoid over-escaping
        chars_to_escape = ["\\", "`", "*", "_", "[", "]", "#"]
        result = text
        for char in chars_to_escape:
            result = result.replace(char, f"\\{char}")
        return result
