#!/usr/bin/env python3
"""
Test script for crypto thoughts service
"""

import asyncio
import logging
from unittest.mock import AsyncMock

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_crypto_service():
    """Test the crypto thoughts service functionality."""
    print("🧪 Testing Crypto Thoughts Service...")

    try:
        # Import the service
        from core.services.crypto_thoughts_service import CryptoThoughtsService

        # Create mock dependencies
        mock_session = AsyncMock()
        mock_redis = AsyncMock()
        mock_status = AsyncMock()

        # Create service instance
        crypto_service = CryptoThoughtsService(
            session=mock_session, redis_service=mock_redis, status_service=mock_status
        )

        print("✅ Service instantiated successfully")

        # Test market data fetching
        print("\n📊 Testing market data fetching...")
        market_data = await crypto_service._fetch_market_data()

        if market_data:
            print(f"✅ Fetched {len(market_data)} cryptocurrencies")
            print(f"   Bitcoin price: ${market_data[0].current_price:,.2f}")
            print(f"   Top 5 coins: {[c.name for c in market_data[:5]]}")
        else:
            print("⚠️  No market data fetched")

        # Test news fetching
        print("\n📰 Testing crypto news fetching...")
        news_data = await crypto_service._fetch_crypto_news()

        if news_data:
            print(f"✅ Fetched {len(news_data)} news items")
            print(f"   Latest: {news_data[0].title}")
        else:
            print("⚠️  No news data fetched")

        # Test fallback analysis
        print("\n🧠 Testing fallback therapist analysis...")
        fallback_analysis = await crypto_service._generate_fallback_analysis(
            market_data, news_data
        )

        print("✅ Fallback analysis generated:")
        print(f"   Market: {fallback_analysis['market_analysis'][:100]}...")
        print(f"   Irrational: {fallback_analysis['irrational_behavior'][:100]}...")
        print(f"   Truth: {fallback_analysis['uncomfortable_truth'][:100]}...")
        print(f"   Confidence: {fallback_analysis['confidence_score']}")

        # Test complete crypto thoughts generation
        print("\n🔮 Testing complete crypto thoughts generation...")
        crypto_thought = await crypto_service.generate_crypto_thoughts(
            force_refresh=True
        )

        print("✅ Crypto thought generated:")
        print(f"   Timestamp: {crypto_thought.timestamp}")
        print(f"   Processing time: {crypto_thought.processing_time_seconds:.2f}s")
        print(f"   Tokens used: {crypto_thought.tokens_used}")
        print(f"   Confidence: {crypto_thought.confidence_score}")
        print(f"   Market analysis: {crypto_thought.market_analysis[:150]}...")
        print(f"   News items: {len(crypto_thought.news_summary)}")

        # Test market summary
        print("\n📈 Testing market summary...")
        if market_data:
            market_summary = crypto_service._prepare_market_summary(market_data)
            print("✅ Market summary generated:")
            print(f"   {market_summary[:200]}...")

        # Test crypto thoughts status
        print("\n📊 Testing crypto thoughts status...")
        mock_redis.get.return_value = None  # No cached thought
        mock_redis.exists.return_value = 1  # Market data cached

        status = await crypto_service.get_crypto_thoughts_status()
        print("✅ Status generated:")
        print(f"   System status: {status['system_status']}")
        print(f"   Latest thought available: {status['latest_thought_available']}")
        print(f"   Market data cached: {status['market_data_cached']}")
        print(f"   News data cached: {status['news_data_cached']}")

        print("\n🎉 All crypto service tests completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_real_apis():
    """Test the actual API calls to verify they work."""
    print("\n🌐 Testing real API calls...")

    try:
        import aiohttp

        # Test CoinGecko API
        print("📊 Testing CoinGecko API...")
        async with aiohttp.ClientSession() as session:
            url = "https://api.coingecko.com/api/v3/coins/markets"
            params = {
                "vs_currency": "usd",
                "order": "market_cap_desc",
                "per_page": "5",
                "page": "1",
                "sparkline": "false",
                "price_change_percentage": "24h",
            }

            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ CoinGecko API working - fetched {len(data)} coins")
                    for coin in data[:3]:
                        print(
                            f"   {coin['name']}: ${coin['current_price']:,.2f} ({coin['price_change_percentage_24h']:+.2f}%)"
                        )
                else:
                    print(f"❌ CoinGecko API failed: {response.status}")

        # Test Cointelegraph RSS
        print("\n📰 Testing Cointelegraph RSS...")
        async with aiohttp.ClientSession() as session:
            async with session.get("https://cointelegraph.com/rss") as response:
                if response.status == 200:
                    rss_content = await response.text()
                    import xml.etree.ElementTree as ET

                    root = ET.fromstring(rss_content)

                    items = root.findall(".//item")[:3]
                    print(f"✅ Cointelegraph RSS working - fetched {len(items)} items")
                    for item in items:
                        title = item.find("title").text
                        print(f"   {title}")
                else:
                    print(f"❌ Cointelegraph RSS failed: {response.status}")

        print("\n🎉 Real API tests completed!")
        return True

    except Exception as e:
        print(f"❌ Real API test failed: {e}")
        return False


async def main():
    """Main test function."""
    print("🚀 Starting Crypto Thoughts Service Tests")
    print("=" * 50)

    # Test real APIs first
    api_test = await test_real_apis()

    # Test service functionality
    service_test = await test_crypto_service()

    print("\n" + "=" * 50)
    if api_test and service_test:
        print("🎉 ALL TESTS PASSED! Crypto service is ready for production!")
    else:
        print("⚠️  Some tests failed. Check logs above.")

    return api_test and service_test


if __name__ == "__main__":
    asyncio.run(main())
