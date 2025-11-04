"""Database configuration and session management.

PostgreSQL only - connects to dev instance in Kubernetes cluster.
"""

import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

# Database configuration - PostgreSQL only
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://dcmaidbot:password@localhost:5432/dcmaidbot_test",
)

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("DATABASE_DEBUG", "false").lower() == "true",
    future=True,
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base model class
Base = declarative_base()


async def get_session():
    """Get a database session."""
    async with AsyncSessionLocal() as session:
        yield session
