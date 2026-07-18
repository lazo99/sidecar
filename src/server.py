"""FastAPI server with MCP and HTTP endpoints."""

import os
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, status, Header
from pydantic import BaseModel

from .auth import AuthManager
from .keys import KeyStore
from .proxy import APIProxy
from .audit import AuditLog
from .bws_client import BWSClient

# Load .env file
load_dotenv()


app = FastAPI(
    title="Sidecar",
    description="Secure API key vault and proxy",
    version="0.1.0",
)

# Initialize components
key_store = KeyStore()
audit_log = AuditLog()
api_proxy = APIProxy(key_store, audit_log)

# Initialize AuthManager with JWT secret from Bitwarden or env
def _get_jwt_secret() -> str:
    """Fetch JWT secret from Bitwarden or environment."""
    # Try Bitwarden first (preferred)
    if os.getenv("BITWARDEN_SM_TOKEN"):
        try:
            bws = BWSClient()
            secret = bws.get_secret("jwt-secret")
            if secret:
                print("✓ JWT secret loaded from Bitwarden")
                return secret
        except Exception as e:
            print(f"⚠️  Failed to fetch JWT secret from Bitwarden: {e}")
            print("   Falling back to JWT_SECRET_KEY env var")

    # Fallback to env var (for testing or if Bitwarden unavailable)
    secret = os.getenv("JWT_SECRET_KEY")
    if not secret:
        raise ValueError("JWT secret not found in Bitwarden or JWT_SECRET_KEY env var")
    return secret

jwt_secret = _get_jwt_secret()
auth_manager = AuthManager(secret_key=jwt_secret)


# Dependency: extract and verify JWT from Authorization header
async def get_current_user(authorization: Optional[str] = Header(None)) -> str:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
        )
    try:
        # Expected format: "Bearer <token>"
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError("Invalid scheme")
        return auth_manager.verify_token(token)
    except (ValueError, IndexError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format",
        )


# Models
class ProxyRequest(BaseModel):
    method: str
    path: str
    headers: Optional[dict] = None
    body: Optional[dict] = None


class ProxyResponse(BaseModel):
    result: dict
    status: str


class KeyUpdate(BaseModel):
    key: str


class APIInfo(BaseModel):
    name: str
    base_url: str
    auth_header: str
    description: str


# Routes
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/api/{api_name}/proxy")
async def proxy_api(
    api_name: str,
    request: ProxyRequest,
    user: str = Depends(get_current_user),
):
    """Proxy a request to a registered API."""
    try:
        result = await api_proxy.proxy_request(
            api_name=api_name,
            method=request.method,
            path=request.path,
            user=user,
            headers=request.headers,
            body=request.body,
        )
        return ProxyResponse(result=result, status="success")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@app.get("/apis")
async def list_apis(user: str = Depends(get_current_user)):
    """List all registered APIs."""
    return {"apis": api_proxy.list_apis()}


@app.get("/apis/{api_name}")
async def get_api_info(api_name: str, user: str = Depends(get_current_user)):
    """Get metadata about a specific API."""
    try:
        info = api_proxy.get_api_info(api_name)
        return {"api": api_name, **info}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@app.post("/keys/{api_name}")
async def update_key(
    api_name: str,
    update: KeyUpdate,
    user: str = Depends(get_current_user),
):
    """Add or update an API key (admin only)."""
    # TODO: Add admin-only authorization check
    try:
        key_store.set_key(api_name, update.key)
        audit_log.log_key_operation(
            user=user,
            operation="add",
            api=api_name,
            result="success",
        )
        return {"status": "success", "api": api_name}
    except Exception as e:
        audit_log.log_key_operation(
            user=user,
            operation="add",
            api=api_name,
            result="error",
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@app.delete("/keys/{api_name}")
async def delete_key(api_name: str, user: str = Depends(get_current_user)):
    """Remove an API key (admin only)."""
    # TODO: Add admin-only authorization check
    try:
        key_store.delete_key(api_name)
        audit_log.log_key_operation(
            user=user,
            operation="remove",
            api=api_name,
            result="success",
        )
        return {"status": "success", "api": api_name}
    except Exception as e:
        audit_log.log_key_operation(
            user=user,
            operation="remove",
            api=api_name,
            result="error",
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@app.get("/audit")
async def get_audit_logs(
    limit: int = 100,
    api_name: Optional[str] = None,
    user: str = Depends(get_current_user),
):
    """Retrieve audit logs (admin only)."""
    # TODO: Add admin-only authorization check
    logs = audit_log.get_logs(limit=limit, filter_api=api_name)
    return {"logs": logs, "count": len(logs)}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
