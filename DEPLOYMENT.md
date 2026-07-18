# Deployment Guide

## Cloud Run (Recommended)

```bash
gcloud run deploy sidecar \
  --source . \
  --platform managed \
  --region us-central1 \
  --no-allow-unauthenticated \
  --memory 512Mi \
  --timeout 300 \
  --set-env-vars \
    JWT_SECRET_KEY=$(cat ~/.secrets/jwt-secret.txt),\
    BITWARDEN_SM_TOKEN=$(cat ~/.secrets/bitwarden-token.txt)
```

Cloud Run automatically handles scaling, SSL, and container management.

## VM Deployment (systemd)

### Prerequisites

- Linux VM (Ubuntu 20.04+ or similar)
- Python 3.10+
- git

### Install

```bash
# SSH to VM
gcloud compute ssh <instance-name> --zone <zone>

# Clone repo
cd /opt
sudo git clone https://github.com/hats-off-it/sidecar.git
sudo chown -R ubuntu:ubuntu sidecar
cd sidecar

# Create venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Setup secrets
mkdir -p ~/.secrets
chmod 700 ~/.secrets
echo "sk-..." > ~/.secrets/claude.key
# ... add other keys ...

# Create .env
cat > .env << EOF
JWT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
BITWARDEN_SM_TOKEN=<your-token>
PORT=8000
EOF
chmod 600 .env
```

### Create systemd Service

Create `/etc/systemd/system/sidecar.service`:

```ini
[Unit]
Description=Sidecar API Key Vault
After=network.target

[Service]
Type=notify
User=ubuntu
WorkingDirectory=/opt/sidecar
Environment="PATH=/opt/sidecar/venv/bin"
EnvironmentFile=/opt/sidecar/.env
ExecStart=/opt/sidecar/venv/bin/python -m src.server
Restart=on-failure
RestartSec=10

# Security
NoNewPrivileges=true
PrivateTmp=true
ReadWritePaths=/opt/sidecar/logs

[Install]
WantedBy=multi-user.target
```

### Enable & Start

```bash
sudo systemctl daemon-reload
sudo systemctl enable sidecar
sudo systemctl start sidecar

# Check status
sudo systemctl status sidecar
sudo journalctl -u sidecar -f  # tail logs
```

### Health Check

```bash
curl http://localhost:8000/health
```

## Docker Compose (Local)

Create `docker-compose.yml`:

```yaml
version: "3.8"

services:
  sidecar:
    build: .
    ports:
      - "8000:8000"
    environment:
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
      BITWARDEN_SM_TOKEN: ${BITWARDEN_SM_TOKEN}
      PORT: 8000
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
```

Run:
```bash
docker-compose up
```

## Monitoring

### Logs

**Cloud Run:**
```bash
gcloud run logs read sidecar --limit 50 --format json
```

**VM:**
```bash
sudo journalctl -u sidecar -f
tail -f /opt/sidecar/logs/audit.jsonl
```

### Metrics

**Cloud Run:** Cloud Console → Cloud Run → sidecar → Metrics

**VM:** Set up monitoring agent (Google Cloud Monitoring recommended)

## Security Checklist

- [ ] JWT secret is strong (min 32 chars, random)
- [ ] Bitwarden token stored securely (not in git, encrypted)
- [ ] Firewall rules restrict access (no public access)
- [ ] HTTPS enabled (Cloud Run: automatic; VM: use reverse proxy like nginx)
- [ ] Audit logs backed up or streamed to Cloud Logging
- [ ] Service account has minimal IAM permissions
- [ ] No API keys in logs or error messages

## Scaling

**Cloud Run:** Auto-scales by default based on traffic

**VM:** 
- Multiple instances behind a load balancer
- Shared Bitwarden token across instances
- Audit logs centralized (e.g., Cloud Logging, ELK)

## Troubleshooting

### "Connection refused"
Check service is running: `systemctl status sidecar`

### "Bitwarden token invalid"
Regenerate in Bitwarden web UI, update .env

### "High CPU/Memory"
- Check audit log file size (rotate if needed)
- Monitor slow API requests (proxy.py timeout)

### "Secrets not accessible"
Verify Bitwarden service account permissions
