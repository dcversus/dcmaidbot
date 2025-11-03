# Self-Check Tool

## Overview
The Self-Check Tool provides comprehensive system diagnostics through Lilith's honest analysis. This tool allows users to trigger self-check thoughts generation and view system health assessments.

## Business Value
- **System Health Monitoring**: Real-time assessment of all system components
- **Transparent Diagnostics**: Honest opinions about system status and performance
- **Proactive Issue Detection**: Early identification of potential problems
- **User Confidence**: Clear communication about system reliability

## Configuration
No additional configuration required. Uses the enhanced status service and background scheduler.

## Usage Examples

### Manual Self-Check via /call
```bash
/call self_check
```

**Response:**
```
🔍 Running self-check diagnostics...

📊 **Self-Check Results:**
✅ Webhook Endpoint: Operational (200 OK)
✅ Database Connection: Stable
✅ Redis Cache: Performing well
✅ Telegram Bot API: Accessible
✅ Crypto Service: Generating insights

💭 **Lilith's Honest Opinion:**
"All my systems are running smoothly today! I'm feeling confident about our infrastructure. The webhook responded quickly and the database is stable. Though I did notice the crypto service took a bit longer than usual - but that's normal with market volatility!"

⏱️ **Diagnostics completed in 2.3 seconds**
🎯 **Overall System Health: 95%**
```

### Scheduled Self-Check
- **Frequency**: Every 24 hours (automatic)
- **Time**: Typically at midnight UTC
- **Storage**: Results stored in database for historical tracking

### Self-Check via Telegram
```
/selfcheck
```

## Tool Integration

### Tool Registration
The self-check tool is automatically registered with the tool system and accessible through:

1. **Call Command**: `/call self_check`
2. **Telegram Command**: `/selfcheck`
3. **API Access**: Through authenticated `/status` endpoint
4. **Manual Trigger**: Admin interface access

### Tool Metadata
```json
{
  "name": "self_check",
  "description": "Run comprehensive system diagnostics",
  "category": "system",
  "permissions": ["status:read"],
  "parameters": {
    "force": {
      "type": "boolean",
      "default": false,
      "description": "Force fresh diagnostics bypassing cache"
    },
    "verbose": {
      "type": "boolean",
      "default": false,
      "description": "Include detailed tool-by-tool results"
    }
  }
}
```

## Self-Check Process

### Diagnostic Sequence
1. **Webhook Endpoint Test**
   - Tests: `/webhook` endpoint accessibility
   - Expectation: 200 OK response
   - Fallback: Tests `/status` then external connectivity

2. **Database Connection Test**
   - Tests: PostgreSQL database connectivity
   - Expectation: Successful query execution
   - Metrics: Connection response time, query performance

3. **Redis Cache Test**
   - Tests: Redis read/write operations
   - Expectation: Successful cache operations
   - Metrics: Cache hit rates, response times

4. **Telegram Bot API Test**
   - Tests: Bot API accessibility and token validity
   - Expectation: Successful bot info retrieval
   - Metrics: API response time, token status

5. **Crypto Service Test**
   - Tests: Crypto thoughts generation capability
   - Expectation: Successful insight generation
   - Metrics: API response times, content quality

### Evaluation Criteria
- **Confidence Score**: 0-10 rating for each component
- **Response Time**: Measured in milliseconds
- **Success Rate**: Percentage of successful operations
- **Health Status**: operational/degraded/failing

## API Integration

### Manual Trigger
```python
# Trigger immediate self-check
from services.thoughts_background_service import thoughts_background_service

result = await thoughts_background_service._generate_self_check_thoughts_now()
print(f"Self-check completed: {result['success']}")
```

### Scheduled Results
```python
# Get latest self-check results
thoughts = thoughts_background_service.get_stored_thoughts()
self_check = thoughts['self_check_thoughts']

if self_check['available']:
    print(f"Last check: {self_check['last_updated']}")
    print(f"Health score: {self_check['confidence_score']}/10")
```

## Error Handling

### Common Scenarios

**Network Connectivity Issues**
- Symptom: External service timeouts
- Resolution: Test local connectivity first, then external
- Lilith's Opinion: "I'm having trouble reaching some external services, but our internal systems are fine!"

**Database Connection Problems**
- Symptom: Query failures or connection timeouts
- Resolution: Check database server status and connection strings
- Lilith's Opinion: "The database seems sleepy today... I hope it wakes up soon!"

**Service Dependencies**
- Symptom: Related services not responding
- Resolution: Check service dependencies and restart if needed
- Lilith's Opinion: "Some of my friends aren't responding... I hope they're okay!"

### Fallback Behavior
- **Partial Failures**: Continue with available components
- **Complete Failures**: Return cached results if available
- **Graceful Degradation**: Provide partial information rather than complete failure

## Performance Metrics

### Target Performance
- **Total Execution Time**: < 5 seconds
- **Individual Tool Tests**: < 1 second each
- **Memory Usage**: < 50MB during execution
- **CPU Usage**: < 10% during diagnostics

### Monitoring Metrics
```json
{
  "self_check_metrics": {
    "execution_time": 2.3,
    "tools_tested": 5,
    "tools_passed": 5,
    "tools_failed": 0,
    "average_response_time": 460,
    "memory_usage_mb": 23,
    "cpu_usage_percent": 6.5,
    "last_execution": "2025-11-03T01:00:00.000Z"
  }
}
```

## Historical Tracking

### Data Storage
Each self-check execution stores:
- **Timestamp**: When the check was performed
- **Results**: Individual tool test results
- **Opinions**: Lilith's honest assessment
- **Metrics**: Performance and timing data
- **Issues**: Identified problems and resolutions

### Trend Analysis
- **Health Trends**: Track system health over time
- **Performance Patterns**: Identify recurring issues
- **Improvement Areas**: Components needing attention
- **Success Rates**: Overall system reliability metrics

## Troubleshooting

### Self-Check Failures

**Self-Check Service Unavailable**
```bash
# Check background service status
curl -H "X-API-Key: YOUR_KEY" https://your-domain.com/status | jq '.self_check_thoughts.available'
```

**Individual Tool Failures**
- Check service logs for specific error messages
- Verify service configuration and connectivity
- Test manual service access if needed

**Performance Degradation**
- Monitor system resource usage
- Check for external service latency
- Review recent configuration changes

### Debug Commands
```bash
# Force fresh self-check (bypassing cache)
/call self_check force=true verbose=true

# Check last self-check results
curl -H "X-API-Key: YOUR_KEY" https://your-domain.com/status | jq '.self_check_thoughts'

# View self-check scheduling
curl -H "X-API-Key: YOUR_KEY" https://your-domain.com/status | jq '.admin_llm_context.last_self_check'
```

## Best Practices

### For Users
1. **Regular Monitoring**: Check self-check results daily
2. **Issue Reporting**: Report consistent failures to administrators
3. **Performance Awareness**: Understand normal system behavior patterns
4. **Documentation**: Keep records of recurring issues

### For Administrators
1. **Scheduled Reviews**: Weekly review of self-check trends
2. **Proactive Maintenance**: Address issues before they impact users
3. **Performance Optimization**: Monitor and optimize slow components
4. **Alert Configuration**: Set up alerts for critical failures

## Security Considerations

### Access Control
- **Read Access**: Available to all authenticated users
- **Manual Trigger**: Requires appropriate permissions
- **Sensitive Data**: Internal system details only visible to admins
- **Audit Trail**: All manual triggers logged for security review

### Data Protection
- **System Information**: Limited to operational status
- **No Credentials**: Never exposes passwords or API keys
- **Network Details**: Internal network topology not revealed
- **User Privacy**: No user data included in diagnostics

## Future Enhancements

### Planned Features
1. **Advanced Analytics**: Predictive failure analysis
2. **Custom Thresholds**: Configurable warning and alert levels
3. **Integration Testing**: Test external service integrations
4. **Performance Baselines**: Automatic baseline establishment
5. **Automated Remediation**: Self-healing capabilities for common issues

### Monitoring Improvements
1. **Real-time Dashboards**: Visual self-check status display
2. **Mobile Notifications**: Immediate alerts for critical issues
3. **Historical Reporting**: Monthly health reports and summaries
4. **Integration Metrics**: Track external service performance trends
5. **Capacity Planning**: Resource usage forecasting and recommendations
