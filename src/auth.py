"""JWT authentication and authorization."""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import HTTPException, status


class AuthManager:
    def __init__(self, secret_key: Optional[str] = None):
        self.secret_key = secret_key or os.getenv("JWT_SECRET_KEY")
        if not self.secret_key:
            raise ValueError("JWT_SECRET_KEY not set in environment")
        self.algorithm = "HS256"

    def create_token(self, subject: str, expires_delta: Optional[timedelta] = None) -> str:
        """Create a signed JWT token."""
        if expires_delta is None:
            expires_delta = timedelta(hours=24)

        expire = datetime.now(timezone.utc) + expires_delta
        payload = {"sub": subject, "exp": expire}
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> str:
        """Verify and decode a JWT token. Returns the subject (user/service name)."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            subject: str = payload.get("sub")
            if subject is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token: missing subject",
                )
            return subject
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
            )
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}",
            )
