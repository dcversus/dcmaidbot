"""Database migration check service.

SIMPLE RULES:
1. Check if migrations are up to date
2. If not up to date: FAIL with clear error message
3. Tell user exactly what to run
4. NO AUTO-MIGRATION - it's dangerous!

Works everywhere:
- ✅ Local development
- ✅ Staging
- ✅ Production
"""

import logging
import sys

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy.ext.asyncio import AsyncEngine

logger = logging.getLogger(__name__)


async def check_migrations(engine: AsyncEngine) -> bool:
    """
    Check if database migrations are up to date.

    FAILS FAST with clear error message if migrations needed.

    Returns:
        True if migrations are up to date
        False if migrations needed (exits with clear error)
    """

    # Get alembic config
    try:
        alembic_cfg = Config("alembic.ini")
        script_dir = ScriptDirectory.from_config(alembic_cfg)
    except FileNotFoundError:
        logger.warning("⚠️  alembic.ini not found - assuming fresh database")
        return True

    # Get current revision from database
    try:
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

        # Database needs migration - FAIL with clear error
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
            "    kubectl exec -n <namespace> <pod-name> -- alembic upgrade head"
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


# No other functions needed - keep it simple!
__all__ = ["check_migrations"]
