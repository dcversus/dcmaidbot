"""Global Chat Manager service for tracking status across all chats and generating summaries."""

import asyncio
import logging
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Set

from services.chat_buffer import ChatSummary, chat_buffer
from services.llm_service import LLMService

logger = logging.getLogger(__name__)


class ActivityLevel(Enum):
    """Activity level classification."""

    VERY_HIGH = "very_high"  # >1000 messages/day
    HIGH = "high"  # 100-1000 messages/day
    MEDIUM = "medium"  # 10-100 messages/day
    LOW = "low"  # 1-10 messages/day
    INACTIVE = "inactive"  # <1 message/day


class ChatHealth(Enum):
    """Chat health status."""

    HEALTHY = "healthy"  # Normal operation
    WARNING = "warning"  # Potential issues
    CRITICAL = "critical"  # Major problems
    OPTIMIZING = "optimizing"  # Performance tuning needed


@dataclass
class GlobalChatStats:
    """Global statistics across all chats."""

    total_chats: int
    active_chats: int
    inactive_chats: int
    total_messages_today: int
    total_messages_processed: int
    average_activity: str
    bot_responses_today: int
    memory_tasks_created: int
    system_health: str
    last_update: datetime


@dataclass
class ChatStatus:
    """Detailed status for a specific chat."""

    chat_id: int
    chat_title: str
    chat_type: str
    activity_level: ActivityLevel
    message_count_today: int
    message_count_total: int
    last_activity: datetime
    admin_present: bool
    bot_responses_today: int
    average_response_time: float
    health_status: ChatHealth
    issues: List[str]
    recent_summary: str
    buffer_size: int


class GlobalChatManager:
    """Manages global chat status and generates comprehensive summaries."""

    def __init__(self):
        self.llm_service = LLMService()

        # Track global statistics
        self.global_stats = GlobalChatStats(
            total_chats=0,
            active_chats=0,
            inactive_chats=0,
            total_messages_today=0,
            total_messages_processed=0,
            average_activity=ActivityLevel.MEDIUM.value,
            bot_responses_today=0,
            memory_tasks_created=0,
            system_health=ChatHealth.HEALTHY.value,
            last_update=datetime.utcnow(),
        )

        # Per-chat detailed status
        self.chat_status: Dict[int, ChatStatus] = {}

        # Track daily metrics
        self.daily_metrics: Dict[str, Dict] = defaultdict(dict)
        self.current_date = datetime.utcnow().date()

        # Performance tracking
        self.performance_metrics = {
            "average_processing_time": 0.0,
            "memory_implicator_performance": 0.0,
            "response_flow_performance": 0.0,
            "buffer_overflow_count": 0,
            "system_errors": 0,
        }

        # Background tasks
        self._background_tasks: Set[asyncio.Task] = set()

        # Start background monitoring
        self._start_background_monitoring()

    def _start_background_monitoring(self):
        """Start background monitoring tasks."""

        # Update global stats every 5 minutes
        task = asyncio.create_task(self._periodic_stats_update())
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

        # Clean old data every hour
        task = asyncio.create_task(self._periodic_cleanup())
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

        # Generate daily summary
        task = asyncio.create_task(self._daily_summary_generation())
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

    async def update_chat_status(self, chat_id: int, chat_summary: ChatSummary):
        """Update status for a specific chat."""

        datetime.utcnow()

        # Calculate activity level
        activity_level = self._calculate_activity_level(chat_summary)

        # Determine health status
        health_status, issues = self._assess_chat_health(chat_summary)

        # Update or create chat status
        if chat_id not in self.chat_status:
            self.chat_status[chat_id] = ChatStatus(
                chat_id=chat_id,
                chat_title=chat_summary.chat_title,
                chat_type=chat_summary.chat_type.value,
                activity_level=activity_level,
                message_count_today=0,
                message_count_total=chat_summary.message_count,
                last_activity=chat_summary.last_activity,
                admin_present=chat_summary.admin_present,
                bot_responses_today=0,
                average_response_time=0.0,
                health_status=health_status,
                issues=issues,
                recent_summary=chat_summary.last_summary or "",
                buffer_size=chat_summary.buffer_size,
            )
        else:
            status = self.chat_status[chat_id]
            status.last_activity = chat_summary.last_activity
            status.message_count_total = chat_summary.message_count
            status.buffer_size = chat_summary.buffer_size
            status.admin_present = chat_summary.admin_present
            status.recent_summary = chat_summary.last_summary or ""
            status.activity_level = activity_level
            status.health_status = health_status
            status.issues = issues

    def _calculate_activity_level(self, chat_summary: ChatSummary) -> ActivityLevel:
        """Calculate activity level based on message patterns."""

        # Simple heuristic based on buffer size and message count
        if chat_summary.buffer_size > 100:
            return ActivityLevel.VERY_HIGH
        elif chat_summary.buffer_size > 50:
            return ActivityLevel.HIGH
        elif chat_summary.buffer_size > 10:
            return ActivityLevel.MEDIUM
        elif chat_summary.buffer_size > 0:
            return ActivityLevel.LOW
        else:
            return ActivityLevel.INACTIVE

    def _assess_chat_health(
        self, chat_summary: ChatSummary
    ) -> tuple[ChatHealth, List[str]]:
        """Assess the health of a chat and identify issues."""

        issues = []

        # Check for potential issues
        if chat_summary.buffer_size > 150:
            issues.append("High message volume - potential buffer overflow")
            health = ChatHealth.WARNING
        elif chat_summary.buffer_size > 200:
            issues.append("Critical message volume - system overload")
            health = ChatHealth.CRITICAL
        elif not chat_summary.admin_present and chat_summary.message_count > 50:
            issues.append("High activity without admin supervision")
            health = ChatHealth.WARNING
        else:
            health = ChatHealth.HEALTHY

        # Check for processing delays
        if chat_summary.needs_processing:
            issues.append("Pending processing required")
            if health == ChatHealth.HEALTHY:
                health = ChatHealth.OPTIMIZING

        return health, issues

    async def _periodic_stats_update(self):
        """Periodically update global statistics."""

        while True:
            try:
                await asyncio.sleep(300)  # 5 minutes

                # Get current stats from all services
                buffer_stats = await chat_buffer.get_global_status()

                # Update global stats
                self.global_stats.total_chats = len(self.chat_status)
                self.global_stats.active_chats = buffer_stats["active_chats"]
                self.global_stats.total_messages_processed = buffer_stats[
                    "total_messages_processed"
                ]
                self.global_stats.total_messages_today = self._count_messages_today()
                self.global_stats.last_update = datetime.utcnow()

                # Calculate average activity
                activity_counts = defaultdict(int)
                for status in self.chat_status.values():
                    activity_counts[status.activity_level.value] += 1

                if activity_counts:
                    most_common = max(activity_counts.items(), key=lambda x: x[1])
                    self.global_stats.average_activity = most_common[0]

                # Assess system health
                self.global_stats.system_health = self._assess_system_health()

                logger.debug(f"Updated global stats: {self.global_stats}")

            except Exception as e:
                logger.error(f"Error updating global stats: {e}")

    async def _periodic_cleanup(self):
        """Periodically clean up old data."""

        while True:
            try:
                await asyncio.sleep(3600)  # 1 hour

                cutoff = datetime.utcnow() - timedelta(days=7)

                # Clean up old daily metrics
                old_dates = [
                    date
                    for date in self.daily_metrics.keys()
                    if datetime.strptime(date, "%Y-%m-%d").date() < cutoff.date()
                ]
                for date in old_dates:
                    del self.daily_metrics[date]

                # Clean up inactive chat status
                inactive_chats = [
                    chat_id
                    for chat_id, status in self.chat_status.items()
                    if status.last_activity < cutoff
                ]
                for chat_id in inactive_chats:
                    del self.chat_status[chat_id]

                logger.info(f"Cleaned up data for {len(inactive_chats)} inactive chats")

            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")

    async def _daily_summary_generation(self):
        """Generate daily summary of all chat activity."""

        while True:
            try:
                # Wait until next day
                now = datetime.utcnow()
                tomorrow = now.replace(
                    hour=0, minute=0, second=0, microsecond=0
                ) + timedelta(days=1)
                sleep_seconds = (tomorrow - now).total_seconds()
                await asyncio.sleep(sleep_seconds)

                # Generate daily summary
                await self._generate_daily_summary()

                # Update current date
                self.current_date = datetime.utcnow().date()

            except Exception as e:
                logger.error(f"Error generating daily summary: {e}")

    async def _generate_daily_summary(self):
        """Generate a comprehensive daily summary."""

        date_str = self.current_date.strftime("%Y-%m-%d")

        # Collect all daily data
        daily_data = {
            "date": date_str,
            "global_stats": asdict(self.global_stats),
            "chat_status": {
                chat_id: asdict(status) for chat_id, status in self.chat_status.items()
            },
            "performance_metrics": self.performance_metrics,
            "top_active_chats": self._get_top_active_chats(),
            "system_issues": self._collect_system_issues(),
        }

        # Store daily metrics
        self.daily_metrics[date_str] = daily_data

        # Generate summary text
        summary_text = await self._create_daily_summary_text(daily_data)

        logger.info(f"Generated daily summary for {date_str}")
        return summary_text

    def _count_messages_today(self) -> int:
        """Count total messages processed today."""

        today = datetime.utcnow().date()
        total = 0

        for status in self.chat_status.values():
            if status.last_activity.date() == today:
                total += status.message_count_today

        return total

    def _assess_system_health(self) -> str:
        """Assess overall system health."""

        if not self.chat_status:
            return ChatHealth.HEALTHY.value

        # Count health statuses
        health_counts = defaultdict(int)
        for status in self.chat_status.values():
            health_counts[status.health_status.value] += 1

        total_chats = len(self.chat_status)

        # If any critical issues, system is critical
        if health_counts.get(ChatHealth.CRITICAL.value, 0) > 0:
            return ChatHealth.CRITICAL.value

        # If many warnings, system is warning
        if health_counts.get(ChatHealth.WARNING.value, 0) > total_chats * 0.2:
            return ChatHealth.WARNING.value

        # If many optimizing, system is optimizing
        if health_counts.get(ChatHealth.OPTIMIZING.value, 0) > total_chats * 0.3:
            return ChatHealth.OPTIMIZING.value

        return ChatHealth.HEALTHY.value

    def _get_top_active_chats(self, limit: int = 10) -> List[Dict]:
        """Get top most active chats."""

        sorted_chats = sorted(
            self.chat_status.items(),
            key=lambda x: x[1].message_count_today,
            reverse=True,
        )

        return [
            {
                "chat_id": chat_id,
                "title": status.chat_title,
                "messages_today": status.message_count_today,
                "activity_level": status.activity_level.value,
            }
            for chat_id, status in sorted_chats[:limit]
        ]

    def _collect_system_issues(self) -> List[str]:
        """Collect all system issues across chats."""

        issues = []

        for chat_id, status in self.chat_status.items():
            for issue in status.issues:
                issues.append(f"Chat {chat_id} ({status.chat_title}): {issue}")

        # Add performance issues
        if self.performance_metrics["system_errors"] > 10:
            issues.append(
                f"High system error count: {self.performance_metrics['system_errors']}"
            )

        if self.performance_metrics["buffer_overflow_count"] > 5:
            issues.append(
                f"Multiple buffer overflows: {self.performance_metrics['buffer_overflow_count']}"
            )

        return issues

    async def _create_daily_summary_text(self, daily_data: Dict) -> str:
        """Create a human-readable daily summary text."""

        stats = daily_data["global_stats"]
        top_chats = daily_data["top_active_chats"]
        issues = daily_data["system_issues"]

        summary = f"""📊 **Daily Chat Summary - {daily_data["date"]}**

## Global Statistics
- **Total Chats**: {stats["total_chats"]}
- **Active Chats**: {stats["active_chats"]}
- **Messages Processed**: {stats["total_messages_processed"]}
- **Bot Responses**: {stats["bot_responses_today"]}
- **System Health**: {stats["system_health"].upper()}

## Top Active Chats
"""

        for i, chat in enumerate(top_chats[:5], 1):
            summary += f"{i}. {chat['title']}: {chat['messages_today']} messages ({chat['activity_level']})\n"

        if issues:
            summary += "\n## ⚠️ System Issues\n"
            for issue in issues[:10]:  # Limit to 10 issues
                summary += f"- {issue}\n"

        summary += f"""
## Performance Metrics
- Average Processing Time: {self.performance_metrics["average_processing_time"]:.2f}s
- Memory Implicator Performance: {self.performance_metrics["memory_implicator_performance"]:.2f}s
- System Errors: {self.performance_metrics["system_errors"]}

*Report generated by dcmaidbot global chat manager* 🤖✨"""

        return summary

    async def get_comprehensive_status(self) -> Dict:
        """Get comprehensive status of all chat operations."""

        return {
            "global_stats": asdict(self.global_stats),
            "chat_count": len(self.chat_status),
            "active_chats_24h": len(
                [
                    s
                    for s in self.chat_status.values()
                    if (datetime.utcnow() - s.last_activity).total_seconds() < 86400
                ]
            ),
            "performance_metrics": self.performance_metrics,
            "system_health": self.global_stats.system_health,
            "recent_issues": self._collect_system_issues()[:5],
            "last_update": self.global_stats.last_update.isoformat(),
        }

    async def force_status_update(self):
        """Force an immediate update of all status information."""

        logger.info("Forcing comprehensive status update")

        # Update all chat statuses
        for chat_id, summary in chat_buffer.chat_summaries.items():
            await self.update_chat_status(chat_id, summary)

        # Update global stats
        await self._periodic_stats_update()

        logger.info("Status update completed")

    def shutdown(self):
        """Clean shutdown of background tasks."""

        logger.info("Shutting down global chat manager")

        # Cancel all background tasks
        for task in self._background_tasks:
            task.cancel()

        # Wait for tasks to complete
        if self._background_tasks:
            asyncio.gather(*self._background_tasks, return_exceptions=True)


# Global instance - initialize lazily to avoid event loop issues
global_chat_manager = None


def get_global_chat_manager() -> GlobalChatManager:
    """Get or create the global chat manager instance."""
    global global_chat_manager
    if global_chat_manager is None:
        global_chat_manager = GlobalChatManager()
    return global_chat_manager
