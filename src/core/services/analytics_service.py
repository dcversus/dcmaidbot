"""
Analytics & Observability Service (PRP-012)

Comprehensive metrics collection and tracking for dcmaidbot including:
- Prometheus metrics for system and business metrics
- LangSmith integration for LLM observability
- Event tracking for user interactions
- Performance monitoring and alerting
"""

import os
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    Summary,
)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models.joke import Joke
from src.core.models.memory import Memory
from src.core.models.message import Message
from src.core.models.user import User

# Initialize LangSmith if API key is available
try:
    from langsmith import Client as LangSmithClient

    LANGSMITH_AVAILABLE = True
except ImportError:
    LANGSMITH_AVAILABLE = False


@dataclass
class AnalyticsEvent:
    """Analytics event data structure"""

    event_type: str
    user_id: Optional[int]
    chat_id: Optional[int]
    metadata: Dict[str, Any]
    timestamp: datetime


class PrometheusMetrics:
    """Prometheus metrics collection for dcmaidbot"""

    # System Metrics
    message_total = Counter(
        "dcmaidbot_messages_total",
        "Total messages processed",
        ["chat_type", "language", "status"],
    )

    command_total = Counter(
        "dcmaidbot_commands_total",
        "Total commands executed",
        ["command_name", "status"],
    )

    message_processing_time = Histogram(
        "dcmaidbot_message_processing_seconds",
        "Time spent processing messages",
        ["message_type"],
        buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
    )

    active_users = Gauge(
        "dcmaidbot_active_users_total", "Number of currently active users"
    )

    # Joke System Metrics
    jokes_told_total = Counter(
        "dcmaidbot_jokes_told_total",
        "Total jokes told",
        ["joke_type", "language", "reaction"],
    )

    joke_generation_time = Histogram(
        "dcmaidbot_joke_generation_seconds",
        "Time spent generating jokes",
        ["joke_type"],
        buckets=[1.0, 2.5, 5.0, 10.0, 20.0, 60.0],
    )

    # Memory System Metrics
    memories_created_total = Counter(
        "dcmaidbot_memories_created_total", "Total memories created", ["memory_type"]
    )

    memories_retrieved_total = Counter(
        "dcmaidbot_memories_retrieved_total",
        "Total memories retrieved",
        ["retrieval_method", "success"],
    )

    # LLM Metrics
    llm_calls_total = Counter(
        "dcmaidbot_llm_calls_total",
        "Total LLM API calls",
        ["model", "endpoint", "status"],
    )

    llm_tokens_used = Summary(
        "dcmaidbot_llm_tokens_used", "LLM tokens used per call", ["model", "operation"]
    )

    llm_response_time = Histogram(
        "dcmaidbot_llm_response_seconds",
        "LLM API response time",
        ["model", "operation"],
        buckets=[0.5, 1.0, 2.5, 5.0, 10.0, 20.0, 60.0],
    )

    # Error Metrics
    error_total = Counter(
        "dcmaidbot_errors_total",
        "Total errors encountered",
        ["error_type", "component"],
    )

    # Friend & System Metrics
    friend_interactions_total = Counter(
        "dcmaidbot_friend_interactions_total",
        "Total friend interactions",
        ["friend_name", "interaction_type"],
    )

    tool_usage_total = Counter(
        "dcmaidbot_tool_usage_total", "Total tool usage", ["tool_name", "status"]
    )


class AnalyticsService:
    """Main analytics service for metrics collection and observability"""

    def __init__(self):
        self.metrics = PrometheusMetrics()
        self.langsmith_client = None
        self.enabled = os.getenv("ANALYTICS_ENABLED", "true").lower() == "true"

        # Initialize LangSmith if available
        if LANGSMITH_AVAILABLE and os.getenv("LANGSMITH_API_KEY"):
            try:
                self.langsmith_client = LangSmithClient(
                    api_key=os.getenv("LANGSMITH_API_KEY"),
                    api_url=os.getenv(
                        "LANGSMITH_API_URL", "https://api.smith.langchain.com"
                    ),
                )
                os.environ["LANGSMITH_TRACING"] = "true"
                os.environ["LANGSMITH_PROJECT"] = os.getenv(
                    "LANGSMITH_PROJECT", "dcmaidbot"
                )
            except Exception as e:
                print(f"Failed to initialize LangSmith: {e}")

    @asynccontextmanager
    async def track_message_processing(self, message_type: str = "unknown"):
        """Context manager for tracking message processing time"""
        start_time = time.time()
        try:
            yield
            self.metrics.message_processing_time.labels(
                message_type=message_type
            ).observe(time.time() - start_time)
        except Exception as e:
            self.metrics.error_total.labels(
                error_type=type(e).__name__, component="message_processing"
            ).inc()
            raise

    def track_message(
        self, chat_type: str, language: str = "en", status: str = "success"
    ):
        """Track a processed message"""
        if not self.enabled:
            return
        self.metrics.message_total.labels(
            chat_type=chat_type, language=language, status=status
        ).inc()

    def track_command(self, command_name: str, status: str = "success"):
        """Track a command execution"""
        if not self.enabled:
            return
        self.metrics.command_total.labels(
            command_name=command_name, status=status
        ).inc()

    def track_joke_told(
        self, joke_type: str, language: str = "en", reaction: str = "unknown"
    ):
        """Track a joke being told"""
        if not self.enabled:
            return
        self.metrics.jokes_told_total.labels(
            joke_type=joke_type, language=language, reaction=reaction
        ).inc()

    @asynccontextmanager
    async def track_joke_generation(self, joke_type: str):
        """Context manager for tracking joke generation time"""
        start_time = time.time()
        try:
            yield
            self.metrics.joke_generation_time.labels(joke_type=joke_type).observe(
                time.time() - start_time
            )
        except Exception as e:
            self.metrics.error_total.labels(
                error_type=type(e).__name__, component="joke_generation"
            ).inc()
            raise

    def track_memory_created(self, memory_type: str = "user"):
        """Track memory creation"""
        if not self.enabled:
            return
        self.metrics.memories_created_total.labels(memory_type=memory_type).inc()

    def track_memory_retrieved(self, retrieval_method: str, success: bool = True):
        """Track memory retrieval"""
        if not self.enabled:
            return
        self.metrics.memories_retrieved_total.labels(
            retrieval_method=retrieval_method,
            success="success" if success else "failure",
        ).inc()

    def track_llm_call(
        self,
        model: str,
        endpoint: str,
        status: str = "success",
        tokens_used: int = 0,
        response_time: float = 0.0,
    ):
        """Track LLM API call"""
        if not self.enabled:
            return

        self.metrics.llm_calls_total.labels(
            model=model, endpoint=endpoint, status=status
        ).inc()

        if tokens_used > 0:
            self.metrics.llm_tokens_used.labels(
                model=model, operation=endpoint
            ).observe(tokens_used)

        if response_time > 0:
            self.metrics.llm_response_time.labels(
                model=model, operation=endpoint
            ).observe(response_time)

    def track_friend_interaction(self, friend_name: str, interaction_type: str):
        """Track friend interaction"""
        if not self.enabled:
            return
        self.metrics.friend_interactions_total.labels(
            friend_name=friend_name, interaction_type=interaction_type
        ).inc()

    def track_tool_usage(self, tool_name: str, status: str = "success"):
        """Track external tool usage"""
        if not self.enabled:
            return
        self.metrics.tool_usage_total.labels(tool_name=tool_name, status=status).inc()

    def track_error(self, error_type: str, component: str):
        """Track an error"""
        if not self.enabled:
            return
        self.metrics.error_total.labels(
            error_type=error_type, component=component
        ).inc()

    async def update_active_users(self, db: AsyncSession):
        """Update active users gauge"""
        if not self.enabled:
            return

        try:
            # Count active users in last 24 hours
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            active_count = await db.scalar(
                select(func.count(func.distinct(Message.user_id))).where(
                    Message.created_at > cutoff_time
                )
            )
            self.metrics.active_users.set(active_count or 0)
        except Exception:
            self.track_error("database_error", "active_users_update")

    def create_langsmith_run(
        self, name: str, inputs: Dict[str, Any], tags: Optional[List[str]] = None
    ) -> Optional[str]:
        """Create a LangSmith run for tracing"""
        if not self.enabled or not self.langsmith_client:
            return None

        try:
            run = self.langsmith_client.create_run(
                name=name,
                inputs=inputs,
                project_name=os.getenv("LANGSMITH_PROJECT", "dcmaidbot"),
                tags=tags or [],
            )
            return run.id
        except Exception:
            self.track_error("langsmith_error", "run_creation")
            return None

    def end_langsmith_run(
        self, run_id: str, outputs: Dict[str, Any], error: Optional[Exception] = None
    ):
        """End a LangSmith run with results"""
        if not self.enabled or not self.langsmith_client or not run_id:
            return

        try:
            self.langsmith_client.end_run(
                run_id=run_id, outputs=outputs, error=str(error) if error else None
            )
        except Exception:
            self.track_error("langsmith_error", "run_ending")

    async def get_metrics_summary(self, db: AsyncSession) -> Dict[str, Any]:
        """Get a summary of key metrics for dashboards"""
        if not self.enabled:
            return {}

        try:
            # Basic stats
            total_messages = await db.scalar(select(func.count(Message.id)))
            total_users = await db.scalar(select(func.count(User.id)))
            total_jokes = await db.scalar(select(func.count(Joke.id)))
            total_memories = await db.scalar(select(func.count(Memory.id)))

            # Recent activity (last 24 hours)
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            recent_messages = await db.scalar(
                select(func.count(Message.id)).where(Message.created_at > cutoff_time)
            )
            recent_users = await db.scalar(
                select(func.count(func.distinct(Message.user_id))).where(
                    Message.created_at > cutoff_time
                )
            )

            return {
                "total_messages": total_messages or 0,
                "total_users": total_users or 0,
                "total_jokes": total_jokes or 0,
                "total_memories": total_memories or 0,
                "recent_messages_24h": recent_messages or 0,
                "active_users_24h": recent_users or 0,
                "langsmith_enabled": self.langsmith_client is not None,
                "analytics_enabled": self.enabled,
            }
        except Exception:
            self.track_error("database_error", "metrics_summary")
            return {}


# Global analytics instance
analytics = AnalyticsService()
