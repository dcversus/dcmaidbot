"""
DCMaidBot - Webhook Mode
Kawai waifu bot with webhook support for production deployment.
"""

import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from dotenv import load_dotenv

from database import engine
from handlers import admin_lessons, waifu
from handlers.call import call_handler
from handlers.event import event_handler, options_handler
from handlers.landing import landing_handler
from handlers.nudge import nudge_handler
from handlers.status import api_version_handler, health_handler
from handlers.waifu import setup_bot_commands
from middlewares.admin_only import AdminOnlyMiddleware
from services.migration_service import check_migrations
from services.redis_service import redis_service

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)


def get_bot_token() -> str:
    """Retrieves and validates the bot token."""
    token = os.getenv("BOT_TOKEN")
    if not token:
        logging.error("No BOT_TOKEN provided")
        raise ValueError("BOT_TOKEN not found")
    return token


def get_admin_ids() -> list[int]:
    """Retrieves admin IDs (NEVER logs actual IDs)."""
    admin_ids_str = os.getenv("ADMIN_IDS", "")
    admins: list[int] = []

    if not admin_ids_str:
        logging.warning("No ADMIN_IDS configured")
        return admins

    for admin_id in admin_ids_str.split(","):
        admin_id = admin_id.strip()
        if not admin_id:
            continue
        try:
            admins.append(int(admin_id))
        except ValueError:
            logging.warning("Invalid admin ID format (skipped)")

    if admins:
        logging.info(f"Loaded {len(admins)} admin(s)")
    else:
        logging.warning("No valid admin IDs found")

    return admins


def get_webhook_config():
    """Get webhook configuration."""
    return {
        "url": os.getenv("WEBHOOK_URL", ""),
        "path": os.getenv("WEBHOOK_PATH", "/webhook"),
        "host": os.getenv("WEBHOOK_HOST", "0.0.0.0"),
        "port": int(os.getenv("WEBHOOK_PORT", "8080")),
        "secret": os.getenv("WEBHOOK_SECRET", "dcmaidbot-secret-token"),
    }


def setup_dispatcher() -> Dispatcher:
    """Setup dispatcher with handlers and middleware."""
    dp = Dispatcher()

    admin_ids = get_admin_ids()
    dp.message.middleware(AdminOnlyMiddleware(admin_ids))
    dp.callback_query.middleware(AdminOnlyMiddleware(admin_ids))

    # Register routers
    dp.include_router(admin_lessons.router)  # Admin commands first
    dp.include_router(waifu.router)  # General handlers last

    return dp


async def on_startup(bot: Bot, webhook_url: str, secret: str):
    """Set webhook on startup."""
    # Check database migrations FIRST (blocks startup if not up to date)
    # Skip migration check for testing with SKIP_MIGRATION_CHECK=true
    skip_migration_check = os.getenv("SKIP_MIGRATION_CHECK", "false").lower() == "true"
    if not skip_migration_check:
        await check_migrations(engine)
    else:
        logging.warning(
            "⚠️  SKIP_MIGRATION_CHECK=true: Skipping migration check for testing"
        )

    # Connect to Redis
    await redis_service.connect()

    # Skip Telegram setup if DISABLE_TG=true
    disable_tg = os.getenv("DISABLE_TG", "false").lower() == "true"
    if disable_tg:
        logging.info("🧪 DISABLE_TG=true: Skipping Telegram webhook setup")
        return

    # Setup bot commands menu
    await setup_bot_commands(bot)
    logging.info("Bot commands menu configured")

    await bot.set_webhook(
        url=webhook_url,
        secret_token=secret,
        allowed_updates=["message", "callback_query"],
    )
    logging.info(f"Webhook set to: {webhook_url}")


async def on_shutdown(bot: Bot):
    """Cleanup on shutdown."""
    # Disconnect from Redis
    await redis_service.disconnect()

    await bot.delete_webhook()
    logging.info("Webhook deleted")


def main():
    """Main function for webhook mode."""
    token = get_bot_token()
    webhook_config = get_webhook_config()

    # Check if webhook mode is enabled OR if running without Telegram for testing
    webhook_mode = os.getenv("WEBHOOK_MODE", "false").lower() == "true"
    disable_tg = os.getenv("DISABLE_TG", "false").lower() == "true"

    if not disable_tg and (not webhook_mode or not webhook_config["url"]):
        logging.error("WEBHOOK_MODE=true and WEBHOOK_URL required for webhook mode")
        logging.error("Use bot.py for polling mode instead")
        logging.error(
            "Or set DISABLE_TG=true to run without Telegram "
            "(for /call endpoint testing)"
        )
        return

    if disable_tg:
        logging.info("🧪 DISABLE_TG=true: Running without Telegram integration")
        logging.info(
            "Only /call, /health, /nudge, and /api/version endpoints will work"
        )

    bot = Bot(token=token)
    dp = setup_dispatcher()

    # Create aiohttp application
    app = web.Application()

    # Setup webhook handler
    webhook_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=webhook_config["secret"],
    )
    webhook_handler.register(app, path=webhook_config["path"])

    # Add landing page (root path)
    app.router.add_get("/", landing_handler)
    logging.info("Landing page registered: /")

    # Add static file serving for images
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
    app.router.add_static("/static/", path=static_dir, name="static")
    logging.info(f"Static files served from: {static_dir}")

    # Add health endpoint for K8s liveness/readiness probes
    app.router.add_get("/health", health_handler)
    logging.info("Health endpoint registered: /health")

    # Add API version endpoint for landing page dynamic data
    app.router.add_get("/api/version", api_version_handler)
    logging.info("API endpoint registered: /api/version")

    # Add agent communication endpoint
    app.router.add_post("/nudge", nudge_handler)
    logging.info("Agent communication endpoint registered: /nudge")

    # Add direct bot logic testing endpoint
    app.router.add_post("/call", call_handler)
    logging.info("Direct bot logic testing endpoint registered: /call")

    # Add event collection endpoint
    app.router.add_post("/event", event_handler)
    app.router.add_options("/event", options_handler)
    logging.info("Event collection endpoint registered: /event")

    # Setup application
    setup_application(app, dp, bot=bot)

    # Set webhook on startup
    app.on_startup.append(
        lambda app: on_startup(bot, webhook_config["url"], webhook_config["secret"])
    )
    app.on_shutdown.append(lambda app: on_shutdown(bot))

    # Run web server
    logging.info(
        f"Starting webhook server on {webhook_config['host']}:{webhook_config['port']}"
    )
    web.run_app(
        app,
        host=webhook_config["host"],
        port=webhook_config["port"],
    )


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped!")
