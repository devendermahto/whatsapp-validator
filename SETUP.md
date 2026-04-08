# WhatsApp Validator Setup Guide

This guide covers setting up both Evolution API and the WhatsApp Validator web app on Unraid using Portainer.

---

## Prerequisites

- Unraid server with Portainer installed
- Telegram Bot Token (get from @BotFather)

---

## Step 1: Deploy Everything (Single Stack)

In Portainer:
1. Go to **Stacks** → **Add stack**
2. Name: `whatsapp-validator`
3. Paste this configuration:

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
    environment:
      - BOT_TOKEN=5380085163:AAGPVNNJl6QI_ymF42Lz4Qw_i1Fttx03VZ0

volumes:
  evolution_instances:
  validator_data:
```

4. Click **Deploy the stack**
5. Wait 3-5 minutes for both containers to build and start

---

## Step 2: Verify Containers

Check in Portainer **Containers** tab:
- `evolution-api` - should be running
- `whatsapp-validator` - should be running

---

## Step 3: Access the Web App

1. Open browser: `http://<your-unraid-ip>:5000`
2. Login with:
   - **Username:** `devendermahto`
   - **Password:** `Mahto@Ertiga8585`

---

## Step 4: Configure Evolution API

In the web app:
1. Enter your API details:
   - **API URL:** `http://<your-unraid-ip>:8089`
   - **Instance Name:** `mywhatsapp` (or whatever you create)
   - **API Key:** `Mahto@Ertiga8585`
2. Click **Save & Connect**
3. Should show "Connected ✅"

---

## Step 5: Create WhatsApp Instance

Option A - Via Evolution API Dashboard:
1. Open `http://<your-unraid-ip>:8089` in browser
2. Create instance with name `mywhatsapp`
3. Scan QR code with WhatsApp

Option B - Via API:
```
POST http://<your-unraid-ip>:8089/instance/create
Body: {"instanceName": "mywhatsapp"}
```

---

## Step 6: Start Validating Numbers

1. Go to web app: `http://<your-unraid-ip>:5000`
2. Login with your credentials
3. Enter phone numbers in the text area
4. Click **Start Validation**
5. Watch real-time progress
6. Download results when complete

---

## Service URLs

| Service | URL |
|---------|-----|
| Web App | `http://<unraid-ip>:5000` |
| Evolution API | `http://<unraid-ip>:8089` |
| Portainer | `http://<unraid-ip>:9443` |

---

## Common Issues

| Problem | Solution |
|---------|----------|
| Web app not loading | Check container logs in Portainer |
| API not connected | Verify instance is created and QR scanned |
| Port already in use | Change port in docker-compose (e.g., 8082:8080) |
| Build fails | Check GitHub repo is public or build context is correct |

---

## Login Credentials

- **Web App Username:** `devendermahto`
- **Web App Password:** `Mahto@Ertiga8585`
- **Telegram Bot:** Already configured in environment