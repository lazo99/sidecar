"""API request proxy with key injection."""

import httpx
from typing import Any, Optional

from .keys import KeyStore
from .audit import AuditLog


class APIProxy:
    """Proxy requests to real APIs with key injection."""

    # API registry: maps API name to endpoint config
    REGISTRY = {
        "claude": {
            "base_url": "https://api.anthropic.com",
            "auth_header": "x-api-key",
            "description": "Anthropic Claude API",
        },
        "openai": {
            "base_url": "https://api.openai.com",
            "auth_header": "authorization",
            "prefix": "Bearer ",
            "description": "OpenAI API",
        },
        "gcp": {
            "base_url": "https://googleapis.com",
            "auth_header": "authorization",
            "prefix": "Bearer ",
            "description": "Google Cloud APIs",
        },
    }

    def __init__(self, key_store: KeyStore, audit_log: AuditLog):
        self.key_store = key_store
        self.audit_log = audit_log
        self.http_client = httpx.AsyncClient(timeout=30.0)

    async def proxy_request(
        self,
        api_name: str,
        method: str,
        path: str,
        user: str,
        headers: Optional[dict] = None,
        body: Optional[dict] = None,
    ) -> Any:
        """Proxy a request to the target API with key injection.

        Args:
            api_name: Registered API name (e.g., 'claude')
            method: HTTP method (GET, POST, etc.)
            path: Request path (e.g., '/v1/messages')
            user: Authenticated user/service making the request
            headers: Additional request headers
            body: Request body (for POST/PUT)

        Returns:
            Response data from target API

        Raises:
            ValueError: If API is not registered or key retrieval fails
            httpx.HTTPError: On network/HTTP errors
        """
        if api_name not in self.REGISTRY:
            raise ValueError(f"Unknown API: {api_name}")

        config = self.REGISTRY[api_name]
        api_key = self.key_store.get_key(api_name)
        url = f"{config['base_url']}{path}"

        # Build headers with auth
        req_headers = headers or {}
        auth_value = api_key
        if "prefix" in config:
            auth_value = f"{config['prefix']}{api_key}"
        req_headers[config["auth_header"]] = auth_value

        # Log request
        self.audit_log.log_access(
            user=user,
            api=api_name,
            method=method,
            path=path,
            status="pending",
        )

        try:
            response = await self.http_client.request(
                method=method,
                url=url,
                headers=req_headers,
                json=body,
            )
            response.raise_for_status()

            # Log success
            self.audit_log.log_access(
                user=user,
                api=api_name,
                method=method,
                path=path,
                status="success",
                status_code=response.status_code,
            )

            return response.json()

        except httpx.HTTPError as e:
            # Log failure
            self.audit_log.log_access(
                user=user,
                api=api_name,
                method=method,
                path=path,
                status="error",
                error=str(e),
            )
            raise

    def get_api_info(self, api_name: str) -> dict:
        """Get metadata about a registered API."""
        if api_name not in self.REGISTRY:
            raise ValueError(f"Unknown API: {api_name}")
        return self.REGISTRY[api_name].copy()

    def list_apis(self) -> list[dict]:
        """List all registered APIs."""
        return [
            {"name": name, **config}
            for name, config in self.REGISTRY.items()
        ]
