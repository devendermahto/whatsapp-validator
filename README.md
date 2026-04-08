# WhatsApp Validator Bot

A self-hosted WhatsApp number validator using Evolution API. Includes both a Telegram bot and a web interface.

## Features

- **Telegram Bot** - Validate numbers via Telegram commands
- **Web Interface** - Visual UI with real-time progress tracking
- **Batch Processing** - Process numbers in batches of 50
- **Anti-Ban Protection** - Randomized delays (2.5-5.5s) between checks, 3-min cooldown between batches
- **SQLite Database** - Persistent storage for API credentials
- **Self-Hosted** - Runs on your own Evolution API server

## Prerequisites

- Python 3.10+
- [Evolution API](https://github.com/AtarryTech/EvolutionApi) running on Docker/Unraid
- Telegram Bot Token (get from @BotFather)

## Installation

```bash
git clone <your-repo-url>
cd WHATSAPP_CHECKER

# Create virtual environment (optional but recommended)
python -m venv venv
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

1. Copy `.env.example` to `.env` (if exists) or create one:
```env
BOT_TOKEN=your_telegram_bot_token_here
```

2. For web interface, open http://localhost:5000 and enter your Evolution API credentials:
   - **API URL**: `http://your-unraid-ip:8080`
   - **Instance Name**: Your Evolution API instance name
   - **API Key**: Your Evolution API key

## Usage

### Web Interface (Recommended)
```bash
python app.py
```
Then open http://localhost:5000

### Telegram Bot
```bash
python main.py
```

### Telegram Commands

1. Send `/start` to your bot
2. Click **🔗 Connect API**
3. Enter credentials: `URL, InstanceName, APIKey`
   - Example: `http://192.168.1.100:8080, myinstance, abc123xyz`
4. Click **📲 Start Checker**
5. Send phone numbers (any format - text, comma-separated, or one per line)

## Project Structure

```
WHATSAPP_CHECKER/
├── .env                 # BOT_TOKEN configuration
├── app.py              # Flask web server
├── core.py             # Shared validation logic
├── database.py         # SQLite database functions
├── evolution_api.py    # Evolution API wrapper
├── main.py             # Telegram bot
├── requirements.txt    # Python dependencies
├── templates/
│   └── index.html      # Web UI
└── whatsapp_checker.db # SQLite database (auto-created)
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `BOT_TOKEN` | Telegram Bot API Token | For Telegram bot only |

## API Endpoints (Web Interface)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web UI |
| `/api/settings` | GET/POST | Get/Save API credentials |
| `/api/check-connection` | GET | Test API connection |
| `/api/validate` | POST | Start validation |
| `/api/download/<task_id>` | GET | Download results |

## Anti-Ban Measures

- **Random delays**: 2.5-5.5 seconds between each number check
- **Batch cooldown**: 180 seconds (3 minutes) between batches of 50
- **Concurrency limit**: Maximum 2 parallel workers
- **Connection check**: Verifies API is reachable before processing

## License

MIT