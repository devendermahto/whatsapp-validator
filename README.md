# WhatsApp Validator

A self-hosted WhatsApp number validator using Evolution API. Features both Telegram bot and web interface with authentication, job history, and real-time progress.

## Features

- **Web Interface** - Visual UI with real-time progress tracking
- **Job History** - View all previous validation jobs with detailed results
- **Background Processing** - Jobs run in background, no page refresh needed
- **Authentication** - Secure login (customizable)
- **Telegram Bot** - Validate numbers via Telegram commands
- **Batch Processing** - Process numbers in batches of 50
- **Anti-Ban Protection** - Randomized delays (2.5-5.5s) between checks, 3-min cooldown
- **SQLite Database** - Persistent storage for credentials and job history
- **Self-Hosted** - Runs on your own Evolution API server
- **Environment Variables** - Secrets stored safely in Portainer, not in code

## Quick Start (Unraid + Portainer)

### Prerequisites

1. Make GitHub repo public:
   - Go to: https://github.com/devendermahto/whatsapp-validator/settings
   - **Danger zone** → **Change visibility** → **Make public**

### Deploy Stack

1. Go to **Portainer** → **Stacks** → **Add stack**
2. Use the **Web editor** and paste:

```yaml
version: '3'
services:
  evolution-api:
    image: atendai/evolution-api:v1.8.7
    ports:
      - "8089:8080"
    environment:
      - SERVER_TYPE=http
      - SERVER_PORT=8080
      - AUTHENTICATION_API_KEY=${API_KEY}
    volumes:
      - evolution_instances:/evolution/instances
    restart: unless-stopped

  whatsapp-validator:
    image: python:3.11-slim
    command:
      - /bin/sh
      - -c
      - |
        pip install flask flask-socketio pyTelegramBotAPI python-dotenv requests
        cd /tmp
        python -c "import urllib.request,os; [urllib.request.urlretrieve(chr(104)+chr(116)+chr(116)+chr(112)+chr(115)+chr(58)+chr(47)+chr(47)+chr(114)+chr(97)+chr(119)+chr(46)+chr(103)+chr(105)+chr(116)+chr(104)+chr(117)+chr(98)+chr(46)+chr(99)+chr(111)+chr(109)+chr(47)+chr(100)+chr(101)+chr(118)+chr(101)+chr(110)+chr(100)+chr(101)+chr(114)+chr(109)+chr(97)+chr(104)+chr(116)+chr(111)+chr(47)+chr(119)+chr(104)+chr(97)+chr(116)+chr(115)+chr(97)+chr(112)+chr(112)+chr(45)+chr(118)+chr(97)+chr(108)+chr(105)+chr(100)+chr(97)+chr(116)+chr(111)+chr(114)+chr(47)+chr(109)+chr(97)+chr(105)+chr(110)+chr(47)+f,f) for f in ['app.py','core.py','database.py','evolution_api.py']]; [os.makedirs('templates',exist_ok=True) or urllib.request.urlretrieve('https://raw.githubusercontent.com/devendermahto/whatsapp-validator/main/templates/'+f,'templates/'+f) for f in ['index.html','login.html']]"
        python app.py
    ports:
      - "5050:5000"
    environment:
      - BOT_TOKEN=${BOT_TOKEN}
    volumes:
      - validator_data:/app
    working_dir: /app
    restart: unless-stopped

volumes:
  evolution_instances:
  validator_data:
```

3. In **Environment variables** section, add:

| Variable | Value |
|----------|-------|
| `API_KEY` | Any value (required but not used) |
| `BOT_TOKEN` | Your Telegram Bot Token |

4. Click **Deploy the stack**
5. Wait 2-3 minutes for containers to start

### Access

| Service | URL |
|---------|-----|
| Web App | `http://<unraid-ip>:5050` |
| Evolution API | `http://<unraid-ip>:8089` |
| Evolution Manager | `http://<unraid-ip>:8089/manager` |

---

## Setup Instructions

### Step 1: Create WhatsApp Instance

After deploying, you need to create an instance in Evolution API:

1. Go to: `http://<your-unraid-ip>:8089/manager`
2. Login with your Evolution API credentials
3. Click **Create Instance**
4. Enter instance name: `whatsappvalidator`
5. **Choose Integration Type:**

| Integration | Pros | Cons |
|------------|------|------|
| **Baileys** | Free, no Meta costs, works with your existing WhatsApp | Requires phone to stay connected |
| **Cloud API** | No phone needed, more reliable uptime | Requires Meta Business verification, has costs |

**Recommendation:** Start with **Baileys** - it's simpler and free.

6. After creating the instance, you'll see a QR code
7. Open WhatsApp on your phone → Go to **Linked Devices**
8. Scan the QR code to connect
9. Copy the **API Key** generated for that instance

### Step 2: Configure Web App

1. Open browser: `http://<your-unraid-ip>:5050/login`
2. Enter any username and password to create your login
3. Go to **Settings**
4. Enter:
   - **API URL:** `http://<your-unraid-ip>:8089`
   - **Instance:** `whatsappvalidator`
   - **API Key:** (the key from Step 1)
5. Click **Save**

---

## Environment Variables

All sensitive data is stored in Portainer, not in the GitHub repo:

| Variable | Description |
|----------|-------------|
| `API_KEY` | Any value (required but not used for auth) |
| `BOT_TOKEN` | Your Telegram Bot API Token |

---

## Security

- **Public repo:** Safe - no secrets in code
- **Secrets:** Stored only in Portainer environment variables

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web UI (requires login) |
| `/login` | GET/POST | Authentication |
| `/api/settings` | GET/POST | API credentials & job list |
| `/api/jobs` | GET | All jobs |
| `/api/job/<id>` | GET | Get specific job |
| `/api/validate` | POST | Start validation |
| `/api/download/<id>` | GET | Download results |

---

## Anti-Ban Measures

- Random delays: 2.5-5.5 seconds between each number check
- Batch cooldown: 180 seconds between batches of 50
- Max 2 parallel workers

---

## Project Structure

```
whatsapp-validator/
├── app.py              # Flask web server
├── core.py             # Core logic + database
├── main.py             # Telegram bot
├── database.py         # SQLite functions
├── evolution_api.py   # Evolution API wrapper
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── templates/
    ├── index.html      # Main UI
    └── login.html      # Login page
```

---

## License

MIT
