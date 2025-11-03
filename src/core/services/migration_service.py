"""Database migration check service."""

import logging
import sys

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy.ext.asyncio import AsyncEngine

from alembic import command  # type: ignore[attr-defined]

logger = logging.getLogger(__name__)


async def check_migrations(engine: AsyncEngine) -> bool:
    """
    Check if database migrations are up to date.

    Args:
        engine: SQLAlchemy async engine

    Returns:
        True if migrations are up to date, False otherwise

    Raises:
        SystemExit: If migrations are not up to date (prevents bot startup)
    """
    try:
        # Skip migration checks for SQLite in test mode
        # Test fixtures create tables from models using Base.metadata
        if engine.url.drivername == "sqlite+aiosqlite":
            logger.info("🧪 SQLite detected - skipping migration check (test mode)")
            logger.info("   Tables will be created by test fixtures from models")
            return True

        # Get alembic config
        alembic_cfg = Config("alembic.ini")
        script_dir = ScriptDirectory.from_config(alembic_cfg)

        # Get current revision from database
        async with engine.connect() as conn:
            current_rev = await conn.run_sync(
                lambda sync_conn: MigrationContext.configure(
                    sync_conn
                ).get_current_revision()
            )

        # Get head revision from scripts
        head_rev = script_dir.get_current_head()

        if current_rev == head_rev:
            logger.info(f"✅ Database migrations up to date: {current_rev}")
            return True
        else:
            logger.error("=" * 80)
            logger.error("❌ DATABASE MIGRATION REQUIRED")
            logger.error("=" * 80)
            logger.error(f"Current database revision: {current_rev}")
            logger.error(f"Latest migration revision: {head_rev}")
            logger.error("")
            logger.error("Please run migrations before starting the bot:")
            logger.error("")
            logger.error("    alembic upgrade head")
            logger.error("")
            logger.error("Or in Kubernetes:")
            logger.error("")
            logger.error(
                "    kubectl exec -n prod-core POD_NAME -- alembic upgrade head"
            )
            logger.error("")
            logger.error("=" * 80)

            # Exit immediately to prevent bot from starting with wrong schema
            sys.exit(1)

    except FileNotFoundError:
        logger.warning("⚠️  alembic.ini not found - skipping migration check")
        logger.warning("   (This is expected in development without migrations)")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to check migrations: {e}")
        logger.error("   Bot startup blocked for safety")
        sys.exit(1)


async def run_migrations_if_needed(engine: AsyncEngine, auto_upgrade: bool = False):
    """
    Check migrations and optionally auto-upgrade.

    Args:
        engine: SQLAlchemy async engine
        auto_upgrade: If True, automatically run migrations (use with caution!)

    Note:
        Auto-upgrade is disabled by default for safety. Production should use
        init containers or manual migration management.
    """
    if auto_upgrade:
        logger.warning("⚠️  AUTO_UPGRADE_DB=true - running migrations automatically")
        logger.warning("   This is not recommended for production!")

        try:
            alembic_cfg = Config("alembic.ini")
            command.upgrade(alembic_cfg, "head")
            logger.info("✅ Database migrations completed successfully")
        except Exception as e:
            logger.error(f"❌ Failed to run migrations: {e}")
            sys.exit(1)
    else:
        # Just check, don't auto-upgrade
        await check_migrations(engine)
