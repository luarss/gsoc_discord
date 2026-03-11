"""Tests for configuration loading."""

from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest

from discord_summary.config import (
    Config,
    ExportConfig,
    GuildConfig,
    OutputConfig,
    ScopeConfig,
    load_config,
)


def test_default_config() -> None:
    """Test that default config values are correct."""
    config = Config()

    assert config.token is None
    assert config.scope.guilds == []
    assert config.output.directory == Path("./exports")
    assert config.export.incremental is True


def test_scope_config_with_guilds() -> None:
    """Test scope configuration with guilds."""
    scope = ScopeConfig(
        guilds=[
            GuildConfig(
                id=123456789,
                name="Test Server",
                channels=[],
            )
        ]
    )

    assert len(scope.guilds) == 1
    assert scope.guilds[0].id == 123456789
    assert scope.guilds[0].name == "Test Server"


def test_output_config_custom_directory() -> None:
    """Test custom output directory."""
    output = OutputConfig(directory=Path("/custom/path"))

    assert output.directory == Path("/custom/path")


def test_export_config_batch_size_validation() -> None:
    """Test batch size validation."""
    # Valid range
    config = ExportConfig(batch_size=100)
    assert config.batch_size == 100

    # Minimum
    config = ExportConfig(batch_size=1)
    assert config.batch_size == 1

    # Maximum
    config = ExportConfig(batch_size=500)
    assert config.batch_size == 500


def test_load_config_file_not_found() -> None:
    """Test error handling for missing config file."""
    with pytest.raises(FileNotFoundError):
        load_config("nonexistent.yaml")


def test_load_config_from_yaml() -> None:
    """Test loading config from YAML file."""
    yaml_content = """
token: "test_token"
scope:
  guilds:
    - id: 123456789
      name: "Test Guild"
      channels:
        - id: 111111111
          name: "general"
output:
  directory: "./test_exports"
export:
  incremental: false
"""

    with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_content)
        f.flush()

        try:
            config = load_config(f.name)

            assert config.token == "test_token"
            assert len(config.scope.guilds) == 1
            assert config.scope.guilds[0].id == 123456789
            assert config.output.directory == Path("./test_exports")
            assert config.export.incremental is False
        finally:
            Path(f.name).unlink()
