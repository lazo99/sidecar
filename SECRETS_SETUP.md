# Secrets Setup Guide

This guide covers setting up Bitwarden Secrets Manager for Sidecar.

## Prerequisites

1. Bitwarden account (free or paid)
2. Bitwarden Secrets Manager CLI (`bws`) — installed automatically by deploy script

## Step 1: Set Up Bitwarden Secrets Manager

1. Log in to Bitwarden at https://vault.bitwarden.com
2. Create a new **Organization** (if you don't have one)
3. Go to **Secrets Manager** and create a project (e.g., "Sidecar")
4. In Secrets Manager, generate an **Access Token**:
   - Click your profile → **Service Accounts**
   - Create a new Service Account
   - Generate an access token (copy and save securely)

## Step 1.5: Create JWT Secret in Bitwarden

This is Sidecar's own secret (not an API key):

1. In Bitwarden Secrets Manager, click **Create secret**
2. Set:
   - **Name**: `jwt-secret`
   - **Value**: Generate a random 32+ character string:
     ```bash
     python -c "import secrets; print(secrets.token_hex(32))"
     ```
   - Click **Save**

The `jwt-secret` is fetched at Sidecar startup via `bws` CLI.

## Step 2: Create Secrets in Bitwarden

For each API you plan to proxy, create a secret in Secrets Manager:

```bash
export BW_CLIENTID=your-client-id
export BW_CLIENTSECRET=your-client-secret

# Login
bw auth login

# Create secrets (use API name as key)
bw secret create claude sk-ant-... --project sidecar
bw secret create openai sk-proj-... --project sidecar
bw secret create gcp <gcp-service-account-json> --project sidecar
```

Or via Bitwarden web UI:
1. Go to Secrets Manager → Your Project
2. Click **Create secret**
3. Set Name to API name (e.g., `claude`, `openai`)
4. Paste the API key in the value field

## Step 3: Configure Sidecar

### Environment Variables

Create `.env` (or set in production):

```env
BITWARDEN_SM_TOKEN=<your-access-token>
PORT=8000
```

That's it! Sidecar fetches `jwt-secret` from Bitwarden at startup.

### For Local Development

```bash
cp .env.example .env
# Edit .env and fill in:
# - BITWARDEN_SM_TOKEN from step 1
```

Then:
```bash
# Ensure bws CLI is installed
curl -fsSL https://vault.bitwarden.com/download/sm/bws/linux | bash
sudo mv bws /usr/local/bin/

# Run server (fetches jwt-secret from Bitwarden)
python -m src.server
```

### For VM Deployment

The `deploy-vm.sh` script handles everything:

```bash
BITWARDEN_SM_TOKEN=<your-token> bash deploy-vm.sh
```

It:
- Installs `bws` CLI
- Sets up `.env` with your token
- Creates systemd service
- Starts Sidecar (which fetches jwt-secret from Bitwarden)

### For Production (Cloud Run)

Store only the Bitwarden token in Google Secret Manager:

```bash
# Create secret in Google Secret Manager
echo -n "your-bitwarden-token" | gcloud secrets create BITWARDEN_SM_TOKEN --data-file=-

# Deploy with secret reference
gcloud run deploy sidecar \
  --image gcr.io/your-project/sidecar \
  --set-env-vars BITWARDEN_SM_TOKEN=from_secret:BITWARDEN_SM_TOKEN
```

Cloud Run must have `bws` CLI installed in Dockerfile (deploy script handles this).

## Step 4: Verify Setup

```bash
python -m src.server
```

In another terminal:

```bash
# Generate a token
python -c "from src.auth import AuthManager; auth = AuthManager(secret_key='test-key-32-chars-minimum'); print(auth.create_token('test'))"

# List keys
curl http://localhost:8000/apis \
  -H "Authorization: Bearer $TOKEN"
```

## Rotating Keys

To rotate an API key:

1. Update the secret in Bitwarden Secrets Manager
2. All subsequent Sidecar requests use the new key
3. No app restart needed

## Troubleshooting

### "BITWARDEN_SM_TOKEN not set"
- Ensure `.env` file exists with the token
- Or export as env var: `export BITWARDEN_SM_TOKEN=...`

### "Secret not found"
- Verify secret exists in Bitwarden Secrets Manager
- Check secret name matches API name in `proxy.py` REGISTRY
- Verify Service Account has access to the project

### "Invalid token"
- Regenerate access token in Bitwarden
- Ensure token hasn't expired (check Bitwarden web UI)

## References

- Bitwarden Docs: https://bitwarden.com/help/manage-secrets/
- Bitwarden Python SDK: https://github.com/bitwarden/sdk-python
