"""
Embedding Service for Hybrid Recommendation

Converts extracted tags to text and generates vector embeddings.

Services:
1. Tag-to-text conversion for embedding
2. SiliconFlow/MiniMax embedding API integration
3. Embedding storage and retrieval
"""

import asyncio
import json
import logging
import httpx
from typing import Optional, Any
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import get_settings
from app.models.exercise import Exercise
from app.services.tag_extraction import ExtractedTags


logger = logging.getLogger(__name__)


@dataclass
class EmbeddingConfig:
    """Configuration for embedding service."""

    provider: str = "siliconflow"
    model: str = "BAAI/bge-large-zh-v1.5"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    dimensions: int = 1536


class EmbeddingService:
    """
    Service for generating embeddings from exercise tags.

    Supports multiple providers:
    - SiliconFlow BAAI/bge-large-zh-v1.5 (default)
    - MiniMax embedding API

    Usage:
        service = EmbeddingService(config)
        embedding = await service.generate_embedding("知识点：数组, 双指针...")
    """

    _client: Optional[httpx.AsyncClient] = None

    def __init__(self, config: Optional[EmbeddingConfig] = None):
        self.config = config or self._get_default_config()
        self._setup_client()

    def _get_default_config(self) -> EmbeddingConfig:
        """Get default configuration from settings."""
        settings = get_settings()
        return EmbeddingConfig(
            provider=settings.EMBEDDING_PROVIDER,
            model=settings.EMBEDDING_MODEL,
            api_key=settings.EMBEDDING_API_KEY,
            base_url=settings.EMBEDDING_BASE_URL,
            dimensions=settings.EMBEDDING_DIMENSIONS,
        )

    def _setup_client(self):
        """Setup HTTP client."""
        if EmbeddingService._client is None or EmbeddingService._client.is_closed:
            EmbeddingService._client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            )

    async def generate_embedding(
        self,
        text: str,
    ) -> Optional[list[float]]:
        """
        Generate embedding for text.

        Args:
            text: Text to embed

        Returns:
            List of floats (embedding vector) or None on failure
        """
        if not text or not self.config.api_key:
            return None

        try:
            # siliconflow uses OpenAI-compatible API
            if self.config.provider in ("openai", "minimax", "siliconflow"):
                return await self._openai_embedding(text)
            else:
                # Fallback for other providers (also use OpenAI-compatible)
                return await self._openai_embedding(text)
        except Exception as e:
            logger.error(f"[EmbeddingService] Error generating embedding: {e}")
            return None

    async def _openai_embedding(self, text: str) -> Optional[list[float]]:
        """Generate embedding using OpenAI-compatible API."""
        base_url = self.config.base_url or "https://api.siliconflow.cn/v1"

        try:
            # Build request body
            # Note: Some embedding models (like BAAI/bge-large-zh-v1.5) don't support dimensions parameter
            request_body: dict[str, Any] = {
                "model": self.config.model,
                "input": text,
            }

            # Only add dimensions for OpenAI models that support it
            # siliconflow's BGE model doesn't support custom dimensions
            if self.config.provider == "openai" and self.config.dimensions:
                request_body["dimensions"] = self.config.dimensions

            client = self._client
            if client is None:
                return None
            response = await client.post(
                f"{base_url}/embeddings",
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                },
                json=request_body,
            )
            response.raise_for_status()
            data = response.json()
            return data["data"][0]["embedding"]
        except httpx.HTTPStatusError as e:
            logger.error(f"[EmbeddingService] API error: {e.response.status_code}")
            try:
                error_detail = e.response.json()
                logger.error(f"[EmbeddingService] Error detail: {error_detail}")
            except Exception:
                logger.error(f"[EmbeddingService] Response text: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"[EmbeddingService] Error: {e}")
            return None

    async def generate_tag_embedding(
        self,
        tags: ExtractedTags,
    ) -> Optional[list[float]]:
        """
        Generate embedding from extracted tags.

        Args:
            tags: ExtractedTags object

        Returns:
            Embedding vector or None
        """
        text = tags.to_embedding_text()
        if not text:
            return None
        return await self.generate_embedding(text)

    async def batch_generate_embeddings(
        self,
        texts: list[str],
    ) -> list[Optional[list[float]]]:
        """
        Generate embeddings for multiple texts in parallel.

        Args:
            texts: List of texts to embed

        Returns:
            List of embeddings (or None for failures)
        """
        tasks = [self.generate_embedding(text) for text in texts]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        # Convert exceptions to None
        return [r if isinstance(r, list) else None for r in results]


class ExerciseEmbeddingService:
    """
    Service for managing exercise embeddings in the database.

    Handles:
    1. Generating embeddings from exercise tags
    2. Storing embeddings in the database
    3. Updating existing embeddings
    """

    def __init__(
        self,
        db: AsyncSession,
        embedding_service: Optional[EmbeddingService] = None,
    ):
        self.db = db
        self.embedding_service = embedding_service or EmbeddingService()

    async def generate_and_store_embedding(
        self,
        exercise_id: int,
    ) -> Optional[list[float]]:
        """
        Generate and store embedding for an exercise.

        Args:
            exercise_id: Exercise ID

        Returns:
            Generated embedding or None
        """
        # Get exercise
        result = await self.db.execute(
            select(Exercise).where(Exercise.id == exercise_id)
        )
        exercise = result.scalar_one_or_none()

        if not exercise:
            return None

        # Generate text from exercise content
        text = self._exercise_to_text(exercise)

        if not text:
            return None

        # Generate embedding
        embedding = await self.embedding_service.generate_embedding(text)

        if embedding:
            # Store embedding
            exercise.embedding = json.dumps(embedding)
            await self.db.commit()

        return embedding

    async def generate_tag_embedding(
        self,
        exercise_id: int,
        tags: ExtractedTags,
    ) -> Optional[list[float]]:
        """
        Generate and store tag-based embedding for an exercise.

        Args:
            exercise_id: Exercise ID
            tags: Extracted tags

        Returns:
            Generated embedding or None
        """
        result = await self.db.execute(
            select(Exercise).where(Exercise.id == exercise_id)
        )
        exercise = result.scalar_one_or_none()

        if not exercise:
            return None

        # Generate embedding from tags
        embedding = await self.embedding_service.generate_tag_embedding(tags)

        if embedding:
            exercise.tag_embedding = json.dumps(embedding)
            await self.db.commit()

        return embedding

    def _exercise_to_text(self, exercise: Exercise) -> str:
        """Convert exercise to text for embedding."""
        parts = []

        content = exercise.content or {}
        if content.get("text"):
            parts.append(content["text"])
        if content.get("description"):
            parts.append(content["description"])
        if content.get("title"):
            parts.append(content["title"])

        if exercise.knowledge_points:
            kp_list = exercise.knowledge_points
            if isinstance(kp_list, str):
                try:
                    kp_list = json.loads(kp_list)
                except Exception:
                    kp_list = []
            if kp_list:
                parts.append(f"知识点：{', '.join(kp_list)}")

        return "\n".join(parts)

    async def batch_update_embeddings(
        self,
        exercise_ids: Optional[list[int]] = None,
        limit: int = 100,
    ) -> dict:
        """
        Update embeddings for multiple exercises.

        Args:
            exercise_ids: Optional list of specific exercise IDs
            limit: Maximum number to process

        Returns:
            Stats dict with count of updated exercises
        """
        query = select(Exercise)

        if exercise_ids:
            query = query.where(Exercise.id.in_(exercise_ids))
        else:
            # Only update exercises without embeddings
            query = query.where(Exercise.embedding.is_(None))

        query = query.limit(limit)

        result = await self.db.execute(query)
        exercises = list(result.scalars().all())

        updated = 0
        failed = 0

        for ex in exercises:
            text = self._exercise_to_text(ex)
            if text:
                embedding = await self.embedding_service.generate_embedding(text)
                if embedding:
                    ex.embedding = json.dumps(embedding)
                    updated += 1
                else:
                    failed += 1
            else:
                failed += 1

        await self.db.commit()

        return {
            "total": len(exercises),
            "updated": updated,
            "failed": failed,
        }


# Singleton for embedding service
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get or create embedding service singleton."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service


def get_exercise_embedding_service(db: AsyncSession) -> ExerciseEmbeddingService:
    """Factory function for exercise embedding service."""
    return ExerciseEmbeddingService(db)
