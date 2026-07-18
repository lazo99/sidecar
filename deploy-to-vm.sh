#!/bin/bash
set -e

# Deploy Sidecar to miss-minutes VM securely
# Handles: token storage, SCP, SSH, and systemd setup

VM_NAME="miss-minutes"
VM_ZONE="us-west1-b"
DEPLOY_SCRIPT="deploy-vm.sh"

echo "🚀 Sidecar VM Deployment Helper"
echo ""

# Step 1: Get token securely
echo "1️⃣  Enter your Bitwarden SM Token (hidden):"
read -sp "Token: " BW_TOKEN
echo ""

if [ -z "$BW_TOKEN" ]; then
    echo "❌ Token is empty"
    exit 1
fi

# Step 2: Store locally (encrypted in ~/.secrets)
echo "2️⃣  Storing token locally in ~/.secrets/..."
mkdir -p ~/.secrets
echo "$BW_TOKEN" > ~/.secrets/bitwarden-token.txt
chmod 600 ~/.secrets/bitwarden-token.txt
echo "✓ Token stored at ~/.secrets/bitwarden-token.txt"

# Step 3: SCP token to VM (via IAP tunnel)
echo ""
echo "3️⃣  Copying token to VM..."
gcloud compute scp ~/.secrets/bitwarden-token.txt $VM_NAME:~/.secrets/bitwarden-token.txt \
    --zone $VM_ZONE \
    --tunnel-through-iap \
    --quiet
echo "✓ Token copied to VM"

# Step 4: SCP deploy script to VM (via IAP tunnel)
echo ""
echo "4️⃣  Copying deploy script to VM..."
gcloud compute scp $DEPLOY_SCRIPT $VM_NAME:~/$DEPLOY_SCRIPT \
    --zone $VM_ZONE \
    --tunnel-through-iap \
    --quiet
echo "✓ Deploy script copied"

# Step 5: Run deploy on VM (via IAP tunnel)
echo ""
echo "5️⃣  Running deployment on VM..."
gcloud compute ssh $VM_NAME --zone $VM_ZONE --tunnel-through-iap --command "bash ~/$DEPLOY_SCRIPT"

# Step 6: Verify (via IAP tunnel)
echo ""
echo "6️⃣  Verifying deployment..."
gcloud compute ssh $VM_NAME --zone $VM_ZONE --tunnel-through-iap --command "sudo systemctl status sidecar --no-pager"

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Next steps:"
echo "  1. Check logs: gcloud compute ssh $VM_NAME --zone $VM_ZONE -- 'sudo journalctl -u sidecar -f'"
echo "  2. Test health: gcloud compute ssh $VM_NAME --zone $VM_ZONE -- 'curl http://localhost:8000/health'"
echo "  3. Get VM IP: gcloud compute instances list --filter=name:$VM_NAME"
