"""Tests for state management."""

from pathlib import Path
from tempfile import NamedTemporaryFile

from discord_summary.utils.state import ChannelState, ExportState


def test_channel_state_defaults() -> None:
    """Test default channel state values."""
    state = ChannelState()

    assert state.last_message_id is None
    assert state.total_exported == 0


def test_export_state_get_or_create() -> None:
    """Test getting or creating channel state."""
    state = ExportState()

    channel_state = state.get_channel_state(12345)

    assert channel_state.last_message_id is None
    assert channel_state.total_exported == 0


def test_export_state_update_channel() -> None:
    """Test updating channel state."""
    state = ExportState()

    state.update_channel(
        channel_id=12345,
        last_message_id="999999999",
        count=10,
    )

    channel_state = state.get_channel_state(12345)
    assert channel_state.last_message_id == "999999999"
    assert channel_state.total_exported == 10


def test_export_state_increment_count() -> None:
    """Test that counts increment on multiple updates."""
    state = ExportState()

    state.update_channel(12345, "100", 5)
    state.update_channel(12345, "200", 3)

    channel_state = state.get_channel_state(12345)
    assert channel_state.total_exported == 8
    assert channel_state.last_message_id == "200"


def test_export_state_serialization() -> None:
    """Test serialization to dictionary."""
    state = ExportState()
    state.update_channel(12345, "999", 10)

    data = state.to_dict()

    assert "channels" in data
    assert "12345" in data["channels"]
    assert data["channels"]["12345"]["last_message_id"] == "999"
    assert data["channels"]["12345"]["total_exported"] == 10


def test_export_state_deserialization() -> None:
    """Test deserialization from dictionary."""
    data = {
        "channels": {
            "12345": {
                "last_message_id": "999",
                "total_exported": 10,
            }
        }
    }

    state = ExportState.from_dict(data)

    channel_state = state.get_channel_state(12345)
    assert channel_state.last_message_id == "999"
    assert channel_state.total_exported == 10


def test_export_state_save_and_load() -> None:
    """Test saving and loading state from file."""
    state = ExportState()
    state.update_channel(12345, "999", 10)
    state.update_channel(67890, "888", 5)

    with NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = Path(f.name)

    try:
        state.save(temp_path)

        loaded = ExportState.load(temp_path)

        assert loaded.get_channel_state(12345).last_message_id == "999"
        assert loaded.get_channel_state(12345).total_exported == 10
        assert loaded.get_channel_state(67890).last_message_id == "888"
        assert loaded.get_channel_state(67890).total_exported == 5
    finally:
        temp_path.unlink()


def test_export_state_load_missing_file() -> None:
    """Test loading state from nonexistent file returns empty state."""
    state = ExportState.load(Path("/nonexistent/path.json"))

    assert len(state.channels) == 0
