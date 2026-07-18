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
- [ ] Create secrets for each API:
  - [ ] `claude` → your Anthropic API key
  - [ ] `openai` → your OpenAI API key (if needed)
  - [ ] `gcp` → your GCP service account JSON (if needed)

**Reference:** See [SECRETS_SETUP.md](./SECRETS_SETUP.md)

## ⏳ Phase 3: VM Deployment (Your Action)

On your `miss-minutes` VM (via `gcloud compute ssh miss-minutes --zone us-west1-b`):

1. [ ] Generate JWT secret:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

2. [ ] Run deployment script:
   ```bash
   bash <(curl -s https://raw.githubusercontent.com/lazo99/sidecar/master/deploy-vm.sh)
   ```
   Or:
   ```bash
   git clone https://github.com/lazo99/sidecar.git /tmp/sidecar-setup
   cd /tmp/sidecar-setup
   bash deploy-vm.sh
   ```

3. [ ] When prompted, edit `.env` at `/opt/sidecar/.env`:
   ```env
   JWT_SECRET_KEY=<generated-secret-from-step-1>
   BITWARDEN_SM_TOKEN=<token-from-phase-2>
   BITWARDEN_API_URL=https://api.bitwarden.us
   PORT=8000
   ```

4. [ ] Verify service is running:
   ```bash
   sudo systemctl status sidecar
   curl http://localhost:8000/health
   ```

5. [ ] View logs:
   ```bash
   sudo journalctl -u sidecar -f
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
