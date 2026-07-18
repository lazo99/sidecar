"""Key management via environment variables."""

import os
from typing import Optional


class KeyStore:
    """Interface to API keys stored as environment variables."""

    def __init__(self):
        """Initialize KeyStore. Keys are read from env vars."""
        self.keys_loaded = True

    def get_key(self, api_name: str) -> str:
        """Retrieve API key from environment.

        Args:
            api_name: API identifier (e.g., 'claude', 'openai')

        Returns:
            API key string

        Raises:
            KeyError: If key not found
        """
        # Look for env var like API_KEY_CLAUDE, API_KEY_OPENAI, etc.
        env_var = f"API_KEY_{api_name.upper()}"
        key = os.getenv(env_var)
        if not key:
            raise KeyError(
                f"API key for '{api_name}' not found. "
                f"Set {env_var} environment variable."
            )
        return key

    def set_key(self, api_name: str, key: str) -> None:
        """Store an API key (not implemented for env vars).

        To add keys: Edit .env and set API_KEY_{API_NAME}=<key>
        """
        raise NotImplementedError(
            "Cannot set keys via API. Edit .env and set "
            f"API_KEY_{api_name.upper()}=<key>, then restart sidecar."
        )

    def delete_key(self, api_name: str) -> None:
        """Remove an API key (not implemented for env vars).

        To remove keys: Edit .env and remove API_KEY_{API_NAME}
        """
        raise NotImplementedError(
            "Cannot delete keys via API. Edit .env and remove "
            f"API_KEY_{api_name.upper()}, then restart sidecar."
        )

    def list_keys(self) -> list[str]:
        """List all API keys available in environment."""
        keys = []
        for key in os.environ:
            if key.startswith("API_KEY_"):
                api_name = key.replace("API_KEY_", "").lower()
                keys.append(api_name)
        return keys
