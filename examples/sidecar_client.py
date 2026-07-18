"""Python client for Sidecar API key proxy.

Usage:
    from sidecar_client import SidecarClient

    client = SidecarClient(
        url="http://localhost:8000",
        token="eyJ..."
    )

    # Call Claude API through sidecar
    response = client.proxy("claude", "POST", "/v1/messages", {
        "model": "claude-3-sonnet-20240229",
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": "Hello!"}]
    })
    print(response)
"""

import httpx
from typing import Any, Optional


class SidecarClient:
    """Client for calling APIs through Sidecar proxy."""

    def __init__(self, url: str, token: str, timeout: float = 30.0):
        """Initialize Sidecar client.

        Args:
            url: Sidecar URL (e.g., "http://localhost:8000")
            token: JWT authentication token
            timeout: Request timeout in seconds
        """
        self.url = url.rstrip("/")
        self.token = token
        self.timeout = timeout
        self.client = httpx.Client(
            headers={"Authorization": f"Bearer {token}"},
            timeout=timeout,
        )

    def list_apis(self) -> list[dict]:
        """List all available APIs."""
        response = self.client.get(f"{self.url}/apis")
        response.raise_for_status()
        return response.json()["apis"]

    def proxy(
        self,
        api_name: str,
        method: str,
        path: str,
        body: Optional[dict] = None,
        headers: Optional[dict] = None,
    ) -> Any:
        """Proxy a request to an API through Sidecar.

        Args:
            api_name: API name (e.g., "claude", "openai")
            method: HTTP method (GET, POST, etc.)
            path: Request path (e.g., "/v1/messages")
            body: Request body (for POST/PUT)
            headers: Additional request headers

        Returns:
            API response JSON

        Raises:
            httpx.HTTPError: On request failure
        """
        request_body = {
            "method": method,
            "path": path,
            "headers": headers or {},
        }
        if body:
            request_body["body"] = body

        response = self.client.post(
            f"{self.url}/api/{api_name}/proxy",
            json=request_body,
        )
        response.raise_for_status()
        result = response.json()
        return result.get("result", result)

    def close(self):
        """Close the client connection."""
        self.client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Example usage
if __name__ == "__main__":
    import os
    import json

    # Get credentials from environment
    sidecar_url = os.getenv("SIDECAR_URL", "http://localhost:8000")
    sidecar_token = os.getenv("SIDECAR_TOKEN")

    if not sidecar_token:
        print("Error: Set SIDECAR_TOKEN environment variable")
        exit(1)

    # Test the client
    with SidecarClient(url=sidecar_url, token=sidecar_token) as client:
        # List available APIs
        print("Available APIs:")
        apis = client.list_apis()
        for api in apis:
            print(f"  - {api['name']}: {api['base_url']}")

        # Example: Call Claude API
        print("\nTesting Claude API proxy...")
        try:
            response = client.proxy(
                "claude",
                "POST",
                "/v1/messages",
                {
                    "model": "claude-3-sonnet-20240229",
                    "max_tokens": 100,
                    "messages": [{"role": "user", "content": "Say 'Hello from Sidecar!'"}],
                },
            )
            print(f"Response: {json.dumps(response, indent=2)}")
        except Exception as e:
            print(f"Error: {e}")
