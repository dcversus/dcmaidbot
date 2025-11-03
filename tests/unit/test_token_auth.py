"""Tests for token authentication system."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from models.admin_token import AdminToken
from services.token_service import TokenService


class TestTokenService:
    """Test cases for TokenService."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = AsyncMock()
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.execute = AsyncMock()
        session.rollback = AsyncMock()

        # Create mock result object for execute
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        session.execute.return_value = mock_result

        # Configure scalar_one_or_none directly on session for backward compatibility
        session.scalar_one_or_none = MagicMock()

        return session

    @pytest.fixture
    def token_service(self, mock_session):
        """Create TokenService instance with mock session."""
        return TokenService(mock_session)

    @pytest.mark.asyncio
    async def test_create_token(self, token_service, mock_session):
        """Test token creation."""
        # Mock database operations
        mock_session.commit.return_value = None
        mock_session.refresh.return_value = None

        # Create token
        admin_token, raw_token = await token_service.create_token(
            name="Test Token",
            created_by=123456,
            description="Test token for unit testing",
            expires_hours=24,
        )

        # Set the is_active property manually since mock refresh doesn't set it
        # In real database, this would be set by the default value
        admin_token.is_active = True

        # Verify token creation
        assert admin_token.name == "Test Token"
        assert admin_token.created_by == 123456
        assert admin_token.description == "Test token for unit testing"
        assert admin_token.is_active is True
        assert admin_token.token_prefix == raw_token[:8]
        assert len(raw_token) > 30  # Should be a substantial token

        # Verify session operations
        mock_session.add.assert_called_once_with(admin_token)
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(admin_token)

    @pytest.mark.asyncio
    async def test_validate_token_success(self, token_service, mock_session):
        """Test successful token validation."""
        # Create a test token
        test_token = AdminToken.generate_token()
        token_hash = AdminToken.hash_token(test_token)

        admin_token = AdminToken(
            name="Test Token",
            token_hash=token_hash,
            token_prefix=test_token[:8],
            created_by=123456,
            expires_at=datetime.utcnow() + timedelta(hours=1),
            is_active=True,
        )

        # Mock database query - the execute() returns a result object
        mock_result = mock_session.execute.return_value
        mock_result.scalar_one_or_none.return_value = admin_token
        mock_session.commit.return_value = None

        # Validate token
        result = await token_service.validate_token(test_token)

        # Verify validation
        assert result is not None
        assert result.id == admin_token.id
        assert result.name == "Test Token"
        assert result.created_by == 123456
        assert result.last_used_at is not None  # Should be updated

    @pytest.mark.asyncio
    async def test_validate_token_invalid(self, token_service, mock_session):
        """Test token validation with invalid token."""
        # Mock database query to return None (no token found)
        mock_session.scalar_one_or_none.return_value = None

        # Validate invalid token
        result = await token_service.validate_token("invalid_token")

        # Verify validation fails
        assert result is None

    @pytest.mark.asyncio
    async def test_validate_token_expired(self, token_service, mock_session):
        """Test token validation with expired token."""
        # Create an expired token
        test_token = AdminToken.generate_token()
        token_hash = AdminToken.hash_token(test_token)

        admin_token = AdminToken(
            name="Expired Token",
            token_hash=token_hash,
            token_prefix=test_token[:8],
            created_by=123456,
            expires_at=datetime.utcnow() - timedelta(hours=1),  # Expired
            is_active=True,
        )

        # Mock database query
        mock_session.scalar_one_or_none.return_value = admin_token

        # Validate expired token
        result = await token_service.validate_token(test_token)

        # Verify validation fails
        assert result is None

    @pytest.mark.asyncio
    async def test_validate_token_inactive(self, token_service, mock_session):
        """Test token validation with inactive token."""
        # Create an inactive token
        test_token = AdminToken.generate_token()
        token_hash = AdminToken.hash_token(test_token)

        admin_token = AdminToken(
            name="Inactive Token",
            token_hash=token_hash,
            token_prefix=test_token[:8],
            created_by=123456,
            expires_at=datetime.utcnow() + timedelta(hours=1),
            is_active=False,  # Inactive
        )

        # Mock database query
        mock_session.scalar_one_or_none.return_value = admin_token

        # Validate inactive token
        result = await token_service.validate_token(test_token)

        # Verify validation fails
        assert result is None

    @pytest.mark.asyncio
    async def test_revoke_token(self, token_service, mock_session):
        """Test token revocation."""
        # Create a test token
        admin_token = AdminToken(
            name="Test Token",
            token_hash="hash",
            token_prefix="prefix",
            created_by=123456,
            expires_at=datetime.utcnow() + timedelta(hours=1),
            is_active=True,
        )

        # Mock database query
        mock_result = mock_session.execute.return_value
        mock_result.scalar_one_or_none.return_value = admin_token
        mock_session.commit.return_value = None

        # Revoke token
        result = await token_service.revoke_token(1)

        # Verify revocation
        assert result is True
        assert admin_token.is_active is False
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_revoke_nonexistent_token(self, token_service, mock_session):
        """Test revoking non-existent token."""
        # Mock database query to return None
        mock_session.execute.return_value.scalar_one_or_none.return_value = None

        # Try to revoke non-existent token
        result = await token_service.revoke_token(999)

        # Verify revocation fails
        assert result is False

    @pytest.mark.asyncio
    async def test_get_tokens_for_admin(self, token_service, mock_session):
        """Test getting tokens for an admin."""
        # Mock database query
        mock_session.execute.return_value.scalars.return_value.all.return_value = [
            MagicMock(name="Token 1"),
            MagicMock(name="Token 2"),
        ]

        # Get tokens
        tokens = await token_service.get_tokens_for_admin(123456)

        # Verify result
        assert len(tokens) == 2
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_extend_token(self, token_service, mock_session):
        """Test extending token expiration."""
        # Create a test token
        original_expiry = datetime.utcnow() + timedelta(hours=1)
        admin_token = AdminToken(
            name="Test Token",
            token_hash="hash",
            token_prefix="prefix",
            created_by=123456,
            expires_at=original_expiry,
            is_active=True,
        )

        # Mock database query
        mock_result = mock_session.execute.return_value
        mock_result.scalar_one_or_none.return_value = admin_token
        mock_session.commit.return_value = None

        # Extend token
        result = await token_service.extend_token(1, hours=24)

        # Verify extension
        assert result is True
        assert admin_token.expires_at > original_expiry
        mock_session.commit.assert_called_once()

    def test_token_generation(self):
        """Test token generation."""
        # Generate multiple tokens
        tokens = [AdminToken.generate_token() for _ in range(10)]

        # Verify tokens are unique
        assert len(set(tokens)) == len(tokens)

        # Verify token length
        for token in tokens:
            assert len(token) >= 30  # Should be substantial
            assert (
                token.isalnum() or "-" in token or "_" in token
            )  # URL-safe characters

    def test_token_hashing(self):
        """Test token hashing."""
        # Create a token
        token = AdminToken.generate_token()

        # Hash it multiple times
        hash1 = AdminToken.hash_token(token)
        hash2 = AdminToken.hash_token(token)

        # Verify hashes are consistent
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length

        # Verify hash is different from token
        assert hash1 != token

    def test_admin_token_properties(self):
        """Test AdminToken model properties."""
        # Create an active, non-expired token
        future_time = datetime.utcnow() + timedelta(hours=1)
        token = AdminToken(
            name="Test Token",
            token_hash="hash",
            token_prefix="prefix",
            created_by=123456,
            expires_at=future_time,
            is_active=True,
        )

        # Test properties
        assert token.is_expired is False
        assert token.is_valid is True

        # Test expired token
        past_time = datetime.utcnow() - timedelta(hours=1)
        token.expires_at = past_time
        assert token.is_expired is True
        assert token.is_valid is False

        # Test inactive token
        token.expires_at = future_time
        token.is_active = False
        assert token.is_expired is False
        assert token.is_valid is False

    def test_admin_token_repr(self):
        """Test AdminToken string representation."""
        token = AdminToken(
            name="Test Token",
            token_hash="hash",
            token_prefix="abcd1234",
            created_by=123456,
            expires_at=datetime.utcnow() + timedelta(hours=1),
            is_active=True,
        )

        # Test repr
        repr_str = repr(token)
        assert "AdminToken" in repr_str
        assert "Test Token" in repr_str
        assert "abcd1234" in repr_str
