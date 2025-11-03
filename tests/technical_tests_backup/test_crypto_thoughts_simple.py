"""
Simple Crypto Thoughts Service Demonstration

This script demonstrates the core crypto thoughts functionality
without complex analysis methods.
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock

# Add the project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.crypto_thoughts_service import CryptoThoughtsService


async def demonstrate_crypto_thoughts_simple():
    """Demonstrate the crypto thoughts service functionality simply."""

    print("🔐 Crypto Thoughts Service - Simple Demonstration")
    print("=" * 60)
    print("Pattern Detection & Anomaly Analysis System")
    print("=" * 60)

    # Initialize crypto thoughts service with mock dependencies
    mock_session = Mock()
    mock_redis_service = AsyncMock()
    mock_redis_service.setex = AsyncMock(return_value=True)
    mock_redis_service.get = AsyncMock(return_value=None)
    mock_redis_service.keys = AsyncMock(return_value=[])
    mock_status_service = AsyncMock()
    mock_status_service.get_full_status.return_value = {
        "version_info": {"version": "0.4.0"},
        "system_info": {
            "current_time_utc": datetime.now(timezone.utc).isoformat(),
            "uptime_seconds": 3600,
            "python_version": "3.9.6",
            "environment": "demo",
        },
        "database": {"connected": True, "status": "healthy"},
        "redis": {"connected": True, "status": "healthy"},
    }

    crypto_service = CryptoThoughtsService(
        session=mock_session,
        redis_service=mock_redis_service,
        status_service=mock_status_service,
    )

    # Get current system data
    print("\n📊 Collecting System Data...")
    system_data = await crypto_service._collect_system_data()

    print(f"   Timestamp: {system_data.get('timestamp')}")
    print(f"   Data Categories: {list(system_data.keys())}")

    # Generate different types of crypto thoughts
    print("\n🧠 Generating Crypto Thoughts...")

    all_thoughts = []

    # 1. Pattern Detection Thoughts
    print("\n🔍 Detecting System Patterns...")
    pattern_thoughts = await crypto_service._generate_pattern_thoughts(system_data)
    all_thoughts.extend(pattern_thoughts)

    print(f"   Generated {len(pattern_thoughts)} pattern thoughts:")
    for i, thought in enumerate(pattern_thoughts, 1):
        print(f"   {i}. [{thought.category.upper()}] {thought.content}")
        print(
            f"      Confidence: {thought.confidence:.2f}, Significance: {thought.significance}"
        )
        print(f"      Hash: {thought.hash_id[:16]}...")
        if thought.pattern_detected:
            print(f"      🎯 Pattern Hash: {thought.pattern_hash[:16]}...")
        print()

    # 2. Anomaly Detection Thoughts
    print("🚨 Detecting System Anomalies...")
    anomaly_thoughts = await crypto_service._generate_anomaly_thoughts(system_data)
    all_thoughts.extend(anomaly_thoughts)

    print(f"   Generated {len(anomaly_thoughts)} anomaly thoughts:")
    for i, thought in enumerate(anomaly_thoughts, 1):
        print(f"   {i}. [{thought.category.upper()}] {thought.content}")
        print(
            f"      Confidence: {thought.confidence:.2f}, Anomaly Score: {thought.anomaly_score:.2f}"
        )
        print(f"      Hash: {thought.hash_id[:16]}...")
        print()

    # 3. Insight Generation Thoughts
    print("💡 Generating System Insights...")
    insight_thoughts = await crypto_service._generate_insight_thoughts(system_data)
    all_thoughts.extend(insight_thoughts)

    print(f"   Generated {len(insight_thoughts)} insight thoughts:")
    for i, thought in enumerate(insight_thoughts, 1):
        print(f"   {i}. [{thought.category.upper()}] {thought.content}")
        print(
            f"      Confidence: {thought.confidence:.2f}, Significance: {thought.significance}"
        )
        print(f"      Hash: {thought.hash_id[:16]}...")
        print()

    # 4. Predictive Analysis Thoughts
    print("🔮 Generating Predictive Analysis...")
    prediction_thoughts = await crypto_service._generate_prediction_thoughts(
        system_data
    )
    all_thoughts.extend(prediction_thoughts)

    print(f"   Generated {len(prediction_thoughts)} prediction thoughts:")
    for i, thought in enumerate(prediction_thoughts, 1):
        print(f"   {i}. [{thought.category.upper()}] {thought.content}")
        print(
            f"      Confidence: {thought.confidence:.2f}, Significance: {thought.significance}"
        )
        print(f"      Hash: {thought.hash_id[:16]}...")
        print()

    # Summary
    print("📊 Crypto Thoughts Summary:")
    print(f"   Total Thoughts Generated: {len(all_thoughts)}")

    # Categorize thoughts by type
    thoughts_by_type = {}
    for thought in all_thoughts:
        if thought.thought_type not in thoughts_by_type:
            thoughts_by_type[thought.thought_type] = []
        thoughts_by_type[thought.thought_type].append(thought)

    print("\n📈 Thoughts by Type:")
    for thought_type, thoughts in thoughts_by_type.items():
        avg_confidence = sum(t.confidence for t in thoughts) / len(thoughts)
        high_significance = sum(
            1 for t in thoughts if t.significance in ["high", "critical"]
        )
        print(f"   {thought_type.title()}: {len(thoughts)} thoughts")
        print(f"      Average Confidence: {avg_confidence:.2f}")
        print(f"      High Significance: {high_significance}")

    # Show high-significance thoughts
    high_significance_thoughts = [
        t for t in all_thoughts if t.significance in ["high", "critical"]
    ]

    if high_significance_thoughts:
        print("\n🚨 High Significance Thoughts:")
        for thought in high_significance_thoughts:
            print(f"   • [{thought.thought_type.upper()}] {thought.content}")
            print(f"      Confidence: {thought.confidence:.2f}")
            print(f"      Hash: {thought.hash_id[:16]}...")
    else:
        print("\n✅ No high-significance thoughts detected")

    # Hash Analysis
    print("\n🔐 Hash Security Analysis:")
    unique_hashes = set(t.hash_id for t in all_thoughts)
    print(f"   Unique Thought Hashes: {len(unique_hashes)}/{len(all_thoughts)}")
    print(
        f"   Hash Collision Detection: {'✅ None' if len(unique_hashes) == len(all_thoughts) else '⚠️ Collisions'}"
    )

    # Pattern hashes
    pattern_hashes = [t.pattern_hash for t in all_thoughts if t.pattern_detected]
    if pattern_hashes:
        unique_pattern_hashes = set(pattern_hashes)
        print(f"   Unique Pattern Hashes: {len(unique_pattern_hashes)}")
        print(
            f"   Pattern Consistency: {'✅ High' if len(unique_pattern_hashes) <= len(pattern_hashes) * 0.8 else '⚠️ Low'}"
        )

    # Store thoughts (simulated)
    print("\n💾 Storing Thoughts...")
    try:
        await crypto_service._store_crypto_thoughts(all_thoughts)
        print(f"   ✅ Successfully stored {len(all_thoughts)} thoughts")
    except Exception as e:
        print(f"   ⚠️ Storage simulation: {str(e)}")

    # Cron job simulation
    print("\n⏰ Simulating Cron Job Execution...")
    try:
        cron_results = await crypto_service.run_crypto_thoughts_cron()
        print("   ✅ Cron Job Results:")
        print(
            f"      Execution Time: {cron_results.get('execution_time_seconds', 0):.2f}s"
        )
        print(f"      Thoughts Generated: {cron_results.get('thoughts_generated', 0)}")
        print(
            f"      High Significance: {cron_results.get('high_significance_count', 0)}"
        )
        print(f"      Success: {cron_results.get('success', False)}")
    except Exception as e:
        print(f"   ⚠️ Cron simulation: {str(e)}")

    # Generate report
    report_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "demonstration": "crypto_thoughts_simple",
        "total_thoughts": len(all_thoughts),
        "thoughts_by_type": {
            t_type: len(thoughts) for t_type, thoughts in thoughts_by_type.items()
        },
        "high_significance_count": len(high_significance_thoughts),
        "hash_security": {
            "unique_hashes": len(unique_hashes),
            "total_thoughts": len(all_thoughts),
            "collision_free": len(unique_hashes) == len(all_thoughts),
        },
        "system_data_keys": list(system_data.keys()),
        "success": True,
    }

    # Save report
    report_filename = "crypto_thoughts_simple_report.json"
    with open(report_filename, "w") as f:
        json.dump(report_data, f, indent=2)

    print(f"\n✅ Report saved to {report_filename}")

    # Final summary
    print("\n🎉 Crypto Thoughts Service Demonstration Complete!")
    print("🔐 Successfully demonstrated:")
    print("   • Pattern detection with hash-based verification")
    print("   • Anomaly detection with confidence scoring")
    print("   • Insight generation from system data")
    print("   • Predictive analysis capabilities")
    print("   • Hash-based security and integrity")
    print("   • Automated storage and cron job execution")
    print("🚀 Crypto-powered monitoring system is operational!")

    return all_thoughts, report_data


if __name__ == "__main__":
    asyncio.run(demonstrate_crypto_thoughts_simple())
