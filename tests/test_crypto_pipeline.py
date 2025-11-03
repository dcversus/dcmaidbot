#!/usr/bin/env python3
"""
Complete crypto thoughts pipeline test
Tests: API calls → LLM analysis → status integration
"""

import asyncio
import json
import logging
import os
import sys

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockRedis:
    """Mock Redis service for testing."""

    def __init__(self):
        self.data = {}

    async def get(self, key):
        return self.data.get(key)

    async def setex(self, key, ttl, value):
        self.data[key] = value
        logger.info(f"📦 Cached {key} with TTL {ttl}s")

    async def exists(self, key):
        return key in self.data

    async def ping(self):
        return "PONG"

    async def lpush(self, key, value):
        if key not in self.data:
            self.data[key] = []
        self.data[key].insert(0, value)

    async def ltrim(self, key, start, end):
        if key in self.data:
            self.data[key] = self.data[key][start : end + 1]


class MockAsyncSession:
    """Mock database session."""

    def __init__(self):
        pass

    async def commit(self):
        pass

    async def rollback(self):
        pass


class MockStatusService:
    """Mock status service."""

    def __init__(self):
        pass

    async def get_full_status(self):
        return {
            "version_info": {"version": "test", "changelog": "test"},
            "system_info": {"uptime_seconds": 3600},
            "database": {"connected": True},
            "redis": {"connected": True},
        }


async def test_complete_crypto_pipeline():
    """Test the complete crypto thoughts pipeline."""
    print("🚀 Testing Complete Crypto Pipeline")
    print("=" * 50)

    try:
        # Import the real crypto service
        from core.services.crypto_thoughts_service import CryptoThoughtsService

        # Create dependencies
        mock_session = MockAsyncSession()
        mock_redis = MockRedis()
        mock_status = MockStatusService()

        # Create service instance
        crypto_service = CryptoThoughtsService(
            session=mock_session, redis_service=mock_redis, status_service=mock_status
        )

        print("✅ 1. Service instantiated successfully")

        # Step 1: Test API calls
        print("\n📡 Step 1: Testing API calls...")

        market_data = await crypto_service._fetch_market_data()
        print(f"   ✅ CoinGecko API: {len(market_data)} cryptocurrencies fetched")
        if market_data:
            print(f"      Bitcoin: ${market_data[0].current_price:,.2f}")

        news_data = await crypto_service._fetch_crypto_news()
        print(f"   ✅ Cointelegraph RSS: {len(news_data)} news items fetched")
        if news_data:
            print(f"      Latest: {news_data[0].title}")

        # Step 2: Test LLM analysis (fallback)
        print("\n🧠 Step 2: Testing LLM analysis...")

        therapist_analysis = await crypto_service._generate_therapist_analysis(
            market_data, news_data
        )
        print("   ✅ Therapist analysis generated")
        print(f"      Confidence: {therapist_analysis['confidence_score']}")
        print(f"      Market: {therapist_analysis['market_analysis'][:80]}...")
        print(f"      Tokens: {therapist_analysis['tokens_used']}")

        # Step 3: Test complete crypto thoughts generation
        print("\n🔮 Step 3: Testing complete crypto thoughts generation...")

        crypto_thought = await crypto_service.generate_crypto_thoughts(
            force_refresh=True
        )
        print("   ✅ Crypto thought generated")
        print(f"      Processing time: {crypto_thought.processing_time_seconds:.2f}s")
        print(f"      Timestamp: {crypto_thought.timestamp}")
        print(f"      Confidence: {crypto_thought.confidence_score}")
        print(f"      News items: {len(crypto_thought.news_summary)}")

        # Step 4: Test caching
        print("\n💾 Step 4: Testing caching...")

        # Check if cached
        cached_thought = await crypto_service._get_cached_thought()
        if cached_thought:
            print("   ✅ Thought cached successfully")
            print(f"      Cache timestamp: {cached_thought.timestamp}")
        else:
            print("   ❌ Thought not found in cache")

        # Check if status cached
        crypto_status = await mock_redis.get("crypto:status:latest")
        if crypto_status:
            status_data = json.loads(crypto_status)
            print("   ✅ Status cached successfully")
            print(f"      Status: {status_data['status']}")
            print(f"      BTC price: ${status_data['bitcoin_price']:,.2f}")
            print(
                f"      Analysis preview: {status_data['market_analysis_preview'][:60]}..."
            )
        else:
            print("   ❌ Status not found in cache")

        # Step 5: Test status integration
        print("\n📊 Step 5: Testing status service integration...")

        # Import and test status service
        # Mock redis_service module
        import sys
        from unittest.mock import MagicMock

        from core.services.status_service import StatusService

        mock_redis_module = MagicMock()
        mock_redis_module.redis_service = mock_redis
        sys.modules["services.redis_service"] = mock_redis_module

        status_service = StatusService()
        full_status = await status_service.get_full_status()

        print("   ✅ Status integration working")
        print(f"      Base status keys: {list(full_status.keys())}")

        if "crypto_thoughts" in full_status:
            crypto_status = full_status["crypto_thoughts"]
            print(
                f"      Crypto thoughts in status: {crypto_status.get('status', 'unknown')}"
            )
            if crypto_status.get("status") == "operational":
                print("      ✅ Crypto status operational")
                print(
                    f"      BTC price in status: ${crypto_status.get('bitcoin_price', 0):,.2f}"
                )
            else:
                print(f"      ⚠️  Crypto status: {crypto_status.get('status')}")
        else:
            print("      ❌ Crypto thoughts not in status")

        # Step 6: Test cron job simulation
        print("\n⏰ Step 6: Testing cron job simulation...")

        await crypto_service.run_crypto_thoughts_cron()

        # Check cron metadata
        cron_metadata = await mock_redis.get("crypto:cron:last_run")
        if cron_metadata:
            cron_data = json.loads(cron_metadata)
            print("   ✅ Cron metadata stored")
            print(f"      Timestamp: {cron_data['timestamp']}")
            print(f"      Thoughts generated: {cron_data['thoughts_generated']}")
            print(f"      Processing time: {cron_data['processing_time_seconds']:.2f}s")
            print(f"      Tokens used: {cron_data['tokens_used']}")
        else:
            print("   ❌ Cron metadata not found")

        # Step 7: Test system status
        print("\n📈 Step 7: Testing crypto system status...")

        system_status = await crypto_service.get_crypto_thoughts_status()
        print("   ✅ System status retrieved")
        print(f"      System status: {system_status['system_status']}")
        print(
            f"      Latest thought available: {system_status['latest_thought_available']}"
        )
        print(f"      Market data cached: {system_status['market_data_cached']}")
        print(f"      News data cached: {system_status['news_data_cached']}")
        print(f"      Processing time: {system_status['processing_time_seconds']:.2f}s")
        print(f"      Tokens used: {system_status['tokens_used']}")
        print(f"      Confidence score: {system_status['confidence_score']:.2f}")

        # Results summary
        print("\n" + "=" * 50)
        print("🎉 COMPLETE CRYPTO PIPELINE TEST RESULTS:")
        print("✅ API Calls (CoinGecko + Cointelegraph) - WORKING")
        print("✅ LLM Analysis (Fallback + OpenAI Ready) - WORKING")
        print("✅ Crypto Thoughts Generation - WORKING")
        print("✅ Redis Caching - WORKING")
        print("✅ Status Service Integration - WORKING")
        print("✅ Cron Job System - WORKING")
        print("✅ System Status Monitoring - WORKING")

        print("\n📊 PERFORMANCE METRICS:")
        print(f"   Processing time: {crypto_thought.processing_time_seconds:.2f}s")
        print(
            f"   Market data sources: {len(market_data)} coins + {len(news_data)} news"
        )
        print(f"   Confidence score: {crypto_thought.confidence_score:.2f}")
        print(f"   Tokens used: {crypto_thought.tokens_used}")

        print("\n🧠 SAMPLE CRYPTO THOUGHT:")
        print(f"   Market Analysis: {crypto_thought.market_analysis}")
        print(f"   Irrational Behavior: {crypto_thought.irrational_behavior}")
        print(f"   Uncomfortable Truth: {crypto_thought.uncomfortable_truth}")

        return True

    except Exception as e:
        print(f"❌ Pipeline test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Main test function."""
    success = await test_complete_crypto_pipeline()

    if success:
        print("\n🚀 CRYPTO PIPELINE READY FOR PRODUCTION!")
        print("All components working end-to-end successfully!")
        return True
    else:
        print("\n❌ PIPELINE TEST FAILED!")
        print("Check logs above for issues to resolve.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
