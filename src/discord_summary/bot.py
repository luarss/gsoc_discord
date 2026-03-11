"""Discord client setup and authentication."""

import asyncio
import logging
from typing import Callable

import discord
from discord import Intents

from discord_summary.config import Config

logger = logging.getLogger(__name__)


class DiscordBot:
    """Discord bot client for message export."""

    def __init__(self, config: Config):
        self.config = config
        self.client: discord.Client | None = None
        self._ready_event = asyncio.Event()
        self._on_ready_callback: Callable[[], asyncio.coroutine] | None = None

    def _create_intents(self) -> Intents:
        """Create Discord intents for the bot."""
        intents = Intents.default()
        intents.message_content = True  # Required to read message content
        intents.guilds = True
        intents.guild_messages = True
        return intents

    async def connect(self) -> None:
        """Connect to Discord with the configured token."""
        token = self.config.get_token()
        intents = self._create_intents()

        self.client = discord.Client(intents=intents)

        @self.client.event
        async def on_ready() -> None:
            logger.info(f"Logged in as {self.client.user}")
            self._ready_event.set()
            if self._on_ready_callback:
                await self._on_ready_callback()

        @self.client.event
        async def on_error(event: str, *args, **kwargs) -> None:
            logger.error(f"Discord error in {event}")

        logger.info("Connecting to Discord...")
        await self.client.start(token)

    async def disconnect(self) -> None:
        """Disconnect from Discord."""
        if self.client:
            await self.client.close()
            logger.info("Disconnected from Discord")

    def on_ready(self, callback: Callable) -> None:
        """Set callback for when bot is ready."""
        self._on_ready_callback = callback

    async def wait_until_ready(self) -> None:
        """Wait until the bot is ready."""
        await self._ready_event.wait()

    def get_guild(self, guild_id: int) -> discord.Guild | None:
        """Get a guild by ID."""
        if self.client:
            return self.client.get_guild(guild_id)
        return None

    async def fetch_channel(self, channel_id: int) -> discord.abc.GuildChannel | None:
        """Fetch a channel by ID."""
        if self.client:
            try:
                channel = self.client.get_channel(channel_id)
                if channel:
                    return channel
                # Try fetching if not in cache
                return await self.client.fetch_channel(channel_id)
            except discord.NotFound:
                logger.warning(f"Channel {channel_id} not found")
                return None
            except discord.Forbidden:
                logger.error(f"No access to channel {channel_id}")
                return None
        return None

    async def fetch_messages(
        self,
        channel: discord.TextChannel,
        after_id: int | None = None,
        limit: int = 100,
    ) -> list[discord.Message]:
        """Fetch messages from a channel.

        Args:
            channel: The channel to fetch from.
            after_id: Only fetch messages after this ID (for incremental).
            limit: Maximum number of messages to fetch.

        Returns:
            List of messages, oldest first.
        """
        messages = []
        try:
            after = None
            if after_id:
                after = discord.Object(id=after_id)

            async for message in channel.history(
                after=after,
                limit=limit,
                oldest_first=True,
            ):
                messages.append(message)

        except discord.Forbidden:
            logger.error(f"No permission to read channel {channel.name}")
        except discord.HTTPException as e:
            logger.error(f"HTTP error fetching from {channel.name}: {e}")

        return messages
