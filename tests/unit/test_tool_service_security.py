"""
Comprehensive Security Tests for ToolService
=============================================

Test suite for ToolService security functionality including
URL validation, rate limiting, access control, and threat prevention.
"""

import asyncio
import os

# Import the service we're testing
import sys
import time
from unittest.mock import patch

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from services.tool_service import SecurityConfig, ThreatLevel, ToolService


class TestSecurityConfig:
    """Test suite for SecurityConfig functionality."""

    def test_default_security_config(self):
        """Test default security configuration."""
        config = SecurityConfig()

        assert config.max_requests_per_minute == 10
        assert config.max_urls_per_request == 5
        assert isinstance(config.allowed_domains, set)
        assert isinstance(config.blocked_domains, set)
        assert config.block_private_networks is True
        assert config.block_file_urls is True

    def test_custom_security_config(self):
        """Test custom security configuration."""
        allowed = ["example.com", "api.example.com"]
        blocked = ["malicious.com"]

        config = SecurityConfig(
            max_requests_per_minute=20, allowed_domains=allowed, blocked_domains=blocked
        )

        assert config.max_requests_per_minute == 20
        assert config.allowed_domains == set(allowed)
        assert config.blocked_domains == set(blocked)

    def test_domain_validation(self):
        """Test domain validation in config."""
        config = SecurityConfig()

        # Test adding valid domain
        config.add_allowed_domain("example.com")
        assert "example.com" in config.allowed_domains

        # Test adding invalid domain
        with pytest.raises(ValueError):
            config.add_allowed_domain("not a domain")

        # Test removing domain
        config.remove_allowed_domain("example.com")
        assert "example.com" not in config.allowed_domains


class TestURLValidation:
    """Test suite for URL validation security."""

    @pytest.fixture
    def tool_service(self):
        """Create ToolService with security config."""
        config = SecurityConfig()
        return ToolService(security_config=config)

    def test_validate_safe_url(self, tool_service):
        """Test validation of safe URLs."""
        safe_urls = [
            "https://example.com",
            "https://api.example.com/users",
            "https://httpbin.org/get",
            "https://jsonplaceholder.typicode.com/posts/1",
        ]

        for url in safe_urls:
            result = tool_service.validate_url(url)
            assert result["valid"] is True
            assert result["threat_level"] == ThreatLevel.SAFE

    def test_validate_blocked_domain(self, tool_service):
        """Test validation of blocked domains."""
        # Add malicious domain to block list
        tool_service.security_config.blocked_domains.add("malicious.com")

        result = tool_service.validate_url("https://malicious.com/evil")
        assert result["valid"] is False
        assert result["threat_level"] == ThreatLevel.BLOCKED
        assert "blocked domain" in result["reason"].lower()

    def test_validate_private_network(self, tool_service):
        """Test validation of private network URLs."""
        private_urls = [
            "http://localhost:3000",
            "http://127.0.0.1:8080",
            "http://192.168.1.1/admin",
            "http://10.0.0.1/api",
            "http://172.16.0.1/internal",
        ]

        for url in private_urls:
            result = tool_service.validate_url(url)
            assert result["valid"] is False
            assert result["threat_level"] == ThreatLevel.DANGEROUS

    def test_validate_file_urls(self, tool_service):
        """Test validation of file URLs."""
        file_urls = [
            "file:///etc/passwd",
            "file://C:/Windows/System32/config",
            "file:///home/user/.ssh/id_rsa",
        ]

        for url in file_urls:
            result = tool_service.validate_url(url)
            assert result["valid"] is False
            assert "file URL" in result["reason"].lower()

    def test_validate_suspicious_urls(self, tool_service):
        """Test validation of suspicious URLs."""
        suspicious_urls = [
            "https://example.com/../../etc/passwd",
            "https://example.com/?redirect=javascript:alert(1)",
            "https://example.com/<script>alert(1)</script>",
            "https://bit.ly/xyz123",  # URL shortener
            "https://tinyurl.com/abc",  # URL shortener
        ]

        for url in suspicious_urls:
            result = tool_service.validate_url(url)
            # Should either be blocked or marked as suspicious
            if result["valid"]:
                assert result["threat_level"] == ThreatLevel.SUSPICIOUS
            else:
                assert result["threat_level"] in [
                    ThreatLevel.BLOCKED,
                    ThreatLevel.DANGEROUS,
                ]

    def test_validate_invalid_urls(self, tool_service):
        """Test validation of malformed URLs."""
        invalid_urls = [
            "not-a-url",
            "ftp://example.com",  # Unsupported protocol
            "http://",
            "https://",
            "javascript:alert(1)",
            "data:text/html,<script>alert(1)</script>",
        ]

        for url in invalid_urls:
            result = tool_service.validate_url(url)
            assert result["valid"] is False
            assert "invalid" in result["reason"].lower()

    def test_validate_url_length(self, tool_service):
        """Test validation of URL length limits."""
        # Create very long URL
        long_url = "https://example.com/" + "a" * 10000

        result = tool_service.validate_url(long_url)
        assert result["valid"] is False
        assert "too long" in result["reason"].lower()

    def test_validate_domain_format(self, tool_service):
        """Test domain format validation."""
        invalid_domains = [
            "https://example..com",
            "https://.example.com",
            "https://example.com.",
            "https://exämple.com",  # Unicode in domain
            "https://example.com:8080/path",  # Non-standard port
        ]

        for url in invalid_domains:
            result = tool_service.validate_url(url)
            # Implementation dependent, but should be suspicious or blocked
            assert (
                not result["valid"] or result["threat_level"] == ThreatLevel.SUSPICIOUS
            )

    def test_validate_allowed_domain_whitelist(self, tool_service):
        """Test domain whitelist functionality."""
        # Set allowed domains
        tool_service.security_config.allowed_domains = {
            "example.com",
            "api.example.com",
        }

        # Test allowed domain
        result = tool_service.validate_url("https://example.com/path")
        assert result["valid"] is True

        # Test non-allowed domain
        result = tool_service.validate_url("https://google.com")
        assert result["valid"] is False
        assert "not in allowed list" in result["reason"].lower()

    def test_validate_url_patterns(self, tool_service):
        """Test URL pattern validation."""
        # Add blocked patterns
        tool_service.security_config.blocked_patterns = [
            r".*\.exe$",
            r".*admin.*",
            r".*\.php\?.*",
        ]

        blocked_urls = [
            "https://example.com/download.exe",
            "https://example.com/admin/panel",
            "https://example.com/script.php?cmd=ls",
        ]

        for url in blocked_urls:
            result = tool_service.validate_url(url)
            assert result["valid"] is False

    def test_validate_ip_urls(self, tool_service):
        """Test validation of IP address URLs."""
        ip_urls = ["https://8.8.8.8", "https://1.1.1.1/api", "http://0.0.0.0"]

        for url in ip_urls:
            result = tool_service.validate_url(url)
            # IP URLs should be suspicious by default
            assert result["threat_level"] == ThreatLevel.SUSPICIOUS


class TestRateLimiting:
    """Test suite for rate limiting functionality."""

    @pytest.fixture
    def tool_service(self):
        """Create ToolService with strict rate limiting."""
        config = SecurityConfig(max_requests_per_minute=2)
        return ToolService(security_config=config)

    @pytest.mark.asyncio
    async def test_rate_limiting_normal_usage(self, tool_service):
        """Test normal usage within rate limits."""
        user_id = 123

        # First request should succeed
        result1 = await tool_service.check_rate_limit(user_id)
        assert result1["allowed"] is True
        assert result1["remaining"] == 1

        # Second request should succeed
        result2 = await tool_service.check_rate_limit(user_id)
        assert result2["allowed"] is True
        assert result2["remaining"] == 0

    @pytest.mark.asyncio
    async def test_rate_limiting_exceeded(self, tool_service):
        """Test rate limit exceeded."""
        user_id = 123

        # Exhaust rate limit
        await tool_service.check_rate_limit(user_id)
        await tool_service.check_rate_limit(user_id)

        # Third request should be blocked
        result = await tool_service.check_rate_limit(user_id)
        assert result["allowed"] is False
        assert "rate limit" in result["reason"].lower()

    @pytest.mark.asyncio
    async def test_rate_limiting_reset(self, tool_service):
        """Test rate limit reset after time window."""
        user_id = 123

        # Exhaust rate limit
        await tool_service.check_rate_limit(user_id)
        await tool_service.check_rate_limit(user_id)

        # Should be blocked
        result = await tool_service.check_rate_limit(user_id)
        assert result["allowed"] is False

        # Mock time passage (more than 1 minute)
        with patch("time.time", return_value=time.time() + 61):
            result = await tool_service.check_rate_limit(user_id)
            assert result["allowed"] is True

    @pytest.mark.asyncio
    async def test_rate_limiting_per_user(self, tool_service):
        """Test rate limiting is per-user."""
        user1 = 123
        user2 = 456

        # User 1 exhausts limit
        await tool_service.check_rate_limit(user1)
        await tool_service.check_rate_limit(user1)

        # User 1 should be blocked
        result1 = await tool_service.check_rate_limit(user1)
        assert result1["allowed"] is False

        # User 2 should still have full quota
        result2 = await tool_service.check_rate_limit(user2)
        assert result2["allowed"] is True

    @pytest.mark.asyncio
    async def test_rate_limiting_bypass_admin(self, tool_service):
        """Test admin bypass of rate limits."""
        admin_id = 999  # Assuming admin ID

        # Admin should not be rate limited
        for _ in range(10):
            result = await tool_service.check_rate_limit(admin_id, is_admin=True)
            assert result["allowed"] is True

    @pytest.mark.asyncio
    async def test_rate_limiting_memory_cleanup(self, tool_service):
        """Test cleanup of old rate limit data."""
        user_id = 123

        # Use rate limit
        await tool_service.check_rate_limit(user_id)

        # Should have entry in rate limit map
        assert user_id in tool_service.rate_limits

        # Mock time passage and cleanup
        with patch("time.time", return_value=time.time() + 3610):  # 1 hour + 10 seconds
            tool_service.cleanup_rate_limits()
            assert user_id not in tool_service.rate_limits


class TestAccessControl:
    """Test suite for access control functionality."""

    @pytest.fixture
    def tool_service(self):
        """Create ToolService with access control."""
        config = SecurityConfig(
            require_admin_for_sensitive=True, admin_user_ids={999, 1000}
        )
        return ToolService(security_config=config)

    def test_is_admin_check(self, tool_service):
        """Test admin user verification."""
        assert tool_service.is_admin(999) is True
        assert tool_service.is_admin(1000) is True
        assert tool_service.is_admin(123) is False
        assert tool_service.is_admin(0) is False

    def test_sensitive_operation_access(self, tool_service):
        """Test access to sensitive operations."""
        # Admin should have access
        assert tool_service.can_access_sensitive(999, "curl") is True

        # Regular user should not
        assert tool_service.can_access_sensitive(123, "curl") is False

        # Non-sensitive operation should be allowed
        assert tool_service.can_access_sensitive(123, "search") is True

    def test_dynamic_admin_update(self, tool_service):
        """Test dynamic admin list updates."""
        # Add new admin
        tool_service.add_admin(777)
        assert tool_service.is_admin(777) is True

        # Remove admin
        tool_service.remove_admin(777)
        assert tool_service.is_admin(777) is False

    def test_permission_levels(self, tool_service):
        """Test different permission levels."""
        # Define permission levels
        permissions = {
            "search": 0,  # Everyone
            "news": 1,  # Regular users
            "curl": 2,  # Admins only
            "eval": 3,  # Super admins only
        }

        tool_service.security_config.permission_levels = permissions
        tool_service.security_config.super_admins = {1000}

        # Test different user levels
        assert tool_service.check_permission(123, "search") is True  # Everyone
        assert tool_service.check_permission(123, "news") is True  # Regular user
        assert tool_service.check_permission(123, "curl") is False  # Admin only

        assert tool_service.check_permission(999, "curl") is True  # Admin
        assert tool_service.check_permission(999, "eval") is False  # Super admin only

        assert tool_service.check_permission(1000, "eval") is True  # Super admin


class TestThreatDetection:
    """Test suite for threat detection functionality."""

    @pytest.fixture
    def tool_service(self):
        """Create ToolService with threat detection."""
        return ToolService()

    def test_detect_sql_injection(self, tool_service):
        """Test SQL injection detection."""
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "1; DELETE FROM users WHERE 1=1; --",
            "' UNION SELECT * FROM passwords --",
        ]

        for input_str in malicious_inputs:
            threat = tool_service.detect_threats(input_str)
            assert threat["detected"] is True
            assert "sql injection" in threat["threat_type"].lower()

    def test_detect_xss(self, tool_service):
        """Test XSS detection."""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert(1)",
            "<img src=x onerror=alert(1)>",
            "';alert('xss');//",
        ]

        for payload in xss_payloads:
            threat = tool_service.detect_threats(payload)
            assert threat["detected"] is True
            assert "xss" in threat["threat_type"].lower()

    def test_detect_command_injection(self, tool_service):
        """Test command injection detection."""
        command_injections = [
            "; ls -la",
            "| cat /etc/passwd",
            "`rm -rf /`",
            "$(whoami)",
        ]

        for injection in command_injections:
            threat = tool_service.detect_threats(injection)
            assert threat["detected"] is True
            assert "command injection" in threat["threat_type"].lower()

    def test_detect_path_traversal(self, tool_service):
        """Test path traversal detection."""
        path_traversals = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config",
            "....//....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
        ]

        for traversal in path_traversals:
            threat = tool_service.detect_threats(traversal)
            assert threat["detected"] is True
            assert "path traversal" in threat["threat_type"].lower()

    def test_log_threat_attempt(self, tool_service):
        """Test threat attempt logging."""
        threat_info = {
            "user_id": 123,
            "threat_type": "SQL Injection",
            "input": "'; DROP TABLE users; --",
            "ip_address": "192.168.1.1",
            "timestamp": time.time(),
        }

        # Should not raise exception
        tool_service.log_threat_attempt(threat_info)

        # Check if threat was logged
        assert len(tool_service.threat_log) > 0
        logged_threat = tool_service.threat_log[-1]
        assert logged_threat["user_id"] == 123
        assert logged_threat["threat_type"] == "SQL Injection"

    def test_threat_score_calculation(self, tool_service):
        """Test threat score calculation."""
        # Multiple threats from same user
        user_id = 123
        threats = [
            {"threat_type": "SQL Injection", "severity": 10},
            {"threat_type": "XSS", "severity": 8},
            {"threat_type": "Command Injection", "severity": 9},
        ]

        for threat in threats:
            tool_service.log_threat_attempt(
                {
                    "user_id": user_id,
                    "threat_type": threat["threat_type"],
                    "severity": threat["severity"],
                }
            )

        score = tool_service.calculate_threat_score(user_id)
        assert score > 0
        assert score >= sum(t["severity"] for t in threats)

    def test_auto_ban_high_threat_users(self, tool_service):
        """Test automatic banning of high threat users."""
        user_id = 123

        # Generate many threats
        for i in range(10):
            tool_service.log_threat_attempt(
                {"user_id": user_id, "threat_type": "SQL Injection", "severity": 10}
            )

        # Should auto-ban
        assert tool_service.should_ban_user(user_id) is True
        assert user_id in tool_service.banned_users

    def test_ban_expiry(self, tool_service):
        """Test ban expiry functionality."""
        user_id = 123
        ban_duration = 3600  # 1 hour

        # Ban user
        tool_service.ban_user(user_id, duration=ban_duration)
        assert tool_service.is_banned(user_id) is True

        # Mock time passage beyond ban duration
        with patch("time.time", return_value=time.time() + ban_duration + 1):
            assert tool_service.is_banned(user_id) is False

    def test_ip_reputation_check(self, tool_service):
        """Test IP reputation checking."""
        # Known malicious IP
        malicious_ip = "192.168.1.100"
        tool_service.blocked_ips.add(malicious_ip)

        assert tool_service.is_ip_blocked(malicious_ip) is True
        assert tool_service.is_ip_blocked("192.168.1.1") is False

    def test_concurrent_threat_detection(self, tool_service):
        """Test concurrent threat detection."""
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "<script>alert(1)</script>",
            "; rm -rf /",
            "../../../etc/passwd",
        ]

        # Detect threats concurrently
        tasks = [
            asyncio.create_task(
                asyncio.to_thread(tool_service.detect_threats, input_str)
            )
            for input_str in malicious_inputs
        ]

        results = asyncio.run(tasks)

        # All should detect threats
        for result in results:
            assert result["detected"] is True


class TestSecurityIntegration:
    """Integration tests for security features."""

    @pytest.mark.asyncio
    async def test_web_search_security_flow(self, tool_service):
        """Test security in web search flow."""
        user_id = 123
        malicious_query = "'; DROP TABLE users; --"

        # Should detect threat
        threat = tool_service.detect_threats(malicious_query)
        assert threat["detected"] is True

        # Search should be blocked
        result = await tool_service.web_search(user_id, malicious_query)
        assert result["success"] is False
        assert "security" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_curl_request_security_flow(self, tool_service):
        """Test security in curl request flow."""
        user_id = 123
        malicious_url = "file:///etc/passwd"

        # URL validation should block
        url_result = tool_service.validate_url(malicious_url)
        assert url_result["valid"] is False

        # Curl should be blocked
        result = await tool_service.curl_request(user_id, malicious_url)
        assert result["success"] is False
        assert "blocked" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_admin_security_bypass(self, tool_service):
        """Test admin security bypass for trusted operations."""
        admin_id = 999
        tool_service.add_admin(admin_id)

        # Admin should be able to access internal URLs if configured
        tool_service.security_config.allow_admin_internal = True

        # Should succeed if admin bypass is enabled
        # (Implementation dependent on actual curl_request method)

    @pytest.mark.asyncio
    async def test_comprehensive_security_check(self, tool_service):
        """Test comprehensive security validation."""
        user_id = 123
        operation = {
            "type": "curl",
            "url": "https://malicious.com/evil",
            "user_agent": "Bot/1.0",
            "headers": {"Authorization": "Bearer secret"},
        }

        # Run comprehensive security check
        security_result = await tool_service.comprehensive_security_check(
            user_id, operation
        )

        assert "allowed" in security_result
        assert "threats" in security_result
        assert "recommendations" in security_result

        # Should block malicious operation
        assert security_result["allowed"] is False
        assert len(security_result["threats"]) > 0

    @pytest.mark.asyncio
    async def test_security_monitoring(self, tool_service):
        """Test security monitoring and alerting."""
        # Generate various security events
        events = [
            {"type": "sql_injection", "user_id": 123},
            {"type": "xss", "user_id": 456},
            {"type": "rate_limit", "user_id": 789},
            {"type": "blocked_url", "user_id": 101},
        ]

        for event in events:
            tool_service.log_security_event(event)

        # Get security report
        report = tool_service.generate_security_report()

        assert "total_events" in report
        assert "events_by_type" in report
        assert "top_offenders" in report
        assert "recommendations" in report

        assert report["total_events"] == len(events)
        assert len(report["events_by_type"]) > 0
