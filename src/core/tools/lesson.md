# Tool Name Documentation

## Overview
[Tool description goes here]

## Available Tools

[List of available tools goes here]

## Usage Examples

[Usage examples go here]

## Integration Notes

[Integration notes go here]

## Rate Limits & Restrictions

[Rate limits information goes here]

## Error Handling

All tools return standardized error responses:
- Success: Result data as specified in tool description
- Permission denied: `{"error": "Access denied", "message": "Insufficient permissions"}`
- Rate limited: `{"error": "Rate limited", "message": "Too many requests"}`
- Invalid parameters: `{"error": "Invalid parameters", "message": "Specific error details"}`

## Testing

Tools are automatically tested by the validation system:
- Unit tests verify individual tool functionality
- E2E tests verify integration with the bot system
- LLM judge validation ensures proper tool responses

---

*This documentation was auto-generated on 2025-11-02. Please review and enhance with additional details and real-world examples.*
