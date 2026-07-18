#!/bin/bash
set -e

echo "🚀 Deploying Sidecar to VM..."

# Configuration
REPO_URL="https://github.com/lazo99/sidecar.git"
INSTALL_DIR="/opt/sidecar"
SERVICE_NAME="sidecar"

# Step 0: Install bws CLI
echo "📥 Installing Bitwarden Secrets Manager CLI..."
if ! command -v bws &> /dev/null; then
    curl -fsSL https://vault.bitwarden.com/download/sm/bws/linux | bash
    sudo mv bws /usr/local/bin/
    bws --version
else
    echo "✓ bws already installed"
fi

# Step 1: Clone/update repo
echo "📦 Cloning repository..."
if [ -d "$INSTALL_DIR" ]; then
    cd "$INSTALL_DIR"
    git pull
else
    sudo git clone "$REPO_URL" "$INSTALL_DIR"
    sudo chown -R $USER:$USER "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"

# Step 2: Create venv
echo "🐍 Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate
pip install -q -r requirements.txt

# Step 3: Create .env with Bitwarden token only
echo "🔐 Setting up environment..."
if [ ! -f .env ]; then
    cp .env.example .env

    # If BITWARDEN_SM_TOKEN is set as env var, use it
    if [ -z "$BITWARDEN_SM_TOKEN" ]; then
        echo ""
        echo "⚠️  Edit .env and add your BITWARDEN_SM_TOKEN"
        echo "   (Get it from https://vault.bitwarden.com/sm/)"
        echo ""
        read -p "Press Enter after editing .env..."
    else
        # Replace placeholder with actual token
        sed -i "s/BITWARDEN_SM_TOKEN=.*/BITWARDEN_SM_TOKEN=$BITWARDEN_SM_TOKEN/" .env
        echo "✓ BITWARDEN_SM_TOKEN configured from environment"
    fi
else
    echo "✓ .env already exists"
fi

chmod 600 .env

# Step 4: Create systemd service
echo "🔧 Creating systemd service..."
sudo tee /etc/systemd/system/sidecar.service > /dev/null <<EOF
[Unit]
Description=Sidecar API Key Vault
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$INSTALL_DIR/venv/bin"
EnvironmentFile=$INSTALL_DIR/.env
ExecStart=$INSTALL_DIR/venv/bin/python -m src.server
Restart=on-failure
RestartSec=10

NoNewPrivileges=true
PrivateTmp=true
ReadWritePaths=$INSTALL_DIR/logs

[Install]
WantedBy=multi-user.target
EOF

# Step 5: Enable and start service
echo "▶️  Starting service..."
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl restart $SERVICE_NAME

# Step 6: Verify
echo ""
echo "✅ Deployment complete!"
echo ""
echo "Verify status:"
echo "  sudo systemctl status $SERVICE_NAME"
echo ""
echo "View logs:"
echo "  sudo journalctl -u $SERVICE_NAME -f"
echo ""
echo "Health check:"
echo "  curl http://localhost:8000/health"
echo ""
echo "Next steps:"
echo "  1. Generate JWT token: python -m src.auth"
echo "  2. Test API: curl http://localhost:8000/apis -H 'Authorization: Bearer <token>'"
