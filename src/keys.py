"""Key management via Bitwarden Secrets Manager."""

import os
from typing import Optional

try:
    from bitwarden_sdk import BitwardenClient, ClientSettings
    BITWARDEN_AVAILABLE = True
except ImportError:
    BITWARDEN_AVAILABLE = False


class KeyStore:
    """Interface to Bitwarden Secrets Manager for secure key storage."""

    def __init__(self):
        self.client = self._init_client()

    def _init_client(self) -> BitwardenClient:
        """Initialize Bitwarden client."""
        token = os.getenv("BITWARDEN_SM_TOKEN")
        if not token:
            raise ValueError("BITWARDEN_SM_TOKEN not set in environment")

        # Initialize client with access token
        # (SDK will auto-configure endpoints based on token domain)
        client = BitwardenClient(
            access_token=token,
            api_url=os.getenv("BITWARDEN_API_URL"),
        )
        return client

    def get_key(self, api_name: str) -> str:
        """Retrieve API key from Bitwarden Secrets Manager.

        Args:
            api_name: API identifier (e.g., 'claude', 'openai')

        Returns:
            API key string

        Raises:
            KeyError: If key not found in Bitwarden
        """
        try:
            secret = self.client.secrets.get(key=api_name)
            if not secret:
                raise KeyError(f"Secret '{api_name}' not found in Bitwarden")
            return secret.value
        except Exception as e:
            raise KeyError(f"Failed to retrieve key for '{api_name}': {str(e)}")

    def set_key(self, api_name: str, key: str) -> None:
        """Store or update an API key in Bitwarden Secrets Manager.

        Args:
            api_name: API identifier
            key: API key value
        """
        try:
            self.client.secrets.create(key=api_name, value=key)
        except Exception as e:
            raise RuntimeError(f"Failed to store key for '{api_name}': {str(e)}")

    def delete_key(self, api_name: str) -> None:
        """Remove an API key from Bitwarden Secrets Manager.

        Args:
            api_name: API identifier
        """
        try:
            self.client.secrets.delete(key=api_name)
        except Exception as e:
            raise RuntimeError(f"Failed to delete key for '{api_name}': {str(e)}")

    def list_keys(self) -> list[str]:
        """List all available API key names."""
        try:
            secrets = self.client.secrets.list()
            return [s.key for s in secrets]
        except Exception as e:
            raise RuntimeError(f"Failed to list keys: {str(e)}")
