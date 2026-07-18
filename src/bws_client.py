"""Bitwarden Secrets Manager Python SDK client."""

import os
from typing import Optional

from bitwarden_sdk import BitwardenClient, ClientSettings


class BWSClient:
    """Interface to Bitwarden Secrets Manager via Python SDK."""

    def __init__(self, access_token: Optional[str] = None):
        """Initialize BWS client.

        Args:
            access_token: Bitwarden SM access token. If not provided,
                         reads from BITWARDEN_SM_TOKEN env var.
        """
        self.token = access_token or os.getenv("BITWARDEN_SM_TOKEN")
        if not self.token:
            raise ValueError("BITWARDEN_SM_TOKEN not set in environment")

        settings = ClientSettings(
            server_name="us",
            api_url=os.getenv("BITWARDEN_API_URL", "https://api.bitwarden.us"),
        )
        self.client = BitwardenClient(settings=settings, access_token=self.token)

    def get_secret(self, key: str) -> str:
        """Fetch a secret from Bitwarden Secrets Manager.

        Args:
            key: Secret key/name (e.g., 'jwt-secret')

        Returns:
            Secret value

        Raises:
            RuntimeError: If secret not found or API call fails
        """
        try:
            # SDK returns secret object with attributes
            secret = self.client.secrets.get(id=key)
            if secret and hasattr(secret, 'value'):
                return secret.value

            # Fallback: try as a key name
            secrets = self.client.secrets.list()
            for s in secrets:
                if s.key == key:
                    return s.value

            raise RuntimeError(f"Secret '{key}' not found in Bitwarden")
        except Exception as e:
            raise RuntimeError(f"Failed to fetch secret '{key}': {str(e)}")

    def list_secrets(self) -> list[str]:
        """List all secret keys in Bitwarden Secrets Manager.

        Returns:
            List of secret key names
        """
        try:
            secrets = self.client.secrets.list()
            return [s.key for s in secrets if hasattr(s, 'key')]
        except Exception as e:
            raise RuntimeError(f"Failed to list secrets: {str(e)}")
