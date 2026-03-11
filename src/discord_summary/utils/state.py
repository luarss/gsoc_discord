"""State management for incremental exports."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ChannelState:
    """State for a single channel."""

    last_message_id: str | None = None
    total_exported: int = 0


@dataclass
class ExportState:
    """State tracking for incremental exports."""

    channels: dict[int, ChannelState] = field(default_factory=dict)

    def get_channel_state(self, channel_id: int) -> ChannelState:
        """Get or create state for a channel."""
        if channel_id not in self.channels:
            self.channels[channel_id] = ChannelState()
        return self.channels[channel_id]

    def update_channel(
        self, channel_id: int, last_message_id: str, count: int
    ) -> None:
        """Update channel state after export."""
        state = self.get_channel_state(channel_id)
        state.last_message_id = last_message_id
        state.total_exported += count

    def to_dict(self) -> dict[str, Any]:
        """Serialize state to dictionary."""
        return {
            "channels": {
                str(ch_id): {
                    "last_message_id": state.last_message_id,
                    "total_exported": state.total_exported,
                }
                for ch_id, state in self.channels.items()
            }
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExportState":
        """Deserialize state from dictionary."""
        state = cls()
        for ch_id_str, ch_data in data.get("channels", {}).items():
            ch_id = int(ch_id_str)
            state.channels[ch_id] = ChannelState(
                last_message_id=ch_data.get("last_message_id"),
                total_exported=ch_data.get("total_exported", 0),
            )
        return state

    def save(self, path: Path) -> None:
        """Save state to JSON file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: Path) -> "ExportState":
        """Load state from JSON file, or return empty state if not found."""
        if not path.exists():
            return cls()
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            return cls.from_dict(data)
        except (json.JSONDecodeError, KeyError):
            return cls()
