"""Core export orchestration."""

import logging
from collections import defaultdict
from datetime import date

from discord_summary.bot import DiscordBot
from discord_summary.config import Config
from discord_summary.formatters.markdown import MarkdownFormatter
from discord_summary.storage.file_writer import FileWriter
from discord_summary.utils.rate_limiter import rate_limiter
from discord_summary.utils.state import ExportState

logger = logging.getLogger(__name__)


class Exporter:
    """Orchestrates the export process."""

    def __init__(self, config: Config):
        self.config = config
        self.bot = DiscordBot(config)
        self.formatter = MarkdownFormatter(
            include_attachments=config.export.include_attachments,
            include_reactions=config.export.include_reactions,
        )
        self.writer = FileWriter(config.output)
        self.state = ExportState.load(config.export.state_file)

    async def run(self) -> None:
        """Run the export process."""
        self.writer.ensure_output_directory()

        async def export_on_ready() -> None:
            try:
                await self._export_all()
            finally:
                await self.bot.disconnect()

        self.bot.on_ready(export_on_ready)
        await self.bot.connect()

    async def _export_all(self) -> None:
        """Export all configured guilds and channels."""
        total_messages = 0

        for guild_config in self.config.scope.guilds:
            guild = self.bot.get_guild(guild_config.id)
            if not guild:
                logger.warning(f"Guild {guild_config.id} not found")
                continue

            guild_name = guild_config.name or guild.name
            logger.info(f"Exporting guild: {guild_name}")

            # If no channels specified, export all text channels
            channels_to_export = guild_config.channels
            if not channels_to_export:
                channels_to_export = self._get_all_text_channels(guild)
                logger.info(f"  Auto-discovered {len(channels_to_export)} text channels")

            for channel_config in channels_to_export:
                count = await self._export_channel(
                    guild=guild,
                    guild_name=guild_name,
                    channel_config=channel_config,
                )
                total_messages += count

    def _get_all_text_channels(self, guild) -> list:
        """Get all text channels from a guild as channel configs."""
        from discord_summary.config import ChannelConfig

        channels = []
        for channel in guild.text_channels:
            channels.append(
                ChannelConfig(id=channel.id, name=channel.name)
            )
        return channels

        # Save state after successful export
        if self.config.export.incremental:
            self.state.save(self.config.export.state_file)
            logger.info(f"State saved to {self.config.export.state_file}")

        logger.info(f"Export complete. Total messages: {total_messages}")

    async def _export_channel(
        self,
        guild: object,  # Reserved for future use
        guild_name: str,
        channel_config,
    ) -> int:
        """Export a single channel.

        Returns:
            Number of messages exported.
        """
        channel = await self.bot.fetch_channel(channel_config.id)
        if not channel:
            logger.warning(f"Channel {channel_config.id} not found")
            return 0

        # Verify it's a text channel
        if not hasattr(channel, "history"):
            logger.warning(f"Channel {channel_config.id} is not a text channel")
            return 0

        channel_name = channel_config.name or channel.name
        logger.info(f"  Exporting channel: #{channel_name}")

        # Get last message ID for incremental export
        after_id = None
        if self.config.export.incremental:
            channel_state = self.state.get_channel_state(channel_config.id)
            if channel_state.last_message_id:
                after_id = int(channel_state.last_message_id)
                logger.debug(f"  Resuming after message ID: {after_id}")

        # Fetch messages
        messages = []
        async with rate_limiter.retry_on_rate_limit():
            messages = await self.bot.fetch_messages(
                channel=channel,
                after_id=after_id,
                limit=self.config.export.batch_size,
            )

        if not messages:
            logger.info(f"  No new messages in #{channel_name}")
            return 0

        logger.info(f"  Fetched {len(messages)} messages")

        # Group messages by date
        messages_by_date: dict[date, list] = defaultdict(list)
        for msg in messages:
            msg_date = msg.created_at.date()
            messages_by_date[msg_date].append(msg)

        # Format and write each date group
        for msg_date, date_messages in messages_by_date.items():
            content_parts = []
            for msg in date_messages:
                formatted = self.formatter.format_message(msg)
                content_parts.append(formatted.content)

            self.writer.write(
                guild_name=guild_name,
                channel_name=channel_name,
                channel_id=channel_config.id,
                message_date=msg_date,
                content="\n".join(content_parts),
            )

        # Update state with last message ID
        if messages and self.config.export.incremental:
            last_message = messages[-1]
            self.state.update_channel(
                channel_id=channel_config.id,
                last_message_id=str(last_message.id),
                count=len(messages),
            )

        return len(messages)
