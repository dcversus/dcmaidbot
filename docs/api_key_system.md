# API Key System Documentation

## Overview

The dcmaidbot API key system provides secure admin access to enhanced endpoints with granular permissions, usage tracking, and rate limiting. This system allows administrators to access sensitive data and administrative functions through API authentication.

## Features

- **Secure Key Generation**: Cryptographically secure random API keys
- **Permission-Based Access**: Granular permissions for different admin functions
- **Usage Tracking**: Monitor API key usage and access patterns
- **Rate Limiting**: Prevent abuse with configurable rate limits
- **Key Expiration**: Automatic key expiration with configurable periods
- **Key Revocation**: Immediate revocation of compromised keys
- **Admin Commands**: Bot commands for key management
- **Audit Trail**: Complete logging of key usage

## API Key Format

```
dcb_<random_string>
```

Example: `dcb_7K9m2X8pQ5rJ3vN6wL4zY1sF9cB8eA`

- Prefix: `dcb_` (dcmaidbot)
- Length: 32 characters total (including prefix)
- Encoding: URL-safe base64
- Entropy: Cryptographically secure

## Available Permissions

| Permission | Description | Endpoints |
|------------|-------------|-----------|
| `status:read` | Read comprehensive status including thoughts | `/status` (authenticated) |
| `interactions:read` | Read admin interactions and logs | `/status` (authenticated) |
| `context:read` | Read admin LLM context data | `/status` (authenticated) |
| `keys:manage` | Generate and manage API keys | Bot commands |
| `admin:full` | Full admin access (includes all permissions) | All endpoints |

## Authentication Methods

### Method 1: Header Authentication
```bash
curl -H "X-API-Key: dcb_7K9m2X8pQ5rJ3vN6wL4zY1sF9cB8eA" \
     https://your-domain.com/status
```

### Method 2: Query Parameter Authentication
```bash
curl "https://your-domain.com/status?api_key=dcb_7K9m2X8pQ5rJ3vN6wL4zY1sF9cB8eA"
```

## Endpoints

### Universal Status Endpoint: `/status`

**Public Access (No API Key)**
Returns basic system status information:

```json
{
  "version": "v2.1.0-enhanced-status-abc123",
  "commit": "abc123d",
  "uptime": "24h 35m",
  "redis": "operational",
  "postgresql": "operational",
  "bot": "online",
  "image_tag": "dcmaidbot:latest",
  "build_time": "2025-11-02T12:00:00Z",
  "timestamp": "2025-11-03T01:00:00.000Z"
}
```

**Authenticated Access (With Valid API Key)**
Returns comprehensive admin status including:

```json
{
  "versiontxt": "v2.1.0-enhanced-status-abc123",
  "version": "v2.1.0",
  "commit": "abc123def456",
  "uptime": 88500.0,
  "start_time": "2025-11-02T00:00:00.000Z",

  "version_thoughts": {
    "available": true,
    "lilith_opinion": "I'm excited about the new features!",
    "generation_time": 1.2,
    "tokens_used": 150,
    "last_updated": "2025-11-03T01:00:00.000Z"
  },

  "self_check_thoughts": {
    "available": true,
    "lilith_honest_opinion": "All systems are running smoothly!",
    "total_time": 2.5,
    "tokens_used": 200,
    "last_updated": "2025-11-03T01:00:00.000Z"
  },

  "crypto_thoughts": {
    "available": true,
    "market_analysis": "Bitcoin is showing strong momentum...",
    "generation_time": 0.8,
    "tokens_used": 120,
    "last_updated": "2025-11-03T01:00:00.000Z"
  },

  "admin_llm_context": {
    "current_context": "Active conversation with user",
    "recent_prompts": ["What's the status?", "Tell me a joke"],
    "token_usage_today": 470,
    "last_llm_interaction": "2025-11-03T00:55:00.000Z",
    "context_size": 2048,
    "active_sessions": 3
  },

  "admin_interactions": {
    "interactions": [
      {
        "id": 12345,
        "user_id": 987654,
        "username": "admin_user",
        "message": "/status",
        "response": "System status: All operational",
        "timestamp": "2025-11-03T00:55:00.000Z",
        "interaction_type": "command",
        "tokens_used": 25
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 50,
      "total": 1250,
      "total_pages": 25,
      "has_next": true,
      "has_prev": false
    },
    "filters": {
      "date_from": null,
      "date_to": null,
      "user_id": null,
      "interaction_type": null
    }
  },

  "api_key_info": {
    "key_id": "7K9m2X8pQ5rJ3vN6",
    "description": "Admin API key for monitoring",
    "permissions": ["status:read", "interactions:read", "context:read"],
    "last_used_at": "2025-11-03T00:55:00.000Z",
    "usage_count": 42
  },

  "tokens_total": 470,
  "tokens_uptime": 0.0053,

  "timestamp": "2025-11-03T01:00:00.000Z"
}
```

### Pagination Support

Authenticated `/status` endpoint supports pagination for interactions:

- `page`: Page number (default: 1)
- `per_page`: Items per page, max 100 (default: 50)

Example:
```bash
curl -H "X-API-Key: dcb_7K9m2X8pQ5rJ3vN6wL4zY1sF9cB8eA" \
     "https://your-domain.com/status?page=2&per_page=25"
```

## Bot Commands for API Key Management

### Generate API Key
```
/generate_api_key [description]
```

**Example:**
```
/generate_api_key "Monitoring dashboard key"
```

**Response:**
```
🔑 API key generated successfully!

🔑 Your API Key:
dcb_7K9m2X8pQ5rJ3vN6wL4zY1sF9cB8eA

📝 Description: Monitoring dashboard key
🔐 Permissions: status:read, interactions:read, context:read
⏰ Expires: 2026-11-03T01:00:00.000Z

📚 How to use your API key:

Method 1 - Header:
curl -H "X-API-Key: dcb_7K9m2X8pQ5rJ3vN6wL4zY1sF9cB8eA" https://your-domain.com/status

Method 2 - Query Parameter:
curl "https://your-domain.com/status?api_key=dcb_7K9m2X8pQ5rJ3vN6wL4zY1sF9cB8eA"

⚠️ Keep this key secure! It provides admin access to your bot.
```

### List API Keys
```
/list_api_keys
```

**Response:**
```
🔑 You have 2 API key(s):

🔑 Key 1: `7K9m2X8pQ5rJ3vN6...`
📝 Description: Monitoring dashboard key
🔐 Permissions: status:read, interactions:read, context:read
📊 Usage: 42 times
📅 Created: 2025-11-01
⏰ Expires: 2026-11-01
📈 Status: ✅ Active

🔑 Key 2: `3W9m1K6pL8rN4vN...`
📝 Description: Backup admin key
🔐 Permissions: admin:full
📊 Usage: 5 times
📅 Created: 2025-10-28
⏰ Expires: 2025-10-28
📈 Status: ❌ Inactive

📊 Summary: 2 total, 1 active, 1 expired, 47 total uses
```

### Revoke API Key
```
/revoke_api_key <key_id>
```

**Example:**
```
/revoke_api_key 7K9m2X8pQ5rJ3vN6
```

**Response:**
```
🔑 API key 7K9m2X8pQ5rJ3vN6... has been revoked successfully.
The key can no longer be used to access admin endpoints.
```

### API Key Statistics
```
/api_key_stats
```

**Response:**
```
📊 Your API key statistics:

📈 Usage Summary:
• Total Keys: 2
• Active Keys: 1
• Expired Keys: 1
• Total Usage: 47 requests
• Last Used: 2025-11-03T00:55:00.000Z

💡 Tip: Use /list_api_keys to see detailed information about each key.
```

## Rate Limiting

- **Default Limit**: 1000 requests per hour per API key
- **Rate Limit Headers**: Included in response when approaching limits
- **Rate Limit Response**: HTTP 429 with retry-after header

**Rate Limit Response:**
```json
{
  "error": "Rate limit exceeded",
  "message": "Too many requests. Try again later.",
  "retry_after": 3600,
  "limit": 1000,
  "remaining": 0,
  "reset_time": "2025-11-03T02:00:00.000Z"
}
```

## Error Handling

### Authentication Errors

**Invalid Key Format:**
```json
{
  "error": "Failed to retrieve status",
  "message": "Invalid key format",
  "timestamp": "2025-11-03T01:00:00.000Z"
}
```

**Key Not Found:**
```json
{
  "error": "Failed to retrieve status",
  "message": "Key not found",
  "timestamp": "2025-11-03T01:00:00.000Z"
}
```

**Key Expired:**
```json
{
  "error": "Failed to retrieve status",
  "message": "Key has expired",
  "timestamp": "2025-11-03T01:00:00.000Z"
}
```

**Permission Denied:**
```json
{
  "error": "Failed to retrieve status",
  "message": "Permission 'status:read' not granted",
  "timestamp": "2025-11-03T01:00:00.000Z"
}
```

## Security Considerations

### Key Storage
- **Server Storage**: Keys are hashed using SHA-256 before storage
- **Client Storage**: Store keys securely (environment variables, secure vaults)
- **Transmission**: Always use HTTPS to prevent key interception

### Best Practices
1. **Principle of Least Privilege**: Grant only necessary permissions
2. **Regular Rotation**: Rotate keys periodically (recommended: every 90 days)
3. **Monitor Usage**: Regularly review key usage patterns
4. **Immediate Revocation**: Revoke keys immediately when compromised
5. **Secure Storage**: Never commit keys to version control
6. **Access Logs**: Monitor API access logs for suspicious activity

### Key Compromise Response
1. **Immediate Revocation**: Use `/revoke_api_key` to disable compromised key
2. **Audit Logs**: Review access logs for unauthorized usage
3. **Generate New Key**: Create new key with different permissions if needed
4. **Update Integrations**: Update all systems using the compromised key
5. **Monitor Activity**: Watch for continued access attempts

## Configuration

### Environment Variables
```bash
# Admin user IDs (comma-separated)
ADMIN_IDS=123456789,987654321

# API Key Settings
API_KEY_DEFAULT_EXPIRATION_DAYS=365
API_KEY_RATE_LIMIT_PER_HOUR=1000
API_KEY_PREFIX=dcb_
```

### Database Schema (Future Implementation)

```sql
-- API Keys table
CREATE TABLE api_keys (
    id SERIAL PRIMARY KEY,
    key_hash VARCHAR(64) UNIQUE NOT NULL,
    user_id BIGINT NOT NULL,
    description TEXT,
    permissions TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    last_used_at TIMESTAMP WITH TIME ZONE,
    usage_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    revoked_at TIMESTAMP WITH TIME ZONE
);

-- API Usage tracking
CREATE TABLE api_usage (
    id SERIAL PRIMARY KEY,
    key_hash VARCHAR(64) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    endpoint VARCHAR(255) NOT NULL,
    user_agent TEXT,
    ip_address INET
);
```

## Integration Examples

### Python
```python
import requests

# Public status
response = requests.get("https://your-domain.com/status")
public_data = response.json()

# Authenticated status
headers = {"X-API-Key": "dcb_7K9m2X8pQ5rJ3vN6wL4zY1sF9cB8eA"}
response = requests.get("https://your-domain.com/status", headers=headers)
admin_data = response.json()
```

### JavaScript
```javascript
// Public status
const publicResponse = await fetch('https://your-domain.com/status');
const publicData = await publicResponse.json();

// Authenticated status
const adminResponse = await fetch('https://your-domain.com/status', {
  headers: {
    'X-API-Key': 'dcb_7K9m2X8pQ5rJ3vN6wL4zY1sF9cB8eA'
  }
});
const adminData = await adminResponse.json();
```

### Shell Script
```bash
#!/bin/bash

API_KEY="dcb_7K9m2X8pQ5rJ3vN6wL4zY1sF9cB8eA"
API_URL="https://your-domain.com/status"

# Get admin status
curl -H "X-API-Key: $API_KEY" "$API_URL" | jq '.version_thoughts.lilith_opinion'
```

## Troubleshooting

### Common Issues

1. **"Invalid key format"**
   - Ensure key starts with `dcb_`
   - Check for extra spaces or characters

2. **"Key not found"**
   - Verify key was generated correctly
   - Check if key was revoked

3. **"Key has expired"**
   - Generate new key with longer expiration
   - Check key expiration date

4. **"Permission not granted"**
   - Verify key has required permissions
   - Regenerate key with correct permissions

5. **"Rate limit exceeded"**
   - Wait for rate limit to reset
   - Consider increasing rate limit for high-usage keys

### Debug Commands

```bash
# Test key validity
curl -H "X-API-Key: YOUR_KEY" "https://your-domain.com/status" | jq '.error'

# Check rate limits
curl -I -H "X-API-Key: YOUR_KEY" "https://your-domain.com/status"

# Test specific permissions
curl -H "X-API-Key: YOUR_KEY" "https://your-domain.com/status?api_key=YOUR_KEY"
```

## Monitoring and Logging

### Log Formats

**API Access Log:**
```
2025-11-03T01:00:00Z INFO API_ACCESS key_id=7K9m2X8p user_id=123456 endpoint=/status status=200 duration=45ms
```

**Key Generation Log:**
```
2025-11-03T01:00:00Z INFO KEY_GENERATED user_id=123456 description="Dashboard key" permissions=status:read,interactions:read
```

**Security Events:**
```
2025-11-03T01:00:00Z WARN AUTH_FAILED key=invalid_key reason="Key not found" ip=192.168.1.100
2025-11-03T01:00:00Z WARN RATE_LIMIT_EXCEEDED key_id=7K9m2X8p usage=1001 limit=1000
```

### Metrics to Monitor

- API key creation and revocation rates
- Authentication success/failure rates
- Rate limit violations
- Permission denied errors
- Token usage patterns
- Geographic access patterns
- Unusual usage spikes

## Future Enhancements

1. **Time-Restricted Keys**: Keys that only work during specific hours
2. **IP-Whitelisting**: Restrict keys to specific IP addresses
3. **Temporary Keys**: Short-lived keys for specific tasks
4. **Key Groups**: Manage multiple keys as a group
5. **Webhook Notifications**: Alerts for key usage and security events
6. **Advanced Analytics**: Detailed usage analytics and reporting
7. **Multi-Factor Authentication**: Additional security for sensitive operations
8. **Key Rotation Automation**: Automatic key rotation policies
