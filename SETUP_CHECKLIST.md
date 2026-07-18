# Sidecar Setup Checklist

Track your progress deploying Sidecar locally and to your VM.

## ✅ Phase 1: Local Development (Complete)
- [x] Repository created: https://github.com/lazo99/sidecar
- [x] Source code scaffolded (auth, keys, proxy, audit, server)
- [x] Dependencies configured (requirements.txt)
- [x] Tests written and passing
- [x] GitHub Actions workflows configured
- [x] Documentation complete (README, DEPLOYMENT, SECRETS_SETUP)

## ⏳ Phase 2: Bitwarden Setup (Your Action)

- [ ] Create Bitwarden account or log in to existing
- [ ] Navigate to Secrets Manager
- [ ] Create a project (e.g., "Sidecar")
- [ ] Create a Service Account
- [ ] Generate and save Access Token (keep safe!)
- [ ] Create secrets in Bitwarden Secrets Manager:
  - [ ] `jwt-secret` → a random 32+ char secret (generate: `python -c "import secrets; print(secrets.token_hex(32))"`)
  - [ ] `claude` → your Anthropic API key
  - [ ] `openai` → your OpenAI API key (if needed)
  - [ ] `gcp` → your GCP service account JSON (if needed)

**Reference:** See [SECRETS_SETUP.md](./SECRETS_SETUP.md)

## ⏳ Phase 3: VM Deployment (Your Action)

On your `miss-minutes` VM (via `gcloud compute ssh miss-minutes --zone us-west1-b`):

1. [ ] Run deployment script with Bitwarden token:
   ```bash
   BITWARDEN_SM_TOKEN=<your-token> bash <(curl -s https://raw.githubusercontent.com/lazo99/sidecar/master/deploy-vm.sh)
   ```
   Or:
   ```bash
   git clone https://github.com/lazo99/sidecar.git /tmp/sidecar-setup
   cd /tmp/sidecar-setup
   BITWARDEN_SM_TOKEN=<your-token> bash deploy-vm.sh
   ```

2. [ ] Script will:
   - Install `bws` CLI
   - Clone sidecar repo to `/opt/sidecar`
   - Create `.env` with your `BITWARDEN_SM_TOKEN`
   - Create systemd service

3. [ ] Verify service is running:
   ```bash
   sudo systemctl status sidecar
   curl http://localhost:8000/health
   ```

4. [ ] Check logs (watch for JWT secret fetched from Bitwarden):
   ```bash
   sudo journalctl -u sidecar -f
   # Should show: "✓ JWT secret loaded from Bitwarden"
   ```

## ⏳ Phase 4: Local Integration (Your Action)

### Generate a JWT token for your laptop

On your laptop, in the sidecar repo:

```bash
source venv/bin/activate
python << 'EOF'
from src.auth import AuthManager
import os

# Use the same secret as on the VM
secret = os.getenv("JWT_SECRET_KEY")  # or paste it here
auth = AuthManager(secret_key=secret)
token = auth.create_token("laptop-agent")
print(f"Token: {token}")
print("\nUse this in your MCP client:")
print(f'curl -H "Authorization: Bearer {token}" http://VM_IP:8000/apis')
EOF
```

### Configure your MCP client

In your MCP config, add sidecar as a resource:

```json
{
  "resources": [
    {
      "name": "sidecar",
      "url": "http://<VM_IP>:8000",
      "auth": {
        "type": "bearer",
        "token": "<JWT-token-from-above>"
      }
    }
  ]
}
```

Then call APIs via sidecar:

```bash
curl -X POST http://VM_IP:8000/api/claude/proxy \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "method": "POST",
    "path": "/v1/messages",
    "body": {"model": "claude-3-sonnet-20240229", ...}
  }'
```

## ⏳ Phase 5: Testing & Iteration (Your Action)

- [ ] Test `/health` endpoint
- [ ] Test `/apis` listing
- [ ] Test key rotation (add/remove via Bitwarden)
- [ ] Check audit logs: `/audit`
- [ ] Load test with multiple concurrent requests
- [ ] Verify logs don't leak API keys

## 📚 Reference Links

- Repo: https://github.com/lazo99/sidecar
- Secrets Setup: [SECRETS_SETUP.md](./SECRETS_SETUP.md)
- Deployment: [DEPLOYMENT.md](./DEPLOYMENT.md)
- Contributing: [CONTRIBUTING.md](./CONTRIBUTING.md)
- Roadmap: [ROADMAP.md](./ROADMAP.md)
