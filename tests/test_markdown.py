"""Tests for markdown formatter."""

from datetime import datetime, timezone

from discord_summary.formatters.markdown import MarkdownFormatter


class MockUser:
    """Mock Discord user."""

    def __init__(self, display_name: str):
        self.display_name = display_name


class MockAttachment:
    """Mock Discord attachment."""

    def __init__(self, filename: str, url: str):
        self.filename = filename
        self.url = url


class MockReaction:
    """Mock Discord reaction."""

    def __init__(self, emoji: str, count: int):
        self.emoji = emoji
        self.count = count


class MockMessage:
    """Mock Discord message."""

    def __init__(
        self,
        content: str,
        author_name: str = "TestUser",
        created_at: datetime | None = None,
        attachments: list | None = None,
        reactions: list | None = None,
        reference: object | None = None,
    ):
        self.content = content
        self.author = MockUser(author_name)
        self.created_at = created_at or datetime(2024, 3, 10, 9, 15, tzinfo=timezone.utc)
        self.attachments = attachments or []
        self.reactions = reactions or []
        self.reference = reference


def test_format_simple_message() -> None:
    """Test formatting a simple message."""
    formatter = MarkdownFormatter()
    message = MockMessage(content="Hello, world!")

    result = formatter.format_message(message)

    assert result.date == message.created_at
    assert "### 09:15 - @TestUser" in result.content
    assert "Hello, world!" in result.content


def test_format_message_with_attachments() -> None:
    """Test formatting a message with attachments."""
    formatter = MarkdownFormatter(include_attachments=True)
    message = MockMessage(
        content="Here's a file",
        attachments=[
            MockAttachment("document.pdf", "https://example.com/doc.pdf")
        ],
    )

    result = formatter.format_message(message)

    assert "📎 **Attachments:**" in result.content
    assert "[document.pdf](https://example.com/doc.pdf)" in result.content


def test_format_message_without_attachments() -> None:
    """Test formatting excludes attachments when disabled."""
    formatter = MarkdownFormatter(include_attachments=False)
    message = MockMessage(
        content="Here's a file",
        attachments=[
            MockAttachment("document.pdf", "https://example.com/doc.pdf")
        ],
    )

    result = formatter.format_message(message)

    assert "📎" not in result.content


def test_format_message_with_reactions() -> None:
    """Test formatting a message with reactions."""
    formatter = MarkdownFormatter(include_reactions=True)
    message = MockMessage(
        content="Good morning!",
        reactions=[
            MockReaction("👍", 3),
            MockReaction("❤️", 2),
        ],
    )

    result = formatter.format_message(message)

    assert "👍 **Reactions:**" in result.content
    assert "👍 (3)" in result.content
    assert "❤️ (2)" in result.content


def test_format_message_without_reactions() -> None:
    """Test formatting excludes reactions when disabled."""
    formatter = MarkdownFormatter(include_reactions=False)
    message = MockMessage(
        content="Good morning!",
        reactions=[MockReaction("👍", 3)],
    )

    result = formatter.format_message(message)

    assert "👍 **Reactions:**" not in result.content


def test_format_message_with_reply() -> None:
    """Test formatting a message that is a reply."""
    formatter = MarkdownFormatter()
    message = MockMessage(
        content="I agree!",
        reference=object(),  # Simulate a reply reference
    )

    result = formatter.format_message(message)

    assert "↩️ *Reply to a message*" in result.content


def test_escape_markdown() -> None:
    """Test markdown escaping in usernames."""
    formatter = MarkdownFormatter()
    message = MockMessage(
        content="Hello",
        author_name="User_With*Special`Chars",
    )

    result = formatter.format_message(message)

    # Escaped characters should be in the output
    assert "\\*" in result.content
    assert "\\_" in result.content
    assert "\\`" in result.content
