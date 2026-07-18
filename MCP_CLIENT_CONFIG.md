# MCP Client Configuration for Sidecar

## Step 1: Get Your JWT Token

Generate a token on the VM:

```bash
gcloud compute ssh miss-minutes --zone us-west1-b --tunnel-through-iap --command "
cd /opt/sidecar
export JWT_SECRET_KEY=\$(grep ^JWT_SECRET_KEY .env | cut -d= -f2)
source venv/bin/activate
python3 -c \"from src.auth import AuthManager; import os; print(AuthManager(secret_key=os.getenv('JWT_SECRET_KEY')).create_token('your-laptop'))\"
"
```

Copy the token output.

## Step 2: Get VM IP Address

```bash
gcloud compute instances describe miss-minutes --zone us-west1-b --format="value(networkInterfaces[0].accessConfigs[0].natIP)"
```

Or if that's only internal:
```bash
gcloud compute instances describe miss-minutes --zone us-west1-b --format="value(networkInterfaces[0].networkIP)"
```

## Step 3: Configure Your MCP Client

### Option A: Direct HTTP Access (if VM is public)

Add to your MCP config (e.g., ~/.claude/mcp.json):

```json
{
  "resources": [
    {
      "type": "api",
      "name": "sidecar-proxy",
      "url": "http://<VM_IP>:8000",
      "headers": {
        "Authorization": "Bearer <YOUR_JWT_TOKEN>"
      }
    }
  ]
}
```

### Option B: Via IAP Tunnel (recommended)

Create a local port forward:

```bash
gcloud compute ssh miss-minutes --zone us-west1-b --tunnel-through-iap \
  -- -L 8000:localhost:8000
```

Then use:
```json
{
  "resources": [
    {
      "type": "api",
      "name": "sidecar-proxy",
      "url": "http://localhost:8000",
      "headers": {
        "Authorization": "Bearer <YOUR_JWT_TOKEN>"
      }
    }
  ]
}
```

## Step 4: Test the Connection

```bash
# Get token
TOKEN=$(gcloud compute ssh miss-minutes --zone us-west1-b --tunnel-through-iap \
  --command "cd /opt/sidecar && export JWT_SECRET_KEY=\$(grep ^JWT_SECRET_KEY .env | cut -d= -f2) && source venv/bin/activate && python3 -c \"from src.auth import AuthManager; import os; print(AuthManager(secret_key=os.getenv('JWT_SECRET_KEY')).create_token('test'))\"")

# Test /apis endpoint
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/apis
```

Expected response:
```json
{
  "apis": [
    {"name": "claude", "base_url": "https://api.anthropic.com", ...},
    {"name": "openai", "base_url": "https://api.openai.com", ...},
    {"name": "gcp", "base_url": "https://googleapis.com", ...}
  ]
}
```

## Step 5: Use Sidecar from Your MCP Client

Once configured, your local agents can call:

```bash
# Proxy a Claude API request through sidecar
curl -X POST http://localhost:8000/api/claude/proxy \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "method": "POST",
    "path": "/v1/messages",
    "body": {
      "model": "claude-3-sonnet-20240229",
      "max_tokens": 1024,
      "messages": [{"role": "user", "content": "Hello!"}]
    }
  }'
```

Sidecar will:
1. Inject your API_KEY_CLAUDE from .env
2. Forward to https://api.anthropic.com/v1/messages
3. Return the response

## Troubleshooting

**401 Unauthorized**: Check JWT token is valid and not expired
**503 Service Unavailable**: API key not found (add API_KEY_CLAUDE to .env)
**Connection refused**: Check VM is running, port 8000 is listening, IAP tunnel is active

## Next Steps

1. Add your API keys to /opt/sidecar/.env
2. Restart sidecar: `sudo systemctl restart sidecar`
3. Generate a JWT token for your laptop
4. Configure your MCP client with the token and URL
5. Test with `curl` first, then integrate into your agents
