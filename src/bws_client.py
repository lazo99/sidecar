"""Bitwarden Secrets Manager CLI client."""

import json
import os
import subprocess
from typing import Optional


class BWSClient:
    """Interface to Bitwarden Secrets Manager via `bws` CLI."""

    def __init__(self, access_token: Optional[str] = None):
        """Initialize BWS client.

        Args:
            access_token: Bitwarden SM access token. If not provided,
                         reads from BITWARDEN_SM_TOKEN env var.
        """
        self.token = access_token or os.getenv("BITWARDEN_SM_TOKEN")
        if not self.token:
            raise ValueError("BITWARDEN_SM_TOKEN not set in environment")

    def get_secret(self, key: str) -> str:
        """Fetch a secret from Bitwarden Secrets Manager.

        Args:
            key: Secret key/name (e.g., 'jwt-secret')

        Returns:
            Secret value

        Raises:
            RuntimeError: If `bws` command fails or secret not found
        """
        try:
            result = subprocess.run(
                ["bws", "secret", "get", key],
                env={**os.environ, "BWS_ACCESS_TOKEN": self.token},
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                raise RuntimeError(f"bws failed: {result.stderr}")

            # bws returns JSON
            data = json.loads(result.stdout)
            return data.get("value", "")

        except subprocess.TimeoutExpired:
            raise RuntimeError(f"bws timeout fetching secret '{key}'")
        except json.JSONDecodeError:
            raise RuntimeError(f"Invalid response from bws: {result.stdout}")
        except FileNotFoundError:
            raise RuntimeError(
                "bws CLI not found. Install: "
                "curl -fsSL https://vault.bitwarden.com/download/sm/bws/linux | bash"
            )

    def list_secrets(self) -> list[str]:
        """List all secret keys in Bitwarden Secrets Manager.

        Returns:
            List of secret key names
        """
        try:
            result = subprocess.run(
                ["bws", "secret", "list"],
                env={**os.environ, "BWS_ACCESS_TOKEN": self.token},
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                raise RuntimeError(f"bws failed: {result.stderr}")

            data = json.loads(result.stdout)
            return [s.get("key") for s in data.get("data", []) if s.get("key")]

        except (subprocess.TimeoutExpired, json.JSONDecodeError) as e:
            raise RuntimeError(f"Failed to list secrets: {str(e)}")
