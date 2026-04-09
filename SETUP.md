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

3. In **Environment variables** section, add your own values:

| Variable | Your Value |
|----------|------------|
| `API_KEY` | Any value (required but not used for auth) |
| `BOT_TOKEN` | Your Telegram Bot Token (from @BotFather) |

4. Click **Deploy the stack**
5. Wait 2-3 minutes for containers to start

---

## Step 2: Verify Containers

Check in Portainer **Containers** tab:
- `evolution-api` - should be running on port 8089
- `whatsapp-validator` - should be running on port 5050

---

## Step 3: Create WhatsApp Instance

After deploying the stack, you need to create an instance in Evolution API:

1. Go to: `http://<your-unraid-ip>:8089/manager`
2. Login with your Evolution API credentials (set up when you first accessed the manager)
3. Click **Create Instance**
4. Enter instance name: `whatsappvalidator`
5. **Choose Integration Type:**

### Which Integration to Choose?

| Integration | Pros | Cons |
|-------------|------|------|
| **Baileys** | Free, no Meta costs, works with your existing WhatsApp | Requires phone to stay connected |
| **Cloud API** | No phone needed, more reliable uptime | Requires Meta Business verification, has costs |

**Recommendation:** Start with **Baileys** - it's simpler and free.

6. After creating the instance, you'll see a QR code
7. Open WhatsApp on your phone → Go to **Linked Devices**
8. Scan the QR code to connect
9. Copy the **API Key** generated for that instance (you'll need this for the web app)

---

## Step 4: Access the Web App

1. Open browser: `http://<your-unraid-ip>:5050/login`
2. Enter any username and password to create your login
3. You'll be redirected to the dashboard

---

## Step 5: Configure Evolution API in Web App

1. In the web app, go to **Settings**
2. Enter your API details:
   - **API URL:** `http://<your-unraid-ip>:8089`
   - **Instance:** `whatsappvalidator`
   - **API Key:** (the key from Step 3)
3. Click **Save**

---

## Service URLs

| Service | URL |
|---------|-----|
| Web App | `http://<unraid-ip>:5050` |
| Evolution API | `http://<unraid-ip>:8089` |
| Evolution Manager | `http://<unraid-ip>:8089/manager` |

---

## Common Issues

| Problem | Solution |
|---------|----------|
| "Could not connect to API" | Verify instance is created in Evolution API manager |
| Instance shows offline | Scan QR code in Evolution API to connect WhatsApp |
| Web app error | Check container logs in Portainer |
| Port already in use | Change port in docker-compose (e.g., 8090:8080) |
| Environment variables not working | Make sure they are added in "Environment variables" section |

---

## Security Note

- **Public repo:** Safe - no secrets in code
- **Secrets:** Stored only in Portainer environment variables
- **Login:** Create your own username/password on first login

---

## First Login

On first login, you'll create your own credentials. No default username/password - just enter what you'd like to use.
