# Crypto Thoughts Tool

## Overview
The crypto thoughts tool generates market insights and analysis for cryptocurrency markets. It combines data from multiple sources to provide educational and entertaining content about crypto markets.

## Business Value
- Provides users with crypto market insights
- Educational content about market behavior
- Entertainment value with personality-driven analysis
- Automated market monitoring and reporting

## Configuration
- **Environment Variables**:
  - `COINGECKO_API_KEY`: API key for CoinGecko (free tier available)
  - `CRYPTO_UPDATE_INTERVAL`: Hours between updates (default: 12)
  - `CRYPTO_THOUGHTS_ENABLED`: Enable/disable crypto thoughts (default: true)
- **Data Sources**: CoinGecko API, Cointelegraph RSS feed
- **Update Schedule**: Twice daily via cron job

## Usage Examples

### Automated Generation
```
# Runs automatically every 12 hours
/crypto thoughts
```

### Manual Trigger
```
/call tell me about crypto market
/call what's happening in crypto
/call give me crypto insights
```

## Data Sources

### CoinGecko API
- **Endpoint**: `https://api.coingecko.com/api/v3/coins/markets`
- **Data**: Top 100 cryptocurrencies by market cap
- **Fields**: Price, market cap, 24h change, trading volume
- **Rate Limit**: 10-50 requests per minute

### Cointelegraph RSS
- **Feed**: `https://cointelegraph.com/rss`
- **Content**: Crypto news headlines and summaries
- **Update Frequency**: Real-time
- **Language**: English

## AI Prompt Structure
```
You're a tired crypto therapist. And she always telling news you something about crypto.
Let's read all abra-cadabra letters about that bethomens-criptoins in their metawersis
{COINGECKO_DATA + CRYPTOTELEGRAPH_NEWS}

NOW after we read all that, lets write 3 paragraphs:
1) Explain as child to parent what's ACTUALLY happening in the numbers (ignore headlines)
2) What irrational behavior this is triggering
3) One uncomfortable truth about why retail loses money.
Be childlish but shy and educational.
```

## Output Format
- **Length**: 3 paragraphs
- **Style**: Educational yet entertaining
- **Tone**: Child-like but shy and insightful
- **Language**: Simple, accessible explanations

## Performance Metrics
- **Generation Time**: < 30 seconds
- **Data Freshness**: Updated every 12 hours
- **Token Usage**: ~500-800 tokens per generation
- **Success Rate**: > 90%

## Storage Requirements
- **crypto_thoughts**: Generated content text
- **crypto_thoughts_secs**: Generation duration in seconds
- **crypto_thoughts_timestamp**: ISO timestamp of generation
- **crypto_thoughts_tokens**: Tokens used for generation

## Error Handling

### API Failures
- **CoinGecko Unavailable**: Use cached market data
- **RSS Feed Issues**: Skip news analysis, focus on numbers only
- **Network Timeouts**: Retry with exponential backoff

### Content Generation Issues
- **LLM Service Down**: Provide template-based insights
- **Content Too Short**: Regenerate with adjusted prompt
- **Inappropriate Content**: Filter and regenerate

## Troubleshooting

### Common Issues
1. **No Crypto Data Available**
   - Check CoinGecko API connectivity
   - Verify API key configuration
   - Check network connectivity

2. **Generic Content Generated**
   - Verify RSS feed is accessible
   - Check prompt template integrity
   - Ensure sufficient context data

3. **Generation Taking Too Long**
   - Monitor API response times
   - Check LLM service performance
   - Consider reducing data scope

## Security Considerations
- Validate API responses before processing
- Sanitize RSS feed content
- Rate limit crypto thoughts generation
- Monitor for market manipulation content

## Monitoring
- Track API quota usage
- Monitor generation success rates
- Analyze content quality metrics
- Track user engagement with crypto content

## Integration Points
- **Status System**: Include in /status response
- **Cron Jobs**: Automated generation schedule
- **Token Tracking**: Monitor LLM usage
- **Database**: Store generated content and metadata

---
*Last Updated: 2025-11-02*
*Version: 1.0*
*Status: Operational*
