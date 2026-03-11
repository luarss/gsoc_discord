# Discord Chat History Exporter

Export Discord chat history to organized markdown files with daily snapshots.

## Features

- **Daily Snapshots**: Messages grouped by date in separate markdown files
- **Incremental Exports**: Only fetch new messages since last run
- **Configurable Scope**: Export specific servers and channels
- **Rich Formatting**: Includes attachments, reactions, and reply references
- **Rate Limit Handling**: Built-in retry logic for Discord API limits

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd discord_summary

# Create virtual environment and install
python -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows
pip install -e .
```

## Discord Bot Setup

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Navigate to "Bot" and create a bot
4. Enable **Message Content Intent** under Privileged Gateway Intents
5. Copy the bot token
6. Invite the bot to your server with `Read Messages` and `Read Message History` permissions

## Configuration

1. Copy the example config:
   ```bash
   cp config.example.yaml config.yaml
   ```

2. Edit `config.yaml`:
   ```yaml
   # Option 1: Set token in config
   token: "YOUR_BOT_TOKEN"

   # Option 2: Use environment variable
   # DISCORD_TOKEN=your_token_here

   scope:
     guilds:
       - id: 123456789012345678  # Your server ID
         name: "My Server"
         channels:
           - id: 111111111111111111
             name: "general"

   output:
     directory: "./exports"
     timezone: "UTC"

   export:
     incremental: true
     state_file: "./export_state.json"
   ```

### Finding IDs

Enable Developer Mode in Discord (Settings > Advanced > Developer Mode), then right-click on servers/channels and select "Copy ID".

## Usage

```bash
# Run with default config (config.yaml)
discord-summary

# Run with custom config
discord-summary --config my_config.yaml

# Run with verbose logging
discord-summary --verbose
```

## Output Structure

```
exports/
├── MyServer/
│   ├── general/
│   │   ├── 2024-03-10.md
│   │   └── 2024-03-11.md
│   └── announcements/
│       └── 2024-03-10.md
```

### Markdown Format

```markdown
# #general - 2024-03-10

> Channel: #general (ID: 111111111111111111)
> Exported: 2024-03-10T15:30:00Z

---

### 09:15 - @Username

Message content here...

📎 **Attachments:**
- [image.png](https://cdn.discordapp.com/...)

👍 **Reactions:**
- 👍 (3)

---
```

## Incremental Exports

On first run, all messages are exported. Subsequent runs only fetch new messages:

```bash
# First run: exports all available messages
discord-summary

# Later runs: only exports new messages
discord-summary
```

The state is tracked in `export_state.json`:

```json
{
  "channels": {
    "111111111111111111": {
      "last_message_id": "1234567890123456789",
      "total_exported": 1523
    }
  }
}
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check src/
```

## License

MIT
