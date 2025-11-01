"""E2E tests for nudge token management system.

Tests the complete nudge token CRUD lifecycle that dcmaidbot can use
to create, list, view, and deactivate nudge tokens for /nudge endpoint
authentication.
"""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from models.nudge_token import NudgeToken
from services.nudge_token_service import NudgeTokenService


@pytest.fixture
async def nudge_token_service(async_session: AsyncSession):
    """Create nudge token service for testing."""
    return NudgeTokenService(async_session)


class TestNudgeTokenManagementE2E:
    """End-to-end tests for nudge token management system."""

    @pytest.mark.asyncio
    async def test_admin_can_create_nudge_token(
        self,
        async_session: AsyncSession,
        nudge_token_service: NudgeTokenService,
    ):
        """Test that admins can create nudge tokens with custom settings."""
        admin_id = 12345

        # Create nudge token with custom settings
        nudge_token, raw_token = await nudge_token_service.create_nudge_token(
            name="Test Admin Nudge Token",
            created_by=admin_id,
            description="Nudge token for testing admin functionality",
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )

        # Verify nudge token creation
        assert nudge_token.name == "Test Admin Nudge Token"
        assert nudge_token.created_by == admin_id
        assert nudge_token.is_active is True
        assert nudge_token.description == "Nudge token for testing admin functionality"
        assert nudge_token.usage_count == 0
        assert raw_token.startswith("nudge_")
        assert len(raw_token) >= 32  # Should be reasonably long
        assert nudge_token.is_valid() is True
        assert nudge_token.is_expired() is False

    @pytest.mark.asyncio
    async def test_admin_can_list_their_nudge_tokens(
        self,
        async_session: AsyncSession,
        nudge_token_service: NudgeTokenService,
    ):
        """Test that admins can list their own nudge tokens."""
        admin_id = 12345

        # Create multiple nudge tokens
        tokens_created = []
        for i in range(3):
            nudge_token, _ = await nudge_token_service.create_nudge_token(
                name=f"Test Token {i + 1}",
                created_by=admin_id,
                description=f"Test nudge token number {i + 1}",
            )
            tokens_created.append(nudge_token)

        # List nudge tokens for this admin
        nudge_tokens = await nudge_token_service.get_nudge_tokens_by_creator(admin_id)

        # Verify we got our tokens
        assert len(nudge_tokens) >= 3

        # Find our created tokens
        created_token_names = {token.name for token in tokens_created}
        returned_token_names = {token.name for token in nudge_tokens}

        assert created_token_names.issubset(returned_token_names)

        # Verify token details
        for token in nudge_tokens:
            if token.name.startswith("Test Token"):
                assert token.created_by == admin_id
                assert token.is_active is True
                assert token.token_prefix.startswith("nudge_")
                assert token.usage_count == 0

    @pytest.mark.asyncio
    async def test_admin_cannot_see_other_admins_tokens(
        self,
        async_session: AsyncSession,
        nudge_token_service: NudgeTokenService,
    ):
        """Test that admins can only see their own nudge tokens."""
        admin1_id = 12345
        admin2_id = 67890

        # Create nudge token for admin 1
        nudge_token1, _ = await nudge_token_service.create_nudge_token(
            name="Admin 1 Token",
            created_by=admin1_id,
            description="Token for admin 1 only",
        )

        # Create nudge token for admin 2
        nudge_token2, _ = await nudge_token_service.create_nudge_token(
            name="Admin 2 Token",
            created_by=admin2_id,
            description="Token for admin 2 only",
        )

        # Admin 1 lists tokens - should only see their own
        admin1_tokens = await nudge_token_service.get_nudge_tokens_by_creator(admin1_id)
        admin1_token_names = {token.name for token in admin1_tokens}

        assert "Admin 1 Token" in admin1_token_names
        assert "Admin 2 Token" not in admin1_token_names

        # Admin 2 lists tokens - should only see their own
        admin2_tokens = await nudge_token_service.get_nudge_tokens_by_creator(admin2_id)
        admin2_token_names = {token.name for token in admin2_tokens}

        assert "Admin 2 Token" in admin2_token_names
        assert "Admin 1 Token" not in admin2_token_names

    @pytest.mark.asyncio
    async def test_admin_can_deactivate_their_nudge_tokens(
        self,
        async_session: AsyncSession,
        nudge_token_service: NudgeTokenService,
    ):
        """Test that admins can deactivate their own nudge tokens."""
        admin_id = 12345

        # Create nudge token
        nudge_token, raw_token = await nudge_token_service.create_nudge_token(
            name="Token to Deactivate",
            created_by=admin_id,
            description="This token will be deactivated",
        )

        # Verify it's active
        assert nudge_token.is_active is True
        assert nudge_token.is_valid() is True

        # Deactivate the token
        success = await nudge_token_service.deactivate_nudge_token(nudge_token.id)
        assert success is True

        # Verify it's now inactive
        await async_session.refresh(nudge_token)
        assert nudge_token.is_active is False
        assert nudge_token.is_valid() is False  # Inactive tokens are not valid

    @pytest.mark.asyncio
    async def test_nudge_token_validation(
        self,
        async_session: AsyncSession,
        nudge_token_service: NudgeTokenService,
    ):
        """Test that nudge token validation works correctly."""
        admin_id = 12345

        # Create nudge token
        nudge_token, raw_token = await nudge_token_service.create_nudge_token(
            name="Validation Test Token",
            created_by=admin_id,
            description="Token for testing validation",
        )

        # Test valid token
        validated_token = await nudge_token_service.validate_nudge_token(raw_token)
        assert validated_token is not None
        assert validated_token.id == nudge_token.id
        assert validated_token.name == "Validation Test Token"

        # Test invalid token
        invalid_token = await nudge_token_service.validate_nudge_token("invalid_token")
        assert invalid_token is None

        # Test usage tracking
        await async_session.refresh(nudge_token)
        assert nudge_token.usage_count >= 1
        assert nudge_token.last_used_at is not None

    @pytest.mark.asyncio
    async def test_expired_nudge_tokens(
        self,
        async_session: AsyncSession,
        nudge_token_service: NudgeTokenService,
    ):
        """Test that expired nudge tokens can be created and identified."""
        admin_id = 12345

        # Create an already expired nudge token
        past_date = datetime.now(timezone.utc) - timedelta(days=1)
        expired_token, raw_expired = await nudge_token_service.create_nudge_token(
            name="Expired Token",
            created_by=admin_id,
            expires_at=past_date,
            description="This token is already expired",
        )

        # Verify the token has the correct expiration date
        assert expired_token.expires_at is not None
        assert expired_token.expires_at < datetime.now(timezone.utc)
        assert expired_token.is_expired() is True
        assert expired_token.is_valid() is False

        # Try to validate expired token - should fail
        validated_expired = await nudge_token_service.validate_nudge_token(raw_expired)
        assert validated_expired is None

        # Create a future expiration token
        future_date = datetime.now(timezone.utc) + timedelta(days=30)
        future_token, raw_future = await nudge_token_service.create_nudge_token(
            name="Future Token",
            created_by=admin_id,
            expires_at=future_date,
            description="This token expires in the future",
        )

        # Verify the token has the correct expiration date
        assert future_token.expires_at is not None
        assert future_token.expires_at > datetime.now(timezone.utc)
        assert future_token.is_expired() is False
        assert future_token.is_valid() is True

        # Try to validate future token - should succeed
        validated_future = await nudge_token_service.validate_nudge_token(raw_future)
        assert validated_future is not None
        assert validated_future.id == future_token.id

    @pytest.mark.asyncio
    async def test_nudge_token_usage_tracking(
        self,
        async_session: AsyncSession,
        nudge_token_service: NudgeTokenService,
    ):
        """Test that nudge token usage is tracked correctly."""
        admin_id = 12345

        # Create nudge token
        nudge_token, raw_token = await nudge_token_service.create_nudge_token(
            name="Usage Tracking Token",
            created_by=admin_id,
            description="Token for testing usage tracking",
        )

        # Verify initial usage
        assert nudge_token.usage_count == 0
        assert nudge_token.last_used_at is None

        # Validate token multiple times
        for i in range(3):
            validated_token = await nudge_token_service.validate_nudge_token(raw_token)
            assert validated_token is not None
            assert validated_token.id == nudge_token.id

        # Verify usage was updated
        await async_session.refresh(nudge_token)
        assert nudge_token.usage_count >= 3
        assert nudge_token.last_used_at is not None

    @pytest.mark.asyncio
    async def test_nudge_token_security_features(
        self,
        async_session: AsyncSession,
        nudge_token_service: NudgeTokenService,
    ):
        """Test nudge token security features."""
        admin_id = 12345

        # Create nudge token
        nudge_token, raw_token = await nudge_token_service.create_nudge_token(
            name="Security Test Token",
            created_by=admin_id,
            description="Token for testing security features",
        )

        # Verify token format
        assert raw_token.startswith("nudge_")
        assert len(raw_token) >= 32
        assert len(nudge_token.token_prefix) == 8
        assert nudge_token.token_prefix == raw_token[:8]

        # Verify the hash is different from the raw token
        assert nudge_token.token_hash != raw_token
        assert len(nudge_token.token_hash) == 64  # SHA-256 hex length

        # Verify the raw token is not stored
        # (We can only verify this by checking that the stored hash is different)
        assert nudge_token.token_hash != raw_token

        # Test token validation with correct format
        validated_token = await nudge_token_service.validate_nudge_token(raw_token)
        assert validated_token is not None
        assert validated_token.id == nudge_token.id

    @pytest.mark.asyncio
    async def test_nudge_token_statistics(
        self,
        async_session: AsyncSession,
        nudge_token_service: NudgeTokenService,
    ):
        """Test nudge token statistics functionality."""
        admin_id = 12345

        # Create multiple tokens with different states
        active_token, _ = await nudge_token_service.create_nudge_token(
            name="Active Token",
            created_by=admin_id,
            description="Active token",
        )

        inactive_token, _ = await nudge_token_service.create_nudge_token(
            name="Inactive Token",
            created_by=admin_id,
            description="Token to be deactivated",
        )
        await nudge_token_service.deactivate_nudge_token(inactive_token.id)

        expired_token, _ = await nudge_token_service.create_nudge_token(
            name="Expired Token",
            created_by=admin_id,
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
            description="Expired token",
        )

        # Get statistics
        stats = await nudge_token_service.get_token_statistics(admin_id)

        # Verify statistics
        assert stats["total_tokens"] >= 3
        assert stats["active_tokens"] >= 1
        assert stats["inactive_tokens"] >= 1
        assert stats["expired_tokens"] >= 1

        # Test token count
        active_count = await nudge_token_service.get_active_tokens_count(admin_id)
        assert active_count >= 1

    @pytest.mark.asyncio
    async def test_nudge_token_cleanup(
        self,
        async_session: AsyncSession,
        nudge_token_service: NudgeTokenService,
    ):
        """Test old nudge token cleanup functionality."""
        admin_id = 12345

        # Create an old token (simulate by creating and manually updating timestamp)
        old_token, _ = await nudge_token_service.create_nudge_token(
            name="Old Token",
            created_by=admin_id,
            description="This token should be cleaned up",
        )

        # Manually update the timestamp to make it old
        from sqlalchemy import update

        await nudge_token_service.session.execute(
            update(NudgeToken)
            .where(NudgeToken.id == old_token.id)
            .values(created_at=datetime.now(timezone.utc) - timedelta(days=95))
        )
        await nudge_token_service.session.commit()

        # Run cleanup
        deleted_count = await nudge_token_service.delete_old_tokens(days=90)
        assert deleted_count >= 1

        # Verify old token is deleted
        deleted_token = await nudge_token_service.get_nudge_token_by_id(old_token.id)
        assert deleted_token is None

    @pytest.mark.asyncio
    async def test_nudge_token_uniqueness(
        self,
        async_session: AsyncSession,
        nudge_token_service: NudgeTokenService,
    ):
        """Test that nudge tokens have unique properties."""
        admin_id = 12345

        # Create multiple tokens
        tokens = []
        raw_tokens = []
        for i in range(5):
            token, raw = await nudge_token_service.create_nudge_token(
                name=f"Unique Token {i + 1}",
                created_by=admin_id,
                description=f"Testing uniqueness {i + 1}",
            )
            tokens.append(token)
            raw_tokens.append(raw)

        # Verify all tokens are unique
        token_hashes = {token.token_hash for token in tokens}
        token_prefixes = {token.token_prefix for token in tokens}
        raw_token_set = set(raw_tokens)

        assert len(token_hashes) == 5  # All hashes should be unique
        assert len(token_prefixes) == 5  # All prefixes should be unique
        assert len(raw_token_set) == 5  # All raw tokens should be unique

        # Verify no token prefix conflicts
        for i, token in enumerate(tokens):
            # Token prefix should match raw token prefix
            assert token.token_prefix == raw_tokens[i][:8]
            # Token prefix should be unique
            assert token_prefixes == {token.token_prefix for token in tokens}
