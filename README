# RPG Chaos Bot

A Twitch chat bot that implements RPG gameplay elements, inspired by Ada RPG bot but with improved code organization and additional features.

## Features

- **Class System**: Players can choose from different classes including:
  - Druid
  - Cat
  - Bard
  - Barbarian

- **Chat Commands**:
  - `!start` - Begin your adventure by choosing a class
  - `!class <classname>` - Select your character class
  - `!intro` - Display bot information
  - `!remind <time> [message]` - Set a reminder (e.g. "!remind 3m" or "!remind 2h")
  - `!followers` - Display channel follower count
  - `!so <username>` - Shoutout another streamer
  - `!cwa <message>` - Send a channel-wide announcement

## Setup

1. Create a `.env` file with your Twitch credentials:
```env
CLIENT_ID=your_client_id
CLIENT_SECRET=your_client_secret
```

2. Install required Python packages:
```bash
pip install flask python-dotenv requests
```

3. Run the OAuth flow to get initial tokens:
```bash
python twitch_oauth_flow.py
```

## File Structure

- `main.py` - Main bot logic and command handling
- `twitch_oauth_flow.py` - Handles Twitch authentication
- `classes.json` - Defines available character classes
- `players.json` - Stores player data and progress
- `.env` - Environment variables (not tracked in git)
- `tokens.json` - OAuth tokens (not tracked in git)

## Development

The bot is written in Python and uses:
- Socket connections for Twitch IRC chat
- Flask for OAuth token management
- JSON for data storage
- Threading for reminder functionality

## License

This project is open source and available under the MIT License.

## Credits

Created by Starry0Wolf as an improved alternative to the Ada RPG bot.