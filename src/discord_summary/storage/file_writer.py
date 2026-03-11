"""File system operations for exporting messages."""

import logging
from datetime import date, datetime
from pathlib import Path
from typing import TextIO

from discord_summary.config import OutputConfig

logger = logging.getLogger(__name__)


class FileWriter:
    """Handles writing exported messages to files."""

    def __init__(self, config: OutputConfig):
        self.config = config
        self._open_files: dict[Path, TextIO] = {}

    def _get_output_path(
        self, guild_name: str, channel_name: str, message_date: date
    ) -> Path:
        """Get the output file path for a channel's date."""
        # Sanitize names for filesystem
        safe_guild = self._sanitize_name(guild_name)
        safe_channel = self._sanitize_name(channel_name)
        filename = f"{message_date.isoformat()}.md"

        return self.config.directory / safe_guild / safe_channel / filename

    def _sanitize_name(self, name: str) -> str:
        """Sanitize a name for use in filesystem paths."""
        # Replace problematic characters
        replacements = {
            "/": "-",
            "\\": "-",
            ":": "-",
            "*": "",
            "?": "",
            '"': "",
            "<": "",
            ">": "",
            "|": "",
            "\n": "",
            "\r": "",
        }
        result = name.strip()
        for old, new in replacements.items():
            result = result.replace(old, new)
        return result or "unnamed"

    def write(
        self,
        guild_name: str,
        channel_name: str,
        channel_id: int,
        message_date: date,
        content: str,
    ) -> Path:
        """Write content to the appropriate file.

        Args:
            guild_name: Name of the Discord guild/server.
            channel_name: Name of the channel.
            channel_id: Discord channel ID (for metadata).
            message_date: Date of the messages.
            content: Markdown content to write.

        Returns:
            Path to the written file.
        """
        output_path = self._get_output_path(guild_name, channel_name, message_date)

        # Check if file exists to determine if we need header
        needs_header = not output_path.exists()

        # Create directories
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Append to file (grouping messages by date)
        with open(output_path, "a", encoding="utf-8") as f:
            if needs_header:
                header = self._create_header(channel_name, channel_id, message_date)
                f.write(header)
            f.write(content)
            f.write("\n")

        logger.debug(f"Wrote to {output_path}")
        return output_path

    def _create_header(
        self, channel_name: str, channel_id: int, message_date: date
    ) -> str:
        """Create the markdown header for a new file."""
        timestamp = datetime.utcnow().isoformat() + "Z"
        return f"""# #{channel_name} - {message_date.isoformat()}

> Channel: #{channel_name} (ID: {channel_id})
> Exported: {timestamp}

---

"""

    def close_all(self) -> None:
        """Close all open file handles."""
        for f in self._open_files.values():
            f.close()
        self._open_files.clear()

    def ensure_output_directory(self) -> None:
        """Ensure the output directory exists."""
        self.config.directory.mkdir(parents=True, exist_ok=True)
