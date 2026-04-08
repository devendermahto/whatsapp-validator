# WhatsApp Validator

A self-hosted WhatsApp number validator using Evolution API. Features both Telegram bot and web interface with authentication, job history, and real-time progress.

## Features

- **Web Interface** - Visual UI with real-time progress tracking
- **Job History** - View all previous validation jobs with detailed results
- **Background Processing** - Jobs run in background, no page refresh needed
- **Authentication** - Secure login (username: `devendermahto`, password: `Mahto@Ertiga8585`)
- **Telegram Bot** - Validate numbers via Telegram commands
- **Batch Processing** - Process numbers in batches of 50
- **Anti-Ban Protection** - Randomized delays (2.5-5.5s) between checks, 3-min cooldown
- **SQLite Database** - Persistent storage for credentials and job history
- **Self-Hosted** - Runs on your own Evolution API server

## Quick Start (Unraid + Portainer)

### Deploy Everything

1. Go to **Portainer** → **Stacks** → **Add stack**
2. Name: `whatsapp-validator`
3. Paste this:

```yaml
version: '3'
services:
  evolution-api:
    image: atarrytech/evolution-api:latest
    container_name: evolution-api
    ports:
      - "8081:8080"
    environment:
      - SERVER_TYPE=http
      - SERVER_PORT=8080
      - AUTHENTICATION_API_KEY=Mahto@Ertiga8585
    volumes:
      - evolution_instances:/evolution/instances
    restart: unless-stopped

  whatsapp-validator:
    build:
      context: https://github.com/devendermahto/whatsapp-validator.git
      dockerfile: Dockerfile
    container_name: whatsapp-validator
    ports:
      - "5000:5000"
    volumes:
      - validator_data:/app
    restart: unless-stopped

volumes:
  evolution_instances:
  validator_data:
```

4. Click **Deploy the stack** (wait 3-5 minutes)

### Access

| Service | URL |
|---------|-----|
| Web App | `http://<unraid-ip>:5000` |
| Evolution API | `http://<unraid-ip>:8081` |

### Login

- **Username:** `devendermahto`
- **Password:** `Mahto@Ertiga8585`

### Configure

In the web app:
1. **API URL:** `http://<unraid-ip>:8081`
2. **Instance Name:** `mywhatsapp`
3. **API Key:** `Mahto@Ertiga8585`
4. Click **Save & Connect**

### Create WhatsApp Instance

```
POST http://<unraid-ip>:8081/instance/create
Body: {"instanceName": "mywhatsapp"}
```

Then scan QR code with WhatsApp.

---

## Local Development

```bash
git clone https://github.com/devendermahto/whatsapp-validator.git
cd whatsapp-validator

pip install -r requirements.txt
python app.py
```

Open http://localhost:5000 and login with:
- Username: `devendermahto`
- Password: `Mahto@Ertiga8585`

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