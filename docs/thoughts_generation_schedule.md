# Thoughts Generation Schedule

## Overview

This document defines when and how different types of thoughts are generated in the dcmaidbot system. Thoughts generation is handled by background tasks to ensure fast API responses and proper timing data collection.

## Thought Types and Generation Triggers

### 1. Version Thoughts
**Purpose**: Lilith's thoughts and opinions about new system versions

**When Generated**:
- **On version change**: When the system detects a different version in `/version.txt` compared to the database
- **On system startup**: First time the system starts with a new version
- **Manual trigger**: Via admin command or API call (future feature)

**Trigger Logic**:
```python
# Pseudo-code for version change detection
current_version = read_version_file("version.txt")
stored_version = get_version_from_database()

if current_version != stored_version:
    await thoughts_background_service.trigger_version_thoughts(
        changelog_content=read_changelog(),
        version=current_version
    )
    update_stored_version_in_database(current_version)
```

**Comparison with Previous Version**:
- Previous version thoughts retrieved for context
- Changes between versions highlighted
- Lilith's opinion compares old vs new functionality
- Improvement assessment and concerns noted

**Data Stored**:
- Technical summary of changes
- Lilith's personal opinion about the version
- Previous version thoughts for comparison
- Generation time and tokens used
- Version string and changelog content
- Success/failure status

### 2. Self-Check Thoughts
**Purpose**: Lilith's honest opinions about system health and diagnostic results

**When Generated**:
- **On system startup**: Immediately when the service starts
- **Every 24 hours**: Scheduled background task (midnight UTC)
- **Manual trigger**: Via `/call self_check` command, `/selfcheck` Telegram command, or admin API call

**Schedule**:
- **Frequency**: Every 24 hours (reduced from hourly for efficiency)
- **Next run**: Stored in background service state
- **Retry logic**: If failed, retry after 1 hour

**Manual Trigger Access**:
```bash
# Via /call command
/call self_check
/call self_check force=true verbose=true

# Via Telegram bot
/selfcheck

# Via API (admin only)
curl -H "X-API-Key: YOUR_KEY" "https://your-domain.com/status?trigger_self_check=true"
```

**Tool Integration**:
- Accessible as a tool: `/call self_check`
- Tool parameters: `force` (bypass cache), `verbose` (detailed results)
- Returns formatted results with Lilith's opinion
- Tool documentation available at `/tools/self_check.md`

**Data Stored**:
- Technical report of all tool checks
- Lilith's honest opinion about system state
- Individual tool results with confidence scores
- Total execution time and tokens used
- Success/failure status

### 3. Crypto Thoughts
**Purpose**: Crypto therapist analysis of market data and trends

**When Generated**:
- **Twice daily**: Every 12 hours on schedule (8 AM and 8 PM UTC)
- **On system startup**: Initial generation when service starts
- **Manual trigger**: Via admin command or API call (future feature)

**Schedule**:
- **Frequency**: Every 12 hours
- **Data sources**: CoinGecko API and Cointelegraph RSS
- **Cache duration**: 6 hours (allows manual refresh within schedule)

**Database Storage**:
All crypto API results are stored in database for admin access:

```python
# Stored crypto data structure
{
  "timestamp": "2025-11-03T01:00:00.000Z",
  "market_data": {
    "total_cryptocurrencies": 100,
    "bitcoin_price": 109558.50,
    "top_5": [...],
    "total_market_cap_top_20": 2450000000000,
    "average_change_24h": 2.3
  },
  "news_summary": [
    "Bitcoin reaches new all-time high",
    "Ethereum network upgrade successful",
    "Regulatory news affecting markets"
  ],
  "confidence_score": 0.85,
  "therapeutic_tone": "kawaii_mama_therapist",
  "processing_time_seconds": 0.8,
  "tokens_used": 120
}
```

**Admin Access to Crypto Data**:
Authenticated `/status` endpoint includes crypto database data:

```json
{
  "crypto_database_data": {
    "records": [...],  // Last 20 crypto data records
    "total_records": 20,
    "last_updated": "2025-11-03T01:00:00.000Z",
    "database_status": "operational"
  },
  "crypto_thoughts": {
    "available": true,
    "market_analysis": "Bitcoin is showing strong momentum...",
    "irrational_behavior": "Investors are showing...",
    "uncomfortable_truth": "Retail investors continue to...",
    "api_results": {
      // Raw API results from database
    }
  }
}
```

**Data Stored**:
- 3-paragraph analysis (market, behavior, uncomfortable truth)
- Raw API results from CoinGecko and Cointelegraph
- Market data summary and news items
- Generation time and tokens used
- Confidence score and therapeutic tone
- Success/failure status
- Historical database records for admin access

## Background Task Management

### Service Startup
```python
# In bot.py or main application startup
from services.thoughts_background_service import thoughts_background_service

# Start all background tasks
await thoughts_background_service.start_background_tasks()

# Trigger version thoughts if version changed
if version_changed:
    await thoughts_background_service.trigger_version_thoughts(
        changelog_content, new_version
    )
```

### Service Shutdown
```python
# Graceful shutdown
await thoughts_background_service.stop_background_tasks()
```

## API Access

### Single Comprehensive Endpoint: `/statusm`
- **Method**: GET
- **Response**: All thoughts data with timing information
- **Source**: Database/storage (no live generation)
- **Response Time**: <100ms (database query only)

**Response Structure**:
```json
{
  "versiontxt": "v2.1.0-enhanced-status-abc123",
  "version": "v2.1.0",
  "commit": "abc123def456",
  "uptime": 3600.0,
  "start_time": "2025-11-03T01:00:00.000Z",
  "version_thoughts": {
    "available": true,
    "content": "Full version thoughts content",
    "technical_summary": "Technical summary of changes",
    "lilith_opinion": "Lilith's personal opinion",
    "generation_time": 1.2,
    "tokens_used": 150,
    "last_updated": "2025-11-03T01:00:00.000Z",
    "success": true
  },
  "self_check_thoughts": {
    "available": true,
    "content": "Full self-check thoughts",
    "technical_report": "Technical diagnostic report",
    "lilith_honest_opinion": "Lilith's honest opinion",
    "tool_results": [...],
    "total_time": 2.5,
    "tokens_used": 200,
    "last_updated": "2025-11-03T01:00:00.000Z",
    "success": true
  },
  "crypto_thoughts": {
    "available": true,
    "content": "Full crypto analysis",
    "market_analysis": "Market analysis paragraph",
    "irrational_behavior": "Behavior analysis paragraph",
    "uncomfortable_truth": "Uncomfortable truth paragraph",
    "generation_time": 0.8,
    "tokens_used": 120,
    "last_updated": "2025-11-03T01:00:00.000Z",
    "success": true
  },
  "self_check_time_sec": 2.5,
  "crypto_thoughts_secs": 0.8,
  "crypto_thoughts_time": "2025-11-03T01:00:00.000Z",
  "crypto_thoughts_tokens": 120,
  "tokens_total": 470,
  "tokens_uptime": 0.13,
  "redis": {"status": "operational", "response_time": 0.1},
  "postgresql": {"status": "operational", "connections": 5},
  "telegram": {"status": "operational", "last_update": "..."},
  "bot": {"status": "operational", "commands_processed": 100},
  "image_tag": "dcmaidbot:latest",
  "build_time": "2025-11-02T12:00:00Z",
  "last_nudge_fact": null,
  "last_nudge_read": null,
  "timestamp": "2025-11-03T01:00:00.000Z"
}
```

## Timing Data Collection

All thought types track the following metrics:

### Generation Metrics
- **Generation Time**: Total time taken to generate thoughts (seconds)
- **Tokens Used**: Number of tokens consumed by LLM calls
- **Success Status**: Whether generation was successful
- **Timestamp**: When generation was completed

### Version Thoughts Specific
- Version string and changelog content
- Technical summary vs personal opinion separation
- Previous version thoughts for context

### Self-Check Thoughts Specific
- Individual tool results with confidence scores
- Expected vs actual outcomes for each tool
- Overall system health assessment

### Crypto Thoughts Specific
- Market data processing time
- API response times and status
- Data source reliability metrics

## Error Handling and Fallbacks

### Version Thoughts Errors
- Fallback message: "I'm having trouble thinking about the new version..."
- Store error information for debugging
- Retry on next version change or manual trigger

### Self-Check Thoughts Errors
- Fallback message: "I'm feeling overwhelmed by all these errors..."
- Continue background scheduler
- Retry on next scheduled run

### Crypto Thoughts Errors
- Fallback message: "Even crypto therapists need to rest sometimes..."
- Continue twice-daily schedule
- Use cached data if available

## Storage Strategy

### Current Implementation (In-Memory)
- Stored in background service memory
- Lost on service restart
- Fast access for API responses

### Future Implementation (Database)
- Persist in database tables:
  - `version_thoughts`
  - `self_check_thoughts`
  - `crypto_thoughts`
- Retain history for analysis
- Survive service restarts

## Monitoring and Alerts

### Success Metrics
- Version thoughts generation success rate: >95%
- Self-check thoughts generation success rate: >90%
- Crypto thoughts generation success rate: >85%

### Alert Conditions
- Thoughts generation failure rate >10%
- Generation time >30 seconds
- Tokens usage >1000 per hour
- Background task not running

### Logging Levels
- **INFO**: Successful generation and timing data
- **WARNING**: Retry attempts and slow generation
- **ERROR**: Failed generation and API errors
- **DEBUG**: Detailed background task status

## Configuration

### Environment Variables
```bash
# Thought generation intervals (seconds)
SELF_CHECK_INTERVAL=3600  # 1 hour
CRYPTO_THOUGHTS_INTERVAL=43200  # 12 hours

# API configuration
OPENAI_API_KEY=your_openai_key

# Retry configuration
MAX_RETRY_ATTEMPTS=3
RETRY_DELAY=60  # seconds
```

### Runtime Configuration
```python
thoughts_background_service.self_check_interval = timedelta(hours=1)
thoughts_background_service.crypto_thoughts_interval = timedelta(hours=12)
```

## Future Enhancements

### Planned Features
1. **Manual Refresh API**: POST `/statusm/refresh` to force refresh all thoughts
2. **Individual Thought Endpoints**: Access specific thought types separately
3. **Historical Data**: API to retrieve past thoughts with pagination
4. **Thoughts Analysis**: Metrics and trends over time
5. **Custom Schedules**: Per-thought-type schedule configuration
6. **Thoughts Export**: Download thoughts data in various formats

### Performance Optimizations
1. **Database Indexing**: Optimize queries for thought retrieval
2. **Cache Layer**: Redis cache for frequently accessed thoughts
3. **Batch Processing**: Generate multiple thoughts in parallel
4. **Compression**: Compress stored thoughts to save space
5. **Background Queues**: Use task queues for reliable processing
