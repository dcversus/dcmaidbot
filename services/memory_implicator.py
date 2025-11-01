"""Memory Implicator service for intelligent classification and memory creation."""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List

from services.llm_service import LLMService
from services.memory_service import MemoryService

logger = logging.getLogger(__name__)


class MemoryCategory(Enum):
    """Memory categories for classification."""

    PERSON = "person"
    EVENT = "event"
    EMOTION = "emotion"
    INTEREST = "interest"
    FACT = "fact"
    SKILL = "skill"
    GOAL = "goal"
    PROBLEM = "problem"
    LOCATION = "location"
    RELATIONSHIP = "relationship"
    DECISION = "decision"
    QUESTION = "question"
    CONFLICT = "conflict"


class ImportanceLevel(Enum):
    """Importance levels for memory classification."""

    CRITICAL = 900  # Life-changing events
    HIGH = 700  # Important relationships/milestones
    MEDIUM = 500  # Regular interactions/events
    LOW = 300  # Casual conversations
    MINIMAL = 100  # Minor details


@dataclass
class MemoryTask:
    """Represents a task for memory creation/updates."""

    task_type: str  # "create", "update", "relate"
    content: str
    category: MemoryCategory
    importance: ImportanceLevel
    user_id: int
    chat_id: int
    related_users: List[int]
    related_memories: List[int]
    metadata: Dict[str, Any]
    timestamp: datetime


@dataclass
class ChatClassification:
    """Classification of chat content."""

    chat_type: str
    primary_topics: List[str]
    participant_roles: Dict[int, str]
    emotional_tone: str
    activity_level: str
    importance_score: float
    key_entities: List[str]
    relationships: List[Dict[str, Any]]


class MemoryImplicator:
    """Intelligent memory classification and creation system."""

    def __init__(self):
        self.llm_service = LLMService()
        self.memory_service = MemoryService()
        self.batch_size = 50  # Messages to process at once
        self.max_tokens_per_batch = 50000  # Max tokens for classification LLM call

    async def process_messages(self, messages: List) -> None:
        """Process a batch of messages and create memory tasks."""

        if not messages:
            return

        logger.info(f"Processing {len(messages)} messages through memory implicator")

        try:
            # Step 1: Classify the chat content
            classification = await self._classify_chat_content(messages)

            # Step 2: Extract important segments and entities
            important_segments = await self._extract_important_segments(
                messages, classification
            )

            # Step 3: Generate memory tasks
            memory_tasks = await self._generate_memory_tasks(
                important_segments, classification
            )

            # Step 4: Execute memory tasks
            await self._execute_memory_tasks(memory_tasks)

            # Step 5: Create relationships and associations
            await self._create_relationships(memory_tasks, classification)

            logger.info(
                f"Processed {len(messages)} messages, created {len(memory_tasks)} memory tasks"
            )

        except Exception as e:
            logger.error(f"Error in memory implicator: {e}")
            raise

    async def _classify_chat_content(self, messages: List) -> ChatClassification:
        """Classify the overall content and context of the chat messages."""

        # Prepare message context for classification
        message_context = []
        participant_map = {}

        for msg in messages:
            user_name = msg.first_name or msg.username or f"User{msg.user_id}"
            participant_map[msg.user_id] = user_name

            # Truncate very long messages
            text = msg.text[:500] + "..." if len(msg.text) > 500 else msg.text
            message_context.append(f"{user_name}: {text}")

        context_text = "\n".join(message_context)

        # Determine chat type based on number of participants
        unique_users = len(set(msg.user_id for msg in messages))
        if unique_users == 2:
            chat_type = "personal"
        elif unique_users <= 5:
            chat_type = "small_group"
        else:
            chat_type = "large_group"

        # Use cheap model for classification
        prompt = f"""Analyze this chat conversation and provide classification:

Chat Type: {chat_type}
Number of Participants: {unique_users}

Conversation:
{context_text}

Provide JSON response with:
{{
    "primary_topics": ["topic1", "topic2"],
    "participant_roles": {{
        "user_id": "role_description"
    }},
    "emotional_tone": "positive/negative/neutral/mixed",
    "activity_level": "high/medium/low",
    "importance_score": 0.0-1.0,
    "key_entities": ["entity1", "entity2"],
    "relationships": [
        {{
            "from_user": user_id,
            "to_user": user_id,
            "relationship_type": "friend/family/coworker/other",
            "interaction_style": "formal/casual/intimate"
        }}
    ]
}}

Use user_ids from the conversation for participant_roles and relationships."""

        try:
            response = await self.llm_service.client.chat.completions.create(
                model="gpt-4o-mini",  # Use cheap model for classification
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                max_tokens=1000,
                temperature=0.3,
            )

            data = json.loads(response.choices[0].message.content)

            return ChatClassification(
                chat_type=chat_type,
                primary_topics=data.get("primary_topics", []),
                participant_roles={
                    int(k): v for k, v in data.get("participant_roles", {}).items()
                },
                emotional_tone=data.get("emotional_tone", "neutral"),
                activity_level=data.get("activity_level", "medium"),
                importance_score=float(data.get("importance_score", 0.5)),
                key_entities=data.get("key_entities", []),
                relationships=data.get("relationships", []),
            )

        except Exception as e:
            logger.error(f"Error classifying chat content: {e}")
            # Return basic classification
            return ChatClassification(
                chat_type=chat_type,
                primary_topics=["general"],
                participant_roles={},
                emotional_tone="neutral",
                activity_level="medium",
                importance_score=0.5,
                key_entities=[],
                relationships=[],
            )

    async def _extract_important_segments(
        self, messages: List, classification: ChatClassification
    ) -> List[Dict[str, Any]]:
        """Extract important segments from messages for memory creation."""

        # Filter messages based on importance indicators
        important_indicators = [
            "love",
            "hate",
            "important",
            "remember",
            "never forget",
            "decision",
            "choose",
            "finally",
            "success",
            "failure",
            "happy",
            "sad",
            "angry",
            "worried",
            "excited",
        ]

        segments = []

        for msg in messages:
            # Check for importance indicators
            text_lower = msg.text.lower()
            has_indicator = any(
                indicator in text_lower for indicator in important_indicators
            )

            # Check for mentions (indicates social importance)
            has_mentions = "@" in msg.text or "mention" in text_lower

            # Check for questions (may indicate important information seeking)
            is_question = "?" in msg.text

            # Check for admin messages
            is_admin = msg.is_admin

            # Determine if message is important
            is_important = (
                has_indicator
                or has_mentions
                or is_question
                or is_admin
                or classification.importance_score > 0.7
            )

            if is_important:
                segments.append(
                    {
                        "message": msg,
                        "text": msg.text,
                        "user_id": msg.user_id,
                        "timestamp": msg.timestamp,
                        "importance_factors": {
                            "has_indicator": has_indicator,
                            "has_mentions": has_mentions,
                            "is_question": is_question,
                            "is_admin": is_admin,
                        },
                    }
                )

        return segments

    async def _generate_memory_tasks(
        self, segments: List[Dict[str, Any]], classification: ChatClassification
    ) -> List[MemoryTask]:
        """Generate memory tasks from important segments."""

        tasks = []

        # Process segments in batches to handle large conversations
        for i in range(0, len(segments), 10):
            batch = segments[i : i + 10]

            # Generate tasks for this batch
            batch_tasks = await self._process_segment_batch(batch, classification)
            tasks.extend(batch_tasks)

        return tasks

    async def _process_segment_batch(
        self, segments: List[Dict[str, Any]], classification: ChatClassification
    ) -> List[MemoryTask]:
        """Process a batch of segments and generate memory tasks."""

        # Prepare batch context
        batch_text = []
        for segment in segments:
            msg = segment["message"]
            user_name = msg.first_name or msg.username or f"User{msg.user_id}"
            batch_text.append(f"{user_name}: {segment['text']}")

        context = "\n".join(batch_text)

        # Generate memory tasks using LLM
        prompt = f"""Analyze this conversation segment and create memory tasks.

Context:
Chat Type: {classification.chat_type}
Primary Topics: {", ".join(classification.primary_topics)}
Importance Score: {classification.importance_score}

Conversation Segment:
{context}

Create memory tasks in this JSON format:
{{
    "tasks": [
        {{
            "task_type": "create|update|relate",
            "content": "specific content to remember",
            "category": "person|event|emotion|interest|fact|skill|goal|problem|location|relationship|decision|question|conflict",
            "importance": 100-900,
            "related_users": [user_ids],
            "key_entities": ["entity1", "entity2"],
            "memory_reason": "why this is important to remember"
        }}
    ]
}}

Guidelines:
- Only create tasks for genuinely important information
- Use importance levels: 100-300 (minor), 300-500 (regular), 500-700 (important), 700-900 (critical)
- Focus on relationships, decisions, emotional moments, and important facts
- Don't create tasks for casual greetings or trivial conversation
- Include user_ids from the conversation"""

        try:
            response = await self.llm_service.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                max_tokens=2000,
                temperature=0.2,
            )

            data = json.loads(response.choices[0].message.content)
            tasks_data = data.get("tasks", [])

            tasks = []
            for task_data in tasks_data:
                # Get related users from the segment
                related_users = list(set(segment["user_id"] for segment in segments))

                task = MemoryTask(
                    task_type=task_data.get("task_type", "create"),
                    content=task_data.get("content", ""),
                    category=MemoryCategory(task_data.get("category", "fact")),
                    importance=ImportanceLevel(task_data.get("importance", 300)),
                    user_id=related_users[0] if related_users else 0,
                    chat_id=segments[0]["message"].chat_id,
                    related_users=related_users,
                    related_memories=[],  # Will be filled later
                    metadata={
                        "key_entities": task_data.get("key_entities", []),
                        "memory_reason": task_data.get("memory_reason", ""),
                        "classification": classification.emotional_tone,
                        "segments_count": len(segments),
                    },
                    timestamp=datetime.utcnow(),
                )
                tasks.append(task)

            return tasks

        except Exception as e:
            logger.error(f"Error generating memory tasks: {e}")
            return []

    async def _execute_memory_tasks(self, tasks: List[MemoryTask]) -> None:
        """Execute memory tasks to create/update memories."""

        for task in tasks:
            try:
                if task.task_type == "create":
                    await self._create_memory(task)
                elif task.task_type == "update":
                    await self._update_memory(task)
                elif task.task_type == "relate":
                    await self._create_relation(task)

            except Exception as e:
                logger.error(f"Error executing memory task {task.task_type}: {e}")

    async def _create_memory(self, task: MemoryTask) -> None:
        """Create a new memory from task."""

        try:
            memory = await self.memory_service.create_memory(
                full_content=task.content,
                categories=[task.category.value],
                created_by=task.user_id,
            )

            # Add metadata
            if task.metadata:
                await self.memory_service.add_memory_metadata(memory.id, task.metadata)

            logger.debug(f"Created memory {memory.id} for task")

        except Exception as e:
            logger.error(f"Error creating memory from task: {e}")

    async def _update_memory(self, task: MemoryTask) -> None:
        """Update existing memory from task."""

        # This would search for similar memories and update them
        # For now, just create a new memory
        await self._create_memory(task)

    async def _create_relation(self, task: MemoryTask) -> None:
        """Create relationships between memories."""

        # This would create relationships between existing memories
        # Implementation depends on specific requirements
        pass

    async def _create_relationships(
        self, tasks: List[MemoryTask], classification: ChatClassification
    ) -> None:
        """Create relationships and associations between memories."""

        # Find relationships between tasks
        for i, task1 in enumerate(tasks):
            for task2 in tasks[i + 1 :]:
                if self._should_create_relation(task1, task2):
                    # Create relation between memories
                    pass

    def _should_create_relation(self, task1: MemoryTask, task2: MemoryTask) -> bool:
        """Determine if a relation should be created between two tasks."""

        # Simple heuristic: same category, related users, or similar content
        same_category = task1.category == task2.category
        common_users = set(task1.related_users) & set(task2.related_users)
        similar_importance = abs(task1.importance.value - task2.importance.value) < 200

        return same_category and (common_users or similar_importance)
