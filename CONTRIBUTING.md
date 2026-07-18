# Contributing to Sidecar

## Local Setup

```bash
git clone https://github.com/hats-off-it/sidecar.git
cd sidecar

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dev dependencies
pip install -r requirements.txt
pip install black ruff pytest pytest-asyncio

# Setup environment
cp .env.example .env.local
# Edit .env.local with test Bitwarden token
```

## Running Tests

```bash
pytest tests/ -v
```

For async tests:
```bash
pytest tests/ -v --asyncio-mode=auto
```

## Code Style

Format with black:
```bash
black src/ tests/
```

Lint with ruff:
```bash
ruff check src/ tests/
```

## Making Changes

1. Create a branch: `git checkout -b feature/your-feature`
2. Make your changes
3. Add tests in `tests/`
4. Run tests: `pytest tests/ -v`
5. Format & lint: `black . && ruff check .`
6. Commit: `git commit -am "Description of change"`
7. Push: `git push origin feature/your-feature`
8. Open a pull request

## Adding a New API

To add support for a new API (e.g., OpenAI):

1. Edit `src/proxy.py` and add to `REGISTRY`:
```python
"openai": {
    "base_url": "https://api.openai.com",
    "auth_header": "authorization",
    "prefix": "Bearer ",
    "description": "OpenAI API",
}
```

2. Add key to Bitwarden Secrets Manager:
```bash
bw secret create openai sk-...
```

3. Test via API:
```bash
curl -X GET http://localhost:8000/apis/openai \
  -H "Authorization: Bearer $TOKEN"
```

## Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for deployment steps.

## Questions?

Open an issue or check existing PRs.
