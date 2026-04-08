# Evolution API Setup Guide

## Option 1: Portainer (Recommended)

### Step 1: Open Portainer
- Go to `http://<your-unraid-ip>:9443`
- Login with your credentials

### Step 2: Create Stack
1. Click **Stacks** (left sidebar)
2. Click **Add stack**
3. Name: `evolution-api`

### Step 3: Paste Configuration
In the editor, paste:
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
      - AUTHENTICATION_API_KEY=mypass123
    volumes:
      - evolution_instances:/evolution/instances
    restart: unless-stopped

volumes:
  evolution_instances:
    driver: local
```

### Step 4: Deploy
1. Click **Deploy the stack**
2. Wait 1-2 minutes for container to start
3. Check container in **Containers** tab

### Step 5: Verify
- Open `http://<your-unraid-ip>:8081` in browser
- You should see Evolution API response

---

## Option 2: Unraid Docker Template

### Step 1: Open Docker Tab
- Go to Unraid UI → **Docker** tab
- Click **Add Container**

### Step 2: Configure Container

| Setting | Value |
|---------|-------|
| **Name** | `evolution-api` |
| **Repository** | `atarrytech/evolution-api:latest` |
| **Network Type** | `Bridge` |

### Step 3: Port Settings
Click **Add**:
- Host Port: `8081`
- Container Port: `8080`
- Protocol: `TCP`

### Step 4: Environment Variables
Click **Add** three times:

| Variable | Value |
|----------|-------|
| `SERVER_TYPE` | `http` |
| `SERVER_PORT` | `8080` |
| `AUTHENTICATION_API_KEY` | `mypass123` |

### Step 5: Volume Settings
Click **Add**:
- Host Path: `/mnt/user/appdata/evolution-api`
- Container Path: `/evolution/instances`

### Step 6: Start Container
- Click **Apply**
- Wait for container to start
- Check logs if needed

---

## Step 6: Create Instance (After Setup)

After container is running:
1. Open `http://<unraid-ip>:8081` in browser
2. Use POST request to create instance:
   ```
   POST http://<unraid-ip>:8081/instance/create
   Body: {"instanceName": "mywhatsapp"}
   ```
3. Scan QR code with WhatsApp

---

## Common Issues

| Problem | Solution |
|---------|----------|
| Port already in use | Change `8081` to another port (8082, 8083, etc.) |
| Container won't start | Check logs in Portainer/Unraid |
| Can't access from PC | Ensure firewall allows the port |
| Instance not working | Make sure you scanned QR code |