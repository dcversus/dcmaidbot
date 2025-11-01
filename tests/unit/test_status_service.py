"""Unit tests for StatusService."""

import pytest

from services.status_service import StatusService


def test_status_service_initialization():
    """Test StatusService initializes with start time."""
    service = StatusService()
    assert service.start_time is not None


def test_get_version_info():
    """Test version info retrieval."""
    service = StatusService()
    info = service.get_version_info()

    assert "version" in info
    assert "git_commit" in info
    assert "image_tag" in info
    assert "build_time" in info
    assert "changelog" in info

    # Version should be a string
    assert isinstance(info["version"], str)
    assert len(info["version"]) > 0


def test_get_system_info():
    """Test system info retrieval."""
    service = StatusService()
    info = service.get_system_info()

    assert "current_time_utc" in info
    assert "uptime_seconds" in info
    assert "uptime_human" in info
    assert "python_version" in info
    assert "environment" in info
    assert "pod_name" in info
    assert "namespace" in info

    # Uptime should be non-negative
    assert info["uptime_seconds"] >= 0
    assert isinstance(info["uptime_seconds"], int)


@pytest.mark.asyncio
async def test_get_database_status():
    """Test database status returns not_configured when no engine."""
    service = StatusService()
    status = await service.get_database_status()

    assert "connected" in status
    assert "status" in status
    assert "message" in status

    # Should be not_configured when no database engine provided
    assert status["connected"] is False
    assert status["status"] == "not_configured"


@pytest.mark.asyncio
async def test_get_redis_status():
    """Test Redis status returns not_configured when not available."""
    service = StatusService()
    status = await service.get_redis_status()

    assert "connected" in status
    assert "status" in status
    assert "message" in status

    # Should be not_configured when Redis not available
    assert status["connected"] is False
    assert status["status"] == "not_configured"


@pytest.mark.asyncio
async def test_get_full_status():
    """Test full status aggregation."""
    service = StatusService()
    status = await service.get_full_status()

    assert "version_info" in status
    assert "system_info" in status
    assert "database" in status
    assert "redis" in status

    # Verify nested structures
    assert "version" in status["version_info"]
    assert "uptime_seconds" in status["system_info"]
    assert "connected" in status["database"]
    assert "connected" in status["redis"]


@pytest.mark.asyncio
async def test_health_status_always_healthy():
    """Test health check returns healthy when services not configured."""
    service = StatusService()
    is_healthy, details = await service.get_health_status()

    assert is_healthy is True
    assert details["status"] == "healthy"
    assert "checks" in details
    assert details["checks"]["bot"] == "ok"
    assert details["checks"]["database"] == "unavailable"
    assert details["checks"]["redis"] == "unavailable"


def test_read_version_file_returns_string():
    """Test _read_version_file returns a string."""
    service = StatusService()
    version = service._read_version_file()

    assert isinstance(version, str)
    assert len(version) > 0
    # Should be either version number or "unknown" or error
    assert version != ""


def test_read_changelog_returns_string():
    """Test _read_changelog returns a string."""
    service = StatusService()
    changelog = service._read_changelog()

    assert isinstance(changelog, str)
    # Should be either changelog content or error message
    assert len(changelog) > 0


def test_read_changelog_respects_line_limit():
    """Test _read_changelog respects line limit parameter."""
    service = StatusService()

    # Read 5 lines
    changelog_5 = service._read_changelog(lines=5)
    # Read 10 lines
    changelog_10 = service._read_changelog(lines=10)

    # If CHANGELOG.md exists and has enough lines, 10 lines should be longer
    # If it doesn't exist or has errors, both will be error messages (equal length)
    if "Changelog not available" not in changelog_5 and "Error" not in changelog_5:
        # Count newlines to verify line limit
        lines_5 = changelog_5.count("\n")
        lines_10 = changelog_10.count("\n")
        assert lines_10 >= lines_5
