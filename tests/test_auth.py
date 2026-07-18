"""Tests for authentication module."""

import pytest
from src.auth import AuthManager


@pytest.fixture
def auth_manager():
    return AuthManager(secret_key="test-secret-key-at-least-32-characters-long")


def test_create_and_verify_token(auth_manager):
    """Test JWT token creation and verification."""
    token = auth_manager.create_token("testuser")
    subject = auth_manager.verify_token(token)
    assert subject == "testuser"


def test_invalid_token(auth_manager):
    """Test that invalid tokens raise HTTPException."""
    with pytest.raises(Exception):  # HTTPException
        auth_manager.verify_token("invalid.token.here")


def test_expired_token(auth_manager):
    """Test that expired tokens raise HTTPException."""
    from datetime import timedelta
    import jwt

    token = auth_manager.create_token("testuser", expires_delta=timedelta(seconds=-1))
    with pytest.raises(Exception):  # HTTPException
        auth_manager.verify_token(token)
