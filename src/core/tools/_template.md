# Tool Name Documentation

## Overview
[Brief description of what this tool module does and its main purpose in the DCMaidBot system]

## Business Value
[Why this tool matters to users and the overall system. What problems does it solve?]

## Available Tools

[List of available tools will be auto-generated here]

## Usage Examples

[Examples will be auto-generated here]

## Integration Notes

[Integration notes will be auto-generated here]

## Rate Limits & Restrictions

[Rate limits will be auto-generated here]

## Error Handling

All tools return standardized error responses:
- Success: Result data as specified in tool description
- Permission denied: `{"error": "Access denied", "message": "Insufficient permissions"}`
- Rate limited: `{"error": "Rate limited", "message": "Too many requests"}`
- Invalid parameters: `{"error": "Invalid parameters", "message": "Specific error details"}`

## Security Considerations
- [Any security considerations for this tool]
- [Access control requirements]
- [Data handling procedures]

## Troubleshooting
[Common issues and solutions]

## Testing
Tools are automatically tested by the validation system:
- Unit tests verify individual tool functionality
- E2E tests verify integration with the bot system
- LLM judge validation ensures proper tool responses

## Maintenance
- [How to maintain this tool]
- [What to check when making changes]
- [Testing requirements]

---

*This documentation was auto-generated. Please review and enhance with additional details and real-world examples.*
