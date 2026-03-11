"""Markdown formatter for Discord messages."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class FormattedMessage:
    """A formatted message ready for output."""

    date: datetime
    content: str


class MarkdownFormatter:
    """Converts Discord messages to markdown format."""

    def __init__(
        self,
        include_attachments: bool = True,
        include_reactions: bool = True,
    ):
        self.include_attachments = include_attachments
        self.include_reactions = include_reactions

    def format_message(self, message: "DiscordMessage") -> FormattedMessage:
        """Format a single Discord message to markdown.

        Args:
            message: Discord message object with required attributes.

        Returns:
            FormattedMessage with date and markdown content.
        """
        parts: list[str] = []

        # Header with timestamp and author
        timestamp = message.created_at.strftime("%H:%M")
        author = self._escape_markdown(message.author.display_name)
        parts.append(f"### {timestamp} - @{author}\n")

        # Main content
        if message.content:
            content = self._format_content(message.content)
            parts.append(content)

        # Attachments
        if self.include_attachments and message.attachments:
            parts.append(self._format_attachments(message.attachments))

        # Reactions
        if self.include_reactions and message.reactions:
            parts.append(self._format_reactions(message.reactions))

        # Reply reference
        if message.reference:
            parts.append(self._format_reference(message.reference))

        parts.append("\n---\n")

        return FormattedMessage(
            date=message.created_at,
            content="\n".join(parts),
        )

    def _format_content(self, content: str) -> str:
        """Format message content."""
        # Handle code blocks
        # Handle mentions - just keep them as-is for now
        return content

    def _format_attachments(self, attachments: list) -> str:
        """Format message attachments."""
        lines = ["\n📎 **Attachments:**"]
        for att in attachments:
            filename = self._escape_markdown(att.filename)
            lines.append(f"- [{filename}]({att.url})")
        return "\n".join(lines)

    def _format_reactions(self, reactions: list) -> str:
        """Format message reactions."""
        lines = ["\n👍 **Reactions:**"]
        for reaction in reactions:
            emoji = str(reaction.emoji)
            count = reaction.count
            lines.append(f"- {emoji} ({count})")
        return "\n".join(lines)

    def _format_reference(self, _reference: object) -> str:
        """Format a message reference (reply)."""
        return "\n↩️ *Reply to a message*"

    def _escape_markdown(self, text: str) -> str:
        """Escape special markdown characters."""
        special_chars = ["*", "_", "`", "~", "|", ">", "#", "[", "]"]
        result = text
        for char in special_chars:
            result = result.replace(char, f"\\{char}")
        return result


# Protocol for type checking without importing discord.py
class DiscordMessage:
    """Protocol for Discord message objects."""

    @property
    def created_at(self) -> datetime:
        ...

    @property
    def author(self) -> "DiscordUser":
        ...

    @property
    def content(self) -> str:
        ...

    @property
    def attachments(self) -> list:
        ...

    @property
    def reactions(self) -> list:
        ...

    @property
    def reference(self) -> object | None:
        ...


class DiscordUser:
    """Protocol for Discord user objects."""

    @property
    def display_name(self) -> str:
        ...
