"""
DCMAIDBot - Unified Entry Point
Automatically detects and runs in the appropriate mode:
- Production webhook mode (if WEBHOOK_URL is set)
- Development webhook mode (if BOT_TOKEN is set but no WEBHOOK_URL)
- API-only mode (if no BOT_TOKEN)
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass  # dotenv not available, continue without it


from src.api import create_app
from src.core.services.database import engine
from src.core.services.metrics_service import get_metrics_service
from src.core.services.migration_service import check_migrations
from src.core.services.redis_service import redis_service
from src.utils.logger import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


def load_environment() -> dict:
    """Load and validate environment configuration."""
    # Set default DATABASE_URL if not provided
    if not os.getenv("DATABASE_URL"):
        os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./dcmaidbot.db"
        logger.info("Using default SQLite database: dcmaidbot.db")

    # Set default WEBHOOK_URL if not provided
    if not os.getenv("WEBHOOK_URL"):
        os.environ["WEBHOOK_URL"] = "/webhook"
        logger.info("Using default webhook path: /webhook")

    config = {
        "mode": "unknown",
        "features": {
            "telegram": bool(os.getenv("BOT_TOKEN")),
            "webhook": bool(
                os.getenv("BOT_TOKEN")
            ),  # Webhook available if BOT_TOKEN is set
            "api": True,  # Always available
            "metrics": bool(os.getenv("METRICS_PORT")),
            "redis": bool(os.getenv("REDIS_URL")),
            "database": True,  # Always true since we set default
        },
        "errors": [],
    }

    # Determine mode
    if os.getenv("BOT_TOKEN"):
        if os.getenv("BASE_URL"):
            config["mode"] = "production_webhook"
            logger.info("🚀 Production webhook mode detected")
        else:
            config["mode"] = "development_webhook"
            logger.info("🔧 Development mode detected (polling)")
    else:
        config["mode"] = "api_only"
        logger.info("📡 API-only mode detected")

    # Validate required configs
    if config["features"]["telegram"] and not os.getenv("ADMIN_IDS"):
        config["errors"].append("ADMIN_IDS is required when BOT_TOKEN is set")

    return config


def run_production_webhook():
    """Run in production webhook mode."""
    from aiohttp import web

    load_environment()

    # Create app
    app = create_app()

    # Setup bot with webhook
    # Note: Bot setup is handled by aiogram automatically based on WEBHOOK_URL env var

    # If WEBHOOK_FULL_URL is set (constructed from BASE_URL + WEBHOOK_URL), use it
    if os.getenv("WEBHOOK_FULL_URL"):
        os.environ["WEBHOOK_URL"] = os.getenv("WEBHOOK_FULL_URL")
        logger.info(f"Using webhook URL: {os.getenv('WEBHOOK_FULL_URL')}")

    # Add startup handler for async setup
    async def on_startup(app):
        await check_migrations(engine)
        await redis_service.connect()
        await get_metrics_service()

    app.on_startup.append(on_startup)

    # Start server
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))

    logger.info(f"🌐 Starting production server on {host}:{port}")

    web.run_app(app, host=host, port=port)


def run_development_webhook():
    """Run in development webhook mode."""
    from aiohttp import web

    load_environment()

    # Create app
    app = create_app()

    # Add startup handler for async setup
    async def on_startup(app):
        await check_migrations(engine)
        await redis_service.connect()
        await get_metrics_service()

    app.on_startup.append(on_startup)

    # Start server
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))

    logger.info(f"🔧 Starting development server on {host}:{port}")
    logger.info("📡 API endpoint: http://localhost:8080/call")

    web.run_app(app, host=host, port=port)


def run_api_only():
    """Run in API-only mode (no Telegram integration)."""
    from aiohttp import web

    load_environment()

    # Create app
    app = create_app()

    # Add startup handler for async setup
    async def on_startup(app):
        await check_migrations(engine)
        await redis_service.connect()

    app.on_startup.append(on_startup)

    # Start server
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))

    logger.info(f"📡 Starting API-only server on {host}:{port}")
    logger.info("Available endpoints:")
    logger.info("  POST /call - Bot API for testing")
    logger.info("  GET /health - Health check")
    logger.info("  GET /api/version - Version info")

    web.run_app(app, host=host, port=port)


async def run_polling():
    """Run in polling mode (legacy)."""
    from src.api.bot import run_bot

    logger.info("🔄 Starting bot in polling mode")

    # Check migrations - fail fast if not up to date
    await check_migrations(engine)

    # Connect services
    await redis_service.connect()
    await get_metrics_service()

    # Run bot
    await run_bot()


def print_startup_banner(config: dict) -> bool:
    """Print startup banner with configuration."""
    print("\n" + "=" * 60)
    print("🤖 DCMAIDBot - AI Assistant with Emotional Intelligence")
    print("=" * 60)

    print(f"\n📋 Mode: {config['mode']}")
    print("\n✅ Enabled Features:")
    for feature, enabled in config["features"].items():
        status = "✅" if enabled else "❌"
        print(f"  {status} {feature.capitalize()}")

    if config["errors"]:
        print("\n❌ Configuration Errors:")
        for error in config["errors"]:
            print(f"  • {error}")
        print("\n💡 Please fix these errors before starting!")
        return False

    print("\n" + "=" * 60)
    return True


def main():
    """Main entry point."""
    # Load and validate configuration
    config = load_environment()

    # Print startup banner
    if not print_startup_banner(config):
        sys.exit(1)

    # Run in appropriate mode
    try:
        if config["mode"] == "production_webhook":
            run_production_webhook()
        elif config["mode"] == "development_webhook":
            run_development_webhook()
        elif config["mode"] == "api_only":
            run_api_only()
        elif config["mode"] == "polling":
            # Only polling mode needs async context
            asyncio.run(run_polling())
        else:
            logger.error("❌ Unknown mode detected")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("\n👋 Shutting down gracefully...")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    # Check for legacy mode
    if os.getenv("USE_POLLING"):
        print("⚠️  USE_POLLING is deprecated. Use WEBHOOK_URL for webhook mode.")
        asyncio.run(run_polling())
    else:
        main()
