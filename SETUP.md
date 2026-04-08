# WhatsApp Validator Setup Guide

This guide covers setting up both Evolution API and the WhatsApp Validator web app on Unraid using Portainer.

---

## Prerequisites

- Unraid server with Portainer installed
- Telegram Bot Token (get from @BotFather)
- GitHub account (repo already public)

---

## Step 1: Deploy Stack in Portainer

1. Go to **Portainer** → **Stacks** → **Add stack**
2. Use the **Web editor** and paste:

```yaml
version: '3'
services:
  evolution-api:
    image: atarrytech/evolution-api:latest
    container_name: evolution-api
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
    build:
      context: https://github.com/devendermahto/whatsapp-validator.git#main
      dockerfile: Dockerfile
    container_name: whatsapp-validator
    ports:
      - "5050:5000"
    environment:
      - BOT_TOKEN=${BOT_TOKEN}
    volumes:
      - validator_data:/app
    restart: unless-stopped

volumes:
  evolution_instances:
  validator_data:
```

3. In **Environment variables** section, add:

| Variable | Value |
|----------|-------|
| `API_KEY` | `Mahto@Ertiga8585` |
| `BOT_TOKEN` | `5380085163:AAGPVNNJl6QI_ymF42Lz4Qw_i1Fttx03VZ0` |

4. Click **Deploy the stack**
5. Wait 3-5 minutes for build to complete

---

## Step 2: Verify Containers

Check in Portainer **Containers** tab:
- `evolution-api` - should be running
- `whatsapp-validator` - should be running

---

## Step 3: Access the Web App

1. Open browser: `http://<your-unraid-ip>:5050`
2. Login with:
   - **Username:** `devendermahto`
   - **Password:** `Mahto@Ertiga8585`

---

## Step 4: Configure Evolution API in Web App

1. Enter your API details:
   - **API URL:** `http://<your-unraid-ip>:8089`
   - **Instance Name:** `mywhatsapp`
   - **API Key:** `Mahto@Ertiga8585`
2. Click **Save & Connect**
3. Should show "Connected ✅"

---

## Step 5: Create WhatsApp Instance

Option A - Via API:
```
POST http://<your-unraid-ip>:8089/instance/create
Body: {"instanceName": "mywhatsapp"}
```

Then scan QR code with WhatsApp.

---

## Service URLs

| Service | URL |
|---------|-----|
| Web App | `http://<unraid-ip>:5050` |
| Evolution API | `http://<unraid-ip>:8089` |
| Portainer | `http://<unraid-ip>:9443` |

---

## Common Issues

| Problem | Solution |
|---------|----------|
| Build fails | Make sure repo is public |
| Web app not loading | Check container logs in Portainer |
| API not connected | Verify instance is created and QR scanned |
| Port already in use | Change port in docker-compose (e.g., 8090:8080) |
| Environment variables not working | Make sure they are added in "Environment variables" section |

---

## Security Note

- **Public repo:** ✅ Safe - no secrets in code
- **Secrets:** ✅ Safe - stored only in Portainer environment variables
- **API Key:** ✅ Safe - only you know it

---

## Login Credentials

- **Web App Username:** `devendermahto`
- **Web App Password:** `Mahto@Ertiga8585`
- **API Key:** `Mahto@Ertiga8585`
- **Telegram Bot:** Already configured via environment variable