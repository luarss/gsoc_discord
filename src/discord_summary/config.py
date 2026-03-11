"""Configuration loading and validation using Pydantic."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ChannelConfig(BaseModel):
    """Configuration for a single Discord channel."""

    id: int
    name: str | None = None


class GuildConfig(BaseModel):
    """Configuration for a Discord guild (server)."""

    id: int
    name: str | None = None
    channels: list[ChannelConfig] | None = None  # None = auto-discover all


class ScopeConfig(BaseModel):
    """Scope configuration defining what to export."""

    guilds: list[GuildConfig] = Field(default_factory=list)


class OutputConfig(BaseModel):
    """Output configuration."""

    directory: Path = Path("./exports")
    timezone: str = "UTC"


class ExportConfig(BaseModel):
    """Export behavior configuration."""

    incremental: bool = True
    state_file: Path = Path("./export_state.json")
    include_attachments: bool = True
    include_reactions: bool = True
    include_threads: bool = True
    batch_size: int = Field(default=100, ge=1, le=500)


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    discord_token: str = Field(default="", alias="DISCORD_TOKEN")


class Config(BaseModel):
    """Main configuration model."""

    token: str | None = None  # Can be set via DISCORD_TOKEN env var
    scope: ScopeConfig = Field(default_factory=ScopeConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    export: ExportConfig = Field(default_factory=ExportConfig)

    @field_validator("token", mode="before")
    @classmethod
    def validate_token(cls, v: Any) -> str | None:
        if v is None or v == "":
            return None
        return str(v)

    def get_token(self) -> str:
        """Get the Discord token from config or environment."""
        if self.token:
            return self.token
        settings = Settings()
        token = settings.discord_token
        if not token:
            raise ValueError(
                "Discord token not found. Set it in config.yaml or DISCORD_TOKEN env var"
            )
        return token


def load_config(config_path: Path | str) -> Config:
    """Load configuration from a YAML file.

    Args:
        config_path: Path to the YAML configuration file.

    Returns:
        Validated Config object.

    Raises:
        FileNotFoundError: If the config file doesn't exist.
        ValueError: If the config is invalid.
    """
    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if data is None:
        data = {}

    return Config.model_validate(data)
