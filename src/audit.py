"""Audit logging for API key access."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


class AuditLog:
    """Centralized audit log for key access and API requests."""

    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        # Setup file logger
        self.logger = logging.getLogger("sidecar.audit")
        self.logger.setLevel(logging.INFO)

        log_file = self.log_dir / "audit.jsonl"
        handler = logging.FileHandler(log_file)
        handler.setFormatter(logging.Formatter("%(message)s"))
        self.logger.addHandler(handler)

    def log_access(
        self,
        user: str,
        api: str,
        method: str,
        path: str,
        status: str,
        status_code: Optional[int] = None,
        error: Optional[str] = None,
    ) -> None:
        """Log an API access attempt.

        Args:
            user: Authenticated user/service
            api: API name (e.g., 'claude')
            method: HTTP method
            path: Request path
            status: Access status ('pending', 'success', 'error')
            status_code: HTTP status code if response received
            error: Error message if status is 'error'
        """
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user": user,
            "api": api,
            "method": method,
            "path": path,
            "status": status,
        }
        if status_code:
            entry["status_code"] = status_code
        if error:
            entry["error"] = error

        self.logger.info(json.dumps(entry))

    def log_key_operation(
        self,
        user: str,
        operation: str,
        api: str,
        result: str,
        error: Optional[str] = None,
    ) -> None:
        """Log a key management operation (add/remove/rotate).

        Args:
            user: Operator (who made the change)
            operation: Operation type ('add', 'remove', 'rotate')
            api: API name affected
            result: Operation result ('success', 'error')
            error: Error message if result is 'error'
        """
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "key_operation",
            "user": user,
            "operation": operation,
            "api": api,
            "result": result,
        }
        if error:
            entry["error"] = error

        self.logger.info(json.dumps(entry))

    def get_logs(self, limit: int = 100, filter_api: Optional[str] = None) -> list[dict]:
        """Retrieve recent audit logs.

        Args:
            limit: Max number of entries to return
            filter_api: Optional API name to filter by

        Returns:
            List of audit log entries
        """
        log_file = self.log_dir / "audit.jsonl"
        if not log_file.exists():
            return []

        entries = []
        with open(log_file) as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    if filter_api and entry.get("api") != filter_api:
                        continue
                    entries.append(entry)
                except json.JSONDecodeError:
                    continue

        return entries[-limit:]
