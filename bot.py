import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web
from dotenv import load_dotenv
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from database import engine, get_session
from handlers import waifu
from middlewares.admin_only import AdminOnlyMiddleware
from middlewares.analytics import AnalyticsMiddleware
from services.analytics_service import analytics
from services.domik_service import DomikService
from services.migration_service import check_migrations
from services.token_service import TokenService

# Load environment variables first
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)


def get_bot_token() -> str:
    """Retrieves and validates the bot token from environment variables."""
    token = os.getenv("BOT_TOKEN")
    if not token:
        logging.error("No BOT_TOKEN provided. Please check your .env file")
        raise ValueError("BOT_TOKEN not found in environment variables")
    return token


def get_admin_ids() -> list[int]:
    """Retrieves admin IDs from environment variables (NEVER logs actual IDs)."""
    admin_ids_str = os.getenv("ADMIN_IDS", "")
    admins: list[int] = []

    if not admin_ids_str:
        logging.warning("No ADMIN_IDS configured. Bot will not respond to anyone.")
        return admins

    # Parse comma-separated admin IDs
    for admin_id in admin_ids_str.split(","):
        admin_id = admin_id.strip()
        if not admin_id:
            continue
        try:
            admins.append(int(admin_id))
        except ValueError:
            # PRIVACY: Never log the actual ID value
            logging.warning("Invalid admin ID format detected (skipped)")

    if admins:
        logging.info(f"Loaded {len(admins)} admin(s) from ADMIN_IDS")
    else:
        logging.warning("No valid admin IDs found. Bot will not respond.")

    return admins


def setup_dispatcher() -> Dispatcher:
    """Initializes and configures the dispatcher."""
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Get admin IDs
    admin_ids = get_admin_ids()

    # Register analytics middleware (first to track all interactions)
    dp.message.outer_middleware(AnalyticsMiddleware())
    dp.callback_query.outer_middleware(AnalyticsMiddleware())
    dp.chat_join_request.outer_middleware(AnalyticsMiddleware())

    # Register the admin-only middleware
    dp.message.middleware(AdminOnlyMiddleware(admin_ids))
    dp.callback_query.middleware(AdminOnlyMiddleware(admin_ids))

    # Register waifu router
    dp.include_router(waifu.router)

    return dp


class MetricsServer:
    """HTTP server for Prometheus metrics endpoint"""

    def __init__(self):
        self.app = web.Application()
        self.setup_routes()

    def setup_routes(self):
        """Setup HTTP routes"""
        self.app.router.add_get("/metrics", self.metrics_handler)
        self.app.router.add_get("/health", self.health_handler)

    async def metrics_handler(self, request):
        """Handle Prometheus metrics scraping"""
        try:
            # Update active users gauge
            async with get_session() as db:
                await analytics.update_active_users(db)

            metrics_data = generate_latest()
            return web.Response(body=metrics_data, content_type=CONTENT_TYPE_LATEST)
        except Exception as e:
            logging.error(f"Error generating metrics: {e}")
            return web.Response(status=500)

    async def health_handler(self, request):
        """Health check endpoint"""
        return web.json_response({"status": "healthy"})


class WebappServer:
    """HTTP server for Telegram webapp game creator"""

    def __init__(self):
        self.app = web.Application()
        self.setup_routes()

    def setup_routes(self):
        """Setup HTTP routes for webapp"""
        # Static file serving for the webapp
        self.app.router.add_static("/static/", "static/", name="static")

        # Webapp main page
        self.app.router.add_get("/", self.webapp_handler)
        self.app.router.add_get("/tgapp/", self.webapp_handler)

        # API routes
        self.app.router.add_post("/api/events", self.events_handler)
        self.app.router.add_post("/api/auth/validate", self.auth_handler)

        # File operations API
        self.app.router.add_get("/api/files/list", self.list_files_handler)
        self.app.router.add_get("/api/files/read", self.read_file_handler)
        self.app.router.add_post("/api/files/write", self.write_file_handler)
        self.app.router.add_post("/api/files/create-dir", self.create_dir_handler)
        self.app.router.add_delete("/api/files/delete", self.delete_file_handler)
        self.app.router.add_get("/api/files/templates", self.get_templates_handler)

    async def webapp_handler(self, request):
        """Serve the main webapp page"""
        try:
            with open("static/tgapp/index.html", "r", encoding="utf-8") as f:
                content = f.read()
            return web.Response(
                body=content,
                content_type="text/html",
                headers={"Cache-Control": "no-cache"},
            )
        except FileNotFoundError:
            return web.Response(status=404, text="Webapp not found")
        except Exception as e:
            logging.error(f"Error serving webapp: {e}")
            return web.Response(status=500, text="Internal server error")

    async def auth_handler(self, request):
        """Handle authentication requests"""
        try:
            data = await request.json()
            token = data.get("token")

            if not token:
                return web.json_response(
                    {"success": False, "message": "Token is required"}, status=400
                )

            # Validate token with session
            async with get_session() as db:
                token_service = TokenService(db)
                admin_token = await token_service.validate_token(token)
                is_valid = admin_token is not None

            if is_valid:
                return web.json_response(
                    {"success": True, "message": "Authentication successful"}
                )
            else:
                return web.json_response(
                    {"success": False, "message": "Invalid token"}, status=401
                )

        except Exception as e:
            logging.error(f"Error in auth handler: {e}")
            return web.json_response(
                {"success": False, "message": "Authentication failed"}, status=500
            )

    async def events_handler(self, request):
        """Handle webapp events"""
        try:
            data = await request.json()
            token = request.headers.get("Authorization", "").replace("Bearer ", "")

            # Validate token with session
            async with get_session() as db:
                token_service = TokenService(db)
                admin_token = await token_service.validate_token(token)
                if not admin_token:
                    return web.json_response(
                        {"success": False, "message": "Unauthorized"}, status=401
                    )

            # Process event (you can integrate with existing EventService here)
            logging.info(f"Received webapp event: {data}")

            return web.json_response({"success": True, "message": "Event received"})

        except Exception as e:
            logging.error(f"Error in events handler: {e}")
            return web.json_response(
                {"success": False, "message": "Event processing failed"}, status=500
            )

    async def list_files_handler(self, request):
        """Handle file listing requests"""
        try:
            token = request.headers.get("Authorization", "").replace("Bearer ", "")
            path = request.query.get("path", "")

            # Validate token and get admin_id
            async with get_session() as db:
                token_service = TokenService(db)
                admin_id = await token_service.get_admin_id_from_token(token)
                if not admin_id:
                    return web.json_response(
                        {"success": False, "message": "Unauthorized"}, status=401
                    )

                domik_service = DomikService(token_service)
                result = await domik_service.list_directory(path, admin_id)
                return web.json_response(result)

        except Exception as e:
            logging.error(f"Error in list_files handler: {e}")
            return web.json_response(
                {"success": False, "message": "Failed to list files"}, status=500
            )

    async def read_file_handler(self, request):
        """Handle file read requests"""
        try:
            token = request.headers.get("Authorization", "").replace("Bearer ", "")
            path = request.query.get("path")

            if not path:
                return web.json_response(
                    {"success": False, "message": "File path is required"}, status=400
                )

            # Validate token and get admin_id
            async with get_session() as db:
                token_service = TokenService(db)
                admin_id = await token_service.get_admin_id_from_token(token)
                if not admin_id:
                    return web.json_response(
                        {"success": False, "message": "Unauthorized"}, status=401
                    )

                domik_service = DomikService(token_service)
                result = await domik_service.read_file(path, admin_id)
                return web.json_response(result)

        except Exception as e:
            logging.error(f"Error in read_file handler: {e}")
            return web.json_response(
                {"success": False, "message": "Failed to read file"}, status=500
            )

    async def write_file_handler(self, request):
        """Handle file write requests"""
        try:
            token = request.headers.get("Authorization", "").replace("Bearer ", "")
            data = await request.json()

            path = data.get("path")
            content = data.get("content", "")

            if not path:
                return web.json_response(
                    {"success": False, "message": "File path is required"}, status=400
                )

            # Validate token and get admin_id
            async with get_session() as db:
                token_service = TokenService(db)
                admin_id = await token_service.get_admin_id_from_token(token)
                if not admin_id:
                    return web.json_response(
                        {"success": False, "message": "Unauthorized"}, status=401
                    )

                domik_service = DomikService(token_service)
                result = await domik_service.write_file(path, content, admin_id)
                return web.json_response(result)

        except Exception as e:
            logging.error(f"Error in write_file handler: {e}")
            return web.json_response(
                {"success": False, "message": "Failed to write file"}, status=500
            )

    async def create_dir_handler(self, request):
        """Handle directory creation requests"""
        try:
            token = request.headers.get("Authorization", "").replace("Bearer ", "")
            data = await request.json()

            path = data.get("path")

            if not path:
                return web.json_response(
                    {"success": False, "message": "Directory path is required"},
                    status=400,
                )

            # Validate token and get admin_id
            async with get_session() as db:
                token_service = TokenService(db)
                admin_id = await token_service.get_admin_id_from_token(token)
                if not admin_id:
                    return web.json_response(
                        {"success": False, "message": "Unauthorized"}, status=401
                    )

                domik_service = DomikService(token_service)
                result = await domik_service.create_directory(path, admin_id)
                return web.json_response(result)

        except Exception as e:
            logging.error(f"Error in create_dir handler: {e}")
            return web.json_response(
                {"success": False, "message": "Failed to create directory"}, status=500
            )

    async def delete_file_handler(self, request):
        """Handle file/directory deletion requests"""
        try:
            token = request.headers.get("Authorization", "").replace("Bearer ", "")
            path = request.query.get("path")

            if not path:
                return web.json_response(
                    {"success": False, "message": "Path is required"}, status=400
                )

            # Validate token and get admin_id
            async with get_session() as db:
                token_service = TokenService(db)
                admin_id = await token_service.get_admin_id_from_token(token)
                if not admin_id:
                    return web.json_response(
                        {"success": False, "message": "Unauthorized"}, status=401
                    )

                domik_service = DomikService(token_service)
                result = await domik_service.delete_file_or_directory(path, admin_id)
                return web.json_response(result)

        except Exception as e:
            logging.error(f"Error in delete_file handler: {e}")
            return web.json_response(
                {"success": False, "message": "Failed to delete file/directory"},
                status=500,
            )

    async def get_templates_handler(self, request):
        """Handle game template requests"""
        try:
            token = request.headers.get("Authorization", "").replace("Bearer ", "")

            # Validate token and get templates
            async with get_session() as db:
                token_service = TokenService(db)
                admin_token = await token_service.validate_token(token)
                if not admin_token:
                    return web.json_response(
                        {"success": False, "message": "Unauthorized"}, status=401
                    )

                domik_service = DomikService(token_service)
                result = await domik_service.get_game_templates()
                return web.json_response(result)

        except Exception as e:
            logging.error(f"Error in get_templates handler: {e}")
            return web.json_response(
                {"success": False, "message": "Failed to get templates"}, status=500
            )

    async def start(self, host: str = "0.0.0.0", port: int = 8081):
        """Start the webapp server"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()
        logging.info(f"Webapp server started on http://{host}:{port}")
        return runner


async def main():
    """Main function to run the bot with metrics server."""
    try:
        token = get_bot_token()
    except ValueError as e:
        logging.error(e)
        return

    # Check database migrations FIRST (blocks startup if not up to date)
    await check_migrations(engine)

    bot = Bot(token=token)
    dp = setup_dispatcher()

    # Start metrics server
    metrics_port = int(os.getenv("METRICS_PORT", "8080"))
    metrics_server = MetricsServer()
    metrics_runner = await metrics_server.start(port=metrics_port)

    # Start webapp server
    webapp_port = int(os.getenv("WEBAPP_PORT", "8081"))
    webapp_server = WebappServer()
    webapp_runner = await webapp_server.start(port=webapp_port)

    try:
        # Skip pending updates and start polling
        await bot.delete_webhook(drop_pending_updates=True)
        logging.info("Starting bot polling...")
        logging.info(f"Webapp server available on port {webapp_port}")
        await dp.start_polling(bot)
    finally:
        # Cleanup servers
        await metrics_runner.cleanup()
        await webapp_runner.cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped!")
