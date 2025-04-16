import json
import os
import sys
import logging
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update
from http.server import BaseHTTPRequestHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import handlers
from handlers import categories, activities, selection, info
from middlewares.private_only import PrivateChatMiddleware

# Get bot token from environment variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# For testing purposes only - will be overridden by real token in production
if not BOT_TOKEN:
    logging.warning("No BOT_TOKEN found in environment, using test token")
    BOT_TOKEN = "123456789:TEST_TOKEN_FOR_LOCAL_DEVELOPMENT"

# Make sure storage directory exists
# os.makedirs("storage", exist_ok=True)

# Initialize dispatcher with memory storage for FSM
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Register the private chat middleware
dp.message.middleware(PrivateChatMiddleware())
dp.callback_query.middleware(PrivateChatMiddleware())

# Register all routers
dp.include_router(categories.router)
dp.include_router(activities.router)
dp.include_router(selection.router)
dp.include_router(info.router)


async def process_update(update_data):
    """Process update from Telegram"""
    try:
        # Initialize Bot instance (create it here to ensure token is available)
        bot = Bot(token=BOT_TOKEN)

        update = Update.model_validate(update_data)
        await dp.feed_update(bot, update)
        return True
    except Exception as e:
        logging.error(f"Error processing update: {e}")
        return False


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write("Hello from Python on Vercel!".encode())
        return

    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length)

        try:
            update_data = json.loads(post_data.decode("utf-8"))
            logging.info(f"Received update: {update_data}")

            # Process the update asynchronously
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(process_update(update_data))
            loop.close()

            # Send response
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write("OK".encode())

        except Exception as e:
            logging.error(f"Error processing webhook: {e}")
            self.send_response(500)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(f"Error: {str(e)}".encode())
