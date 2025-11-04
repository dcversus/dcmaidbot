"""Simple RAG service using JSON-based embeddings.

This provides retrieval-augmented generation capabilities without requiring
pgvector or other complex vector databases.
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.memory import Memory
from .embedding_service import embedding_service

logger = logging.getLogger(__name__)


class SimpleRAGService:
    """Simple RAG service using JSON embeddings."""

    def __init__(self):
        """Initialize the RAG service."""
        self.embedding_service = embedding_service

    async def create_memory_embedding(self, db: AsyncSession, memory_id: int) -> bool:
        """Create and store embedding for a memory.

        Args:
            db: Database session
            memory_id: ID of the memory

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get the memory
            stmt = select(Memory).where(Memory.id == memory_id)
            result = await db.execute(stmt)
            memory = result.scalar_one_or_none()

            if not memory:
                logger.error(f"Memory {memory_id} not found")
                return False

            # Create embedding
            embedding = self.embedding_service.create_embedding(memory.content)
            embedding_json = self.embedding_service.format_embedding_for_db(embedding)

            # Update the memory with embedding
            memory.embedding = embedding_json
            await db.commit()

            logger.debug(f"Created embedding for memory {memory_id}")
            return True

        except Exception as e:
            logger.error(f"Error creating embedding for memory {memory_id}: {e}")
            await db.rollback()
            return False

    async def search_similar_memories(
        self,
        db: AsyncSession,
        query: str,
        user_id: Optional[int] = None,
        threshold: float = 0.3,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Search for memories similar to the query.

        Args:
            db: Database session
            query: Search query
            user_id: Optional user ID to filter memories
            threshold: Similarity threshold (0-1)
            limit: Maximum number of results

        Returns:
            List of similar memories with similarity scores
        """
        try:
            # Create embedding for query
            query_embedding = self.embedding_service.create_embedding(query)

            # Build base query
            stmt = select(Memory).where(Memory.embedding.isnot(None))

            if user_id:
                stmt = stmt.where(Memory.user_id == user_id)

            # Get all memories with embeddings
            result = await db.execute(stmt)
            memories = result.scalars().all()

            # Calculate similarities
            results = []
            for memory in memories:
                if not memory.embedding:
                    continue

                memory_embedding = self.embedding_service.parse_embedding_from_db(
                    memory.embedding
                )
                if not memory_embedding:
                    continue

                similarity = self.embedding_service.calculate_similarity(
                    query_embedding, memory_embedding
                )

                if similarity >= threshold:
                    results.append(
                        {
                            "id": memory.id,
                            "content": memory.content,
                            "category": memory.category,
                            "similarity": similarity,
                            "created_at": memory.created_at,
                            "valence": memory.valence,
                            "arousal": memory.arousal,
                            "dominance": memory.dominance,
                        }
                    )

            # Sort by similarity and limit
            results.sort(key=lambda x: x["similarity"], reverse=True)
            return results[:limit]

        except Exception as e:
            logger.error(f"Error searching similar memories: {e}")
            return []

    async def batch_create_embeddings(self, db: AsyncSession, limit: int = 100) -> int:
        """Create embeddings for memories that don't have them.

        Args:
            db: Database session
            limit: Maximum number of memories to process

        Returns:
            Number of embeddings created
        """
        try:
            # Get memories without embeddings
            stmt = select(Memory).where(Memory.embedding.is_(None)).limit(limit)
            result = await db.execute(stmt)
            memories = result.scalars().all()

            count = 0
            for memory in memories:
                success = await self.create_memory_embedding(db, memory.id)
                if success:
                    count += 1

            logger.info(f"Created {count} new embeddings")
            return count

        except Exception as e:
            logger.error(f"Error in batch embedding creation: {e}")
            return 0

    async def get_embedding_stats(self, db: AsyncSession) -> Dict[str, Any]:
        """Get statistics about embeddings in the database.

        Args:
            db: Database session

        Returns:
            Dictionary with embedding statistics
        """
        try:
            # Total memories
            total_stmt = select(func.count(Memory.id))
            total_result = await db.execute(total_stmt)
            total_memories = total_result.scalar()

            # Memories with embeddings
            embed_stmt = select(func.count(Memory.id)).where(
                Memory.embedding.isnot(None)
            )
            embed_result = await db.execute(embed_stmt)
            embedded_memories = embed_result.scalar()

            # Calculate percentage
            percentage = (
                (embedded_memories / total_memories * 100) if total_memories > 0 else 0
            )

            return {
                "total_memories": total_memories,
                "embedded_memories": embedded_memories,
                "embedding_coverage": round(percentage, 2),
                "pending_embeddings": total_memories - embedded_memories,
            }

        except Exception as e:
            logger.error(f"Error getting embedding stats: {e}")
            return {
                "total_memories": 0,
                "embedded_memories": 0,
                "embedding_coverage": 0,
                "pending_embeddings": 0,
            }

    async def delete_embedding(self, db: AsyncSession, memory_id: int) -> bool:
        """Delete embedding for a memory.

        Args:
            db: Database session
            memory_id: ID of the memory

        Returns:
            True if successful, False otherwise
        """
        try:
            stmt = select(Memory).where(Memory.id == memory_id)
            result = await db.execute(stmt)
            memory = result.scalar_one_or_none()

            if not memory:
                return False

            memory.embedding = None
            await db.commit()

            logger.debug(f"Deleted embedding for memory {memory_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting embedding for memory {memory_id}: {e}")
            await db.rollback()
            return False

    async def rebuild_all_embeddings(self, db: AsyncSession) -> int:
        """Rebuild all embeddings (useful after changing embedding model).

        Args:
            db: Database session

        Returns:
            Number of embeddings rebuilt
        """
        try:
            # Clear all existing embeddings
            stmt = select(Memory).where(Memory.embedding.isnot(None))
            result = await db.execute(stmt)
            memories = result.scalars().all()

            count = 0
            for memory in memories:
                embedding = self.embedding_service.create_embedding(memory.content)
                memory.embedding = self.embedding_service.format_embedding_for_db(
                    embedding
                )
                count += 1

            await db.commit()
            logger.info(f"Rebuilt {count} embeddings")
            return count

        except Exception as e:
            logger.error(f"Error rebuilding embeddings: {e}")
            await db.rollback()
            return 0


# Global instance
simple_rag_service = SimpleRAGService()
