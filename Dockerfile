FROM python:3.11-slim

WORKDIR /app

# Install bws CLI (Bitwarden Secrets Manager) from GitHub releases
RUN BWS_VERSION=$(curl -s https://api.github.com/repos/bitwarden/sdk-sm/releases/latest | grep -oP '"tag_name": "v\K[^"]+') && \
    curl -fsSL "https://github.com/bitwarden/sdk-sm/releases/download/v${BWS_VERSION}/bws-x86_64-unknown-linux-musl" -o /usr/local/bin/bws && \
    chmod +x /usr/local/bin/bws

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Create logs directory
RUN mkdir -p logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:${PORT}/health')" || exit 1

# Run the server
CMD ["python", "-m", "src.server"]
