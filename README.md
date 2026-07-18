# Sidecar: Secure API Key Vault & Proxy

A master API key holder and intelligent gateway. Keep all your API keys in one encrypted vault, expose a single authenticated endpoint, and let sidecar route requests to the real APIs.

## Problem

- **Key sprawl**: API keys scattered across apps, configs, environment variables
- **Rotation pain**: Updating a key means rebuilding/redeploying everything
- **No audit trail**: Who accessed what key, when?

## Solution

Sidecar centralizes API key management:

1. **You** hold all keys in Bitwarden Secrets Manager (encrypted)
2. **Agents/apps** call sidecar via authenticated HTTP or MCP
3. **Sidecar** validates JWT, retrieves the key from Bitwarden, proxies to the real API
4. **Audit log** tracks every access

Rotate a key once → all apps instantly use the new one.

## Quick Start

### Prerequisites

- Python 3.10+
- Bitwarden Secrets Manager account & access token
- JWT secret key (min 32 chars)

### Local Development

```bash
git clone https://github.com/hats-off-it/sidecar.git
cd sidecar
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your Bitwarden token and JWT secret

# Run the server
python -m src.server
```

Server runs on `http://localhost:8000`.

### Generate a JWT Token

```python
from src.auth import AuthManager

auth = AuthManager()
token = auth.create_token("my-agent")
print(token)
```

### Make an API Request

```bash
curl -X POST http://localhost:8000/api/claude/proxy \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "method": "POST",
    "path": "/v1/messages",
    "body": {"model": "claude-3-sonnet-20240229", "messages": [...]}
  }'
```

## API Endpoints

### Health Check
```
GET /health
```

### List APIs
```
GET /apis
Authorization: Bearer <token>
```

### Proxy Request
```
POST /api/{api_name}/proxy
Authorization: Bearer <token>

Body:
{
  "method": "POST",
  "path": "/v1/messages",
  "headers": {...},
  "body": {...}
}
```

### Add/Update Key (Admin)
```
POST /keys/{api_name}
Authorization: Bearer <admin_token>

Body:
{
  "key": "sk-..."
}
```

### Remove Key (Admin)
```
DELETE /keys/{api_name}
Authorization: Bearer <admin_token>
```

### View Audit Logs (Admin)
```
GET /audit?limit=100&api_name=claude
Authorization: Bearer <admin_token>
```

## Architecture

- **auth.py**: JWT token creation & verification
- **keys.py**: Bitwarden Secrets Manager integration
- **proxy.py**: Route requests to real APIs with key injection
- **audit.py**: JSONL audit logging
- **server.py**: FastAPI server with HTTP & MCP endpoints

## Deployment

### Cloud Run

```bash
gcloud run deploy sidecar \
  --source . \
  --platform managed \
  --region us-central1 \
  --no-allow-unauthenticated \
  --set-env-vars \
    JWT_SECRET_KEY=<secret>,\
    BITWARDEN_SM_TOKEN=<token>
```

### Docker

```bash
docker build -t sidecar .
docker run -e JWT_SECRET_KEY=... -e BITWARDEN_SM_TOKEN=... -p 8000:8000 sidecar
```

### systemd (VM)

See [DEPLOYMENT.md](./DEPLOYMENT.md) for systemd service setup.

## Security

- All API keys stored in Bitwarden Secrets Manager (encrypted at rest, in transit)
- JWT-based authentication for all requests
- Audit log records every access (user, API, timestamp, status)
- No keys logged or printed — only references to API names
- HTTP-only; use HTTPS in production

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md).

## License

MIT
