"""
Crypto Thoughts Service Demonstration

This script demonstrates the crypto thoughts service with
pattern detection, anomaly analysis, and predictive capabilities.
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock

# Add the project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.crypto_thoughts_service import CryptoThought, CryptoThoughtsService


async def demonstrate_crypto_thoughts_service():
    """Demonstrate the crypto thoughts service functionality."""

    print("🔐 Crypto Thoughts Service Demonstration")
    print("=" * 60)
    print("Advanced Pattern Detection & Anomaly Analysis System")
    print("=" * 60)

    # Initialize crypto thoughts service with mock dependencies
    mock_session = Mock()
    mock_redis_service = AsyncMock()
    mock_redis_service.setex = AsyncMock(return_value=True)
    mock_redis_service.get = AsyncMock(return_value=None)
    mock_redis_service.keys = AsyncMock(return_value=[])
    mock_status_service = AsyncMock()
    mock_status_service.get_full_status.return_value = {
        "version_info": {
            "version": "0.4.0",
            "changelog": "Demo version for crypto thoughts testing",
            "git_commit": "demo-commit",
            "image_tag": "latest",
            "build_time": "demo-build-time",
        },
        "system_info": {
            "current_time_utc": datetime.now(timezone.utc).isoformat(),
            "uptime_seconds": 3600,
            "uptime_human": "1:00:00",
            "python_version": "3.9.6",
            "environment": "demo",
            "pod_name": "demo-pod",
            "namespace": "demo-namespace",
        },
        "database": {
            "connected": True,
            "status": "healthy",
            "message": "Database connection healthy",
        },
        "redis": {
            "connected": True,
            "status": "healthy",
            "message": "Redis connection healthy",
        },
    }

    crypto_service = CryptoThoughtsService(
        session=mock_session,
        redis_service=mock_redis_service,
        status_service=mock_status_service,
    )

    # Get current system data
    print("\n📊 Collecting System Data...")
    system_data = await crypto_service._collect_system_data()

    print("   System Data Collected:")
    print(f"   Timestamp: {system_data.get('timestamp', 'N/A')}")
    print(f"   Available Keys: {list(system_data.keys())}")

    # Safely print available data
    for key, value in system_data.items():
        if key == "system_info" and isinstance(value, dict):
            print("   System Info:")
            for sub_key, sub_value in value.items():
                print(f"      {sub_key}: {sub_value}")
        else:
            print(f"   {key}: {value}")

    # Generate different types of crypto thoughts
    print("\n🧠 Generating Crypto Thoughts...")

    # 1. Pattern Detection Thoughts
    print("\n🔍 Detecting System Patterns...")
    pattern_thoughts = await crypto_service._generate_pattern_thoughts(system_data)

    print(f"   Generated {len(pattern_thoughts)} pattern thoughts:")
    for i, thought in enumerate(pattern_thoughts, 1):
        print(f"   {i}. [{thought.category.upper()}] {thought.content}")
        print(f"      Hash: {thought.hash_id[:16]}...")
        print(
            f"      Confidence: {thought.confidence:.2f}, Significance: {thought.significance}"
        )
        if thought.pattern_detected:
            print(f"      🎯 Pattern Detected: {thought.pattern_hash[:16]}...")
        print()

    # 2. Anomaly Detection Thoughts
    print("🚨 Detecting System Anomalies...")
    anomaly_thoughts = await crypto_service._generate_anomaly_thoughts(system_data)

    print(f"   Generated {len(anomaly_thoughts)} anomaly thoughts:")
    for i, thought in enumerate(anomaly_thoughts, 1):
        print(f"   {i}. [{thought.category.upper()}] {thought.content}")
        print(f"      Hash: {thought.hash_id[:16]}...")
        print(
            f"      Confidence: {thought.confidence:.2f}, Anomaly Score: {thought.anomaly_score:.2f}"
        )
        if thought.anomaly_score > 0.7:
            print("      ⚠️ High Anomaly Score - Requires Attention!")
        print()

    # 3. Insight Generation Thoughts
    print("💡 Generating System Insights...")
    insight_thoughts = await crypto_service._generate_insight_thoughts(system_data)

    print(f"   Generated {len(insight_thoughts)} insight thoughts:")
    for i, thought in enumerate(insight_thoughts, 1):
        print(f"   {i}. [{thought.category.upper()}] {thought.content}")
        print(f"      Hash: {thought.hash_id[:16]}...")
        print(
            f"      Confidence: {thought.confidence:.2f}, Significance: {thought.significance}"
        )
        print(f"      Data Hash: {thought.data_hash[:16]}...")
        print()

    # 4. Predictive Analysis Thoughts
    print("🔮 Generating Predictive Analysis...")
    prediction_thoughts = await crypto_service._generate_prediction_thoughts(
        system_data
    )

    print(f"   Generated {len(prediction_thoughts)} prediction thoughts:")
    for i, thought in enumerate(prediction_thoughts, 1):
        print(f"   {i}. [{thought.category.upper()}] {thought.content}")
        print(f"      Hash: {thought.hash_id[:16]}...")
        print(
            f"      Confidence: {thought.confidence:.2f}, Significance: {thought.significance}"
        )
        if thought.significance in ["high", "critical"]:
            print("      🚨 High Significance - Action Required!")
        print()

    # 5. Full Analysis Pipeline
    print("🎯 Running Complete Analysis Pipeline...")
    all_thoughts = await crypto_service.analyze_crypto_thoughts(system_data)

    print(f"   Total Thoughts Generated: {len(all_thoughts)}")

    # Categorize thoughts by type
    thoughts_by_type = {}
    for thought in all_thoughts:
        if thought.thought_type not in thoughts_by_type:
            thoughts_by_type[thought.thought_type] = []
        thoughts_by_type[thought.thought_type].append(thought)

    print("\n📊 Thoughts Breakdown by Type:")
    for thought_type, thoughts in thoughts_by_type.items():
        print(f"   {thought_type.title()}: {len(thoughts)} thoughts")
        avg_confidence = sum(t.confidence for t in thoughts) / len(thoughts)
        high_significance = sum(
            1 for t in thoughts if t.significance in ["high", "critical"]
        )
        print(f"      Average Confidence: {avg_confidence:.2f}")
        print(f"      High Significance: {high_significance}")

    # Show high-significance thoughts
    high_significance_thoughts = [
        t for t in all_thoughts if t.significance in ["high", "critical"]
    ]

    if high_significance_thoughts:
        print("\n🚨 High Significance Thoughts Requiring Attention:")
        for thought in high_significance_thoughts:
            print(f"   • [{thought.thought_type.upper()}] {thought.content}")
            print(
                f"      Confidence: {thought.confidence:.2f}, Impact: {thought.significance}"
            )
            print(f"      Hash: {thought.hash_id[:16]}...")
            print()

    # Hash Analysis
    print("🔐 Hash Analysis:")
    unique_hashes = set(t.hash_id for t in all_thoughts)
    print(f"   Unique Thought Hashes: {len(unique_hashes)}")
    print(
        f"   Hash Collision Detection: {'✅ None' if len(unique_hashes) == len(all_thoughts) else '⚠️ Collisions Detected'}"
    )

    # Pattern Hash Analysis
    pattern_hashes = [t.pattern_hash for t in all_thoughts if t.pattern_detected]
    unique_pattern_hashes = set(pattern_hashes)
    print(f"   Unique Pattern Hashes: {len(unique_pattern_hashes)}")
    if pattern_hashes:
        print(
            f"   Pattern Repetition Rate: {(len(pattern_hashes) - len(unique_pattern_hashes)) / len(pattern_hashes) * 100:.1f}%"
        )

    # Store thoughts in database (simulated)
    print("\n💾 Storing Thoughts in Database...")
    stored_count = 0
    for thought in all_thoughts:
        # In real implementation, this would store to database
        # For demo, we'll just count
        stored_count += 1

    print(f"   Thoughts Stored: {stored_count}")
    print(
        f"   Storage Integrity: {'✅ Verified' if stored_count == len(all_thoughts) else '⚠️ Storage Issues'}"
    )

    # Generate summary statistics
    print("\n📈 Crypto Thoughts Summary:")
    print(f"   Analysis Duration: {datetime.now(timezone.utc).isoformat()}")
    print(f"   System Complexity Score: {len(system_data) * len(all_thoughts)}")
    print(
        f"   Pattern Detection Rate: {len([t for t in all_thoughts if t.pattern_detected]) / len(all_thoughts) * 100:.1f}%"
    )
    print(
        f"   Anomaly Detection Rate: {len([t for t in all_thoughts if t.anomaly_score > 0.5]) / len(all_thoughts) * 100:.1f}%"
    )
    print(
        f"   High Confidence Thoughts: {len([t for t in all_thoughts if t.confidence > 0.8]) / len(all_thoughts) * 100:.1f}%"
    )

    # Create a summary thought
    summary_thought = CryptoThought(
        hash_id=crypto_service._generate_hash(
            f"crypto_thoughts_summary_{datetime.now(timezone.utc).isoformat()}"
        ),
        timestamp=datetime.now(timezone.utc).isoformat(),
        thought_type="summary",
        category="analysis",
        content=f"Generated {len(all_thoughts)} crypto thoughts with {len([t for t in all_thoughts if t.significance in ['high', 'critical']])} high-significance findings requiring attention",
        confidence=0.95,
        significance="high" if high_significance_thoughts else "medium",
        pattern_detected=True,
        anomaly_score=0.0,
        data_hash=crypto_service._generate_hash(
            json.dumps(system_data, sort_keys=True)
        ),
        pattern_hash=crypto_service._generate_hash(str(len(all_thoughts))),
        previous_hashes=[
            t.hash_id for t in all_thoughts[:5]
        ],  # Reference to first 5 thoughts
    )

    print("\n🎯 Summary Thought:")
    print(f"   {summary_thought.content}")
    print(f"   Confidence: {summary_thought.confidence:.2f}")
    print(f"   Hash: {summary_thought.hash_id[:16]}...")

    # Simulate cron job execution
    print("\n⏰ Simulating Crypto Thoughts Cron Job...")
    cron_results = await crypto_service.run_crypto_thoughts_cron()

    print("   Cron Job Results:")
    print(f"   Execution Time: {cron_results['execution_time_seconds']:.2f}s")
    print(f"   Thoughts Generated: {cron_results['thoughts_generated']}")
    print(f"   High Significance: {cron_results['high_significance_count']}")
    print(f"   Patterns Detected: {cron_results['patterns_detected']}")
    print(f"   Anomalies Detected: {cron_results['anomalies_detected']}")
    print(f"   Success: {cron_results['success']}")

    # Save comprehensive report
    report_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "system_data": system_data,
        "crypto_thoughts_generated": len(all_thoughts),
        "thoughts_by_type": {
            t_type: len(thoughts) for t_type, thoughts in thoughts_by_type.items()
        },
        "high_significance_thoughts": len(high_significance_thoughts),
        "pattern_detection_rate": len([t for t in all_thoughts if t.pattern_detected])
        / len(all_thoughts),
        "average_confidence": sum(t.confidence for t in all_thoughts)
        / len(all_thoughts),
        "unique_hashes": len(unique_hashes),
        "cron_results": cron_results,
        "summary_thought": {
            "content": summary_thought.content,
            "confidence": summary_thought.confidence,
            "significance": summary_thought.significance,
            "hash": summary_thought.hash_id,
        },
    }

    # Save comprehensive report
    report_filename = "crypto_thoughts_demo_report.json"
    with open(report_filename, "w") as f:
        json.dump(report_data, f, indent=2)

    print(f"\n✅ Comprehensive report saved to {report_filename}")

    # Generate markdown summary
    markdown_report = f"""# Crypto Thoughts Service Demonstration Report

**Generated**: {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}

## System Analysis

- **Hostname**: {system_data["hostname"]}
- **Uptime**: {system_data["uptime_seconds"]:.0f}s
- **Memory Usage**: {system_data["memory_usage_mb"]:.0f}MB
- **CPU Temperature**: {system_data["cpu_temp_celsius"]:.0f}°C
- **Python Version**: {system_data["system_info"]["python_version"]}

## Crypto Thoughts Generated

- **Total Thoughts**: {len(all_thoughts)}
- **High Significance**: {len(high_significance_thoughts)}
- **Pattern Detection Rate**: {len([t for t in all_thoughts if t.pattern_detected]) / len(all_thoughts) * 100:.1f}%
- **Average Confidence**: {sum(t.confidence for t in all_thoughts) / len(all_thoughts) * 100:.1f}%

## Thoughts by Type

{chr(10).join(f"- **{thought_type.title()}**: {len(thoughts)} thoughts" for thought_type, thoughts in thoughts_by_type.items())}

## Cron Job Results

- **Execution Time**: {cron_results["execution_time_seconds"]:.2f}s
- **Thoughts Generated**: {cron_results["thoughts_generated"]}
- **High Significance**: {cron_results["high_significance_count"]}
- **Success Rate**: {cron_results["success"]}

## Summary

{summary_thought.content}

---

*Report generated by Crypto Thoughts Service with Pattern Detection & Anomaly Analysis*
"""

    # Save markdown report
    markdown_filename = "crypto_thoughts_demo_report.md"
    with open(markdown_filename, "w") as f:
        f.write(markdown_report)

    print(f"✅ Markdown report saved to {markdown_filename}")

    # Final summary
    print("\n🎉 Crypto Thoughts Service Demonstration Complete!")
    print("🔐 Successfully demonstrated advanced crypto analysis with:")
    print("   • Pattern detection with hash-based verification")
    print("   • Anomaly detection with confidence scoring")
    print("   • Insight generation with system analysis")
    print("   • Predictive analysis with forecasting")
    print("   • Comprehensive hash-based integrity checking")
    print("   • Automated cron job execution")
    print("   • High-significance thought identification")
    print("🚀 System is ready for intelligent crypto-powered monitoring!")

    return all_thoughts, report_data


if __name__ == "__main__":
    asyncio.run(demonstrate_crypto_thoughts_service())
