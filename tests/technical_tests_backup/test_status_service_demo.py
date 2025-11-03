"""
Status Service Demonstration

This script demonstrates the enhanced status service with
version_thoughts and self_check_thoughts functionality.
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timezone

# Add the project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.status_service import StatusService


async def demonstrate_status_service():
    """Demonstrate the enhanced status service functionality."""

    print("🔍 Status Service Demonstration")
    print("=" * 60)
    print("Enhanced Status Service with Version Thoughts & Self-Check Thoughts")
    print("=" * 60)

    # Initialize status service
    status_service = StatusService()

    # Get current system status
    print("\n📊 Getting Current System Status...")
    current_status = await status_service.get_full_status()

    # Display basic status information
    print("\n🎯 System Status Overview:")
    print(f"   Version: {current_status['version_info']['version']}")
    print(f"   Python: {current_status['system_info']['python_version']}")
    print(f"   Environment: {current_status['system_info']['environment']}")
    print(f"   Uptime: {current_status['system_info']['uptime_human']}")
    print(f"   Database: {current_status['database']['status']}")
    print(f"   Redis: {current_status['redis']['status']}")

    # Generate version thoughts
    print("\n🧠 Generating Version Thoughts...")
    version_thoughts = await status_service.generate_version_thoughts(current_status)

    print(f"   Generated {len(version_thoughts)} version thoughts:")
    for i, thought in enumerate(version_thoughts, 1):
        print(f"   {i}. [{thought.category.upper()}] {thought.content}")
        print(f"      Confidence: {thought.confidence:.1f}, Impact: {thought.impact}")
        if thought.actionable:
            print("      🔧 Actionable: Yes")
            for rec in thought.recommendations[:2]:  # Show first 2 recommendations
                print(f"         • {rec}")
        print()

    # Generate self-check thoughts
    print("🔍 Generating Self-Check Thoughts...")
    self_check_thoughts = await status_service.generate_self_check_thoughts(
        current_status
    )

    print(f"   Generated {len(self_check_thoughts)} self-check thoughts:")
    for i, thought in enumerate(self_check_thoughts, 1):
        print(f"   {i}. [{thought.category.upper()}] {thought.content}")
        print(f"      Confidence: {thought.confidence:.1f}, Impact: {thought.impact}")
        if thought.actionable:
            print("      🔧 Actionable: Yes")
            for rec in thought.recommendations[:2]:  # Show first 2 recommendations
                print(f"         • {rec}")
        print()

    # Get system thoughts summary
    print("📈 Generating Thoughts Summary...")
    thoughts_summary = await status_service.generate_thoughts_summary(hours=24)

    print("\n📊 Thoughts Summary (Last 24 Hours):")
    print(f"   Total Thoughts: {thoughts_summary['total_thoughts']}")
    print(f"   Version Thoughts: {thoughts_summary['version_thoughts']}")
    print(f"   Self-Check Thoughts: {thoughts_summary['self_check_thoughts']}")
    print(f"   Actionable Thoughts: {thoughts_summary['actionable_thoughts']}")
    print(f"   Average Confidence: {thoughts_summary['average_confidence']:.2f}")
    print(f"   Actionable Rate: {thoughts_summary['actionable_rate'] * 100:.1f}%")

    # Display insights
    if thoughts_summary["insights"]:
        print("\n💡 Key Insights:")
        for insight in thoughts_summary["insights"]:
            print(f"   {insight}")

    # Display impact breakdown
    print("\n⚡ Impact Breakdown:")
    for impact, count in thoughts_summary["impact_breakdown"].items():
        print(f"   {impact.capitalize()}: {count} thoughts")

    # Display category breakdown
    print("\n📂 Category Breakdown:")
    for category, count in thoughts_summary["category_breakdown"].items():
        print(f"   {category.replace('_', ' ').title()}: {count} thoughts")

    # Get thoughts by type
    print("\n🔍 Getting Version Thoughts Only...")
    version_only_thoughts = await status_service.get_system_thoughts(
        hours=24, thought_type="version"
    )
    print(f"   Found {len(version_only_thoughts)} version thoughts")

    print("\n🔍 Getting Self-Check Thoughts Only...")
    self_check_only_thoughts = await status_service.get_system_thoughts(
        hours=24, thought_type="self_check"
    )
    print(f"   Found {len(self_check_only_thoughts)} self-check thoughts")

    # Simulate a thought analysis scenario
    print("\n🎭 Simulating Thought Analysis Scenario...")

    # Create a hypothetical degraded status
    degraded_status = current_status.copy()
    degraded_status["database"]["status"] = "degraded"
    degraded_status["redis"]["status"] = "error"

    # Generate thoughts for degraded scenario
    degraded_version_thoughts = await status_service.generate_version_thoughts(
        degraded_status
    )
    degraded_self_check_thoughts = await status_service.generate_self_check_thoughts(
        degraded_status
    )

    print("   Degraded Scenario Analysis:")
    print(f"   Version Thoughts: {len(degraded_version_thoughts)}")
    print(f"   Self-Check Thoughts: {len(degraded_self_check_thoughts)}")

    # Show high-impact thoughts from degraded scenario
    high_impact_thoughts = [
        t
        for t in degraded_version_thoughts + degraded_self_check_thoughts
        if t.impact in ["high", "critical"]
    ]

    if high_impact_thoughts:
        print("\n⚠️ High-Impact Thoughts Detected:")
        for thought in high_impact_thoughts:
            print(f"   🚨 [{thought.impact.upper()}] {thought.content}")
            print(f"      Recommendations: {', '.join(thought.recommendations[:2])}")
    else:
        print("\n✅ No high-impact thoughts in current scenario")

    # Generate comprehensive report
    print("\n📋 Generating Comprehensive Status Report...")
    report_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "system_status": current_status,
        "thoughts_summary": thoughts_summary,
        "analysis": {
            "total_thoughts_generated": len(version_thoughts)
            + len(self_check_thoughts),
            "version_thoughts_count": len(version_thoughts),
            "self_check_thoughts_count": len(self_check_thoughts),
            "actionable_items_count": len(
                [t for t in version_thoughts + self_check_thoughts if t.actionable]
            ),
            "high_impact_items_count": len(
                [
                    t
                    for t in version_thoughts + self_check_thoughts
                    if t.impact in ["high", "critical"]
                ]
            ),
        },
    }

    # Save comprehensive report
    report_filename = "status_service_demo_report.json"
    with open(report_filename, "w") as f:
        json.dump(report_data, f, indent=2)

    print(f"✅ Comprehensive report saved to {report_filename}")

    # Generate markdown summary
    markdown_report = f"""# Status Service Demonstration Report

**Generated**: {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}

## System Status

- **Version**: {current_status["version_info"]["version"]}
- **Environment**: {current_status["system_info"]["environment"]}
- **Uptime**: {current_status["system_info"]["uptime_human"]}
- **Database**: {current_status["database"]["status"]}
- **Redis**: {current_status["redis"]["status"]}

## Thoughts Analysis

### Summary Statistics
- **Total Thoughts**: {thoughts_summary["total_thoughts"]}
- **Version Thoughts**: {thoughts_summary["version_thoughts"]}
- **Self-Check Thoughts**: {thoughts_summary["self_check_thoughts"]}
- **Actionable Items**: {thoughts_summary["actionable_thoughts"]}
- **Average Confidence**: {thoughts_summary["average_confidence"]:.2f}

### Key Insights
{chr(10).join(f"- {insight}" for insight in thoughts_summary["insights"])}

### Impact Breakdown
{chr(10).join(f"- **{impact.capitalize()}**: {count}" for impact, count in thoughts_summary["impact_breakdown"].items())}

### Category Breakdown
{chr(10).join(f"- **{category.replace('_', ' ').title()}**: {count}" for category, count in thoughts_summary["category_breakdown"].items())}

## Sample Thoughts

### Version Thoughts
{chr(10).join(f"- **{thought.category.title()}**: {thought.content}" for thought in version_thoughts[:3])}

### Self-Check Thoughts
{chr(10).join(f"- **{thought.category.title()}**: {thought.content}" for thought in self_check_thoughts[:3])}

---

*Report generated by Enhanced Status Service with Version Thoughts & Self-Check Thoughts*
"""

    # Save markdown report
    markdown_filename = "status_service_demo_report.md"
    with open(markdown_filename, "w") as f:
        f.write(markdown_report)

    print(f"✅ Markdown report saved to {markdown_filename}")

    # Final summary
    print("\n🎉 Status Service Demonstration Complete!")
    print("📊 Successfully demonstrated enhanced status service with:")
    print("   • Version thoughts generation and analysis")
    print("   • Self-check thoughts for system health monitoring")
    print("   • Comprehensive thoughts summary and insights")
    print("   • Impact and category breakdown analysis")
    print("   • Actionable recommendations and confidence scoring")
    print("   • Scenario-based thought analysis")
    print("🚀 System is ready for intelligent status monitoring!")


if __name__ == "__main__":
    asyncio.run(demonstrate_status_service())
