import os
import json
import sys
import logging
import asyncio
from http.server import BaseHTTPRequestHandler
from aiogram import Bot, types
from dotenv import load_dotenv

# Import setup functions from bot.py first
# Append path *after* attempting local imports
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
try:
    from bot import get_bot_token, setup_dispatcher
except ImportError:
    # If running directly in api/, add parent dir to path and retry
    logging.warning("Could not import 'bot' directly, adding parent directory to path.")
    sys.path.append(APP_DIR)
    from bot import get_bot_token, setup_dispatcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)

# Load environment variables first
load_dotenv()

# Add parent directory to path to import modules (Moved up)
# sys.path.append(APP_DIR)

# Import setup functions from bot.py (Moved up)
# from bot import get_bot_token, setup_dispatcher

# Get Bot Token and setup Dispatcher ONCE at module level
try:
    BOT_TOKEN = get_bot_token()
    dp = setup_dispatcher()
    # Initialize Bot instance ONCE
    bot = Bot(token=BOT_TOKEN)
except ValueError as e:
    logging.critical(f"Failed to initialize bot: {e}")
    # Handle critical error appropriately - maybe exit or prevent handler setup
    BOT_TOKEN = None
    dp = None
    bot = None
except Exception as e:
    logging.critical(f"Unexpected error during bot initialization: {e}")
    BOT_TOKEN = None
    dp = None
    bot = None


async def process_update(update_data):
    """Process update from Telegram using the pre-configured bot and dispatcher."""
    if not bot or not dp:
        logging.error("Bot or Dispatcher not initialized, cannot process update.")
        return False
    try:
        update = types.Update.model_validate(update_data)
        # Use the existing bot and dp instances
        await dp.feed_update(bot=bot, update=update)
        return True
    except Exception as e:
        logging.error(f"Error processing update: {e}")
        return False


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write("Hello from DCMaidBot webhook!".encode())
        return

    def do_POST(self):
        if not bot or not dp:
            logging.error("Bot/Dispatcher not ready, rejecting POST request.")
            self.send_response(500)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write("Bot not initialized".encode())
            return

        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length)

        try:
            update_data = json.loads(post_data.decode("utf-8"))
            logging.info(f"Received update via webhook: {update_data.get('update_id')}")

            # Process the update asynchronously
            # Avoid creating new loops if possible, depends on Vercel env
            asyncio.run(process_update(update_data))

            # Send response immediately (Telegram doesn't wait for processing)
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write("OK".encode())

        except json.JSONDecodeError as e:
            logging.error(f"Error decoding JSON: {e}")
            self.send_response(400)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write("Bad Request: Invalid JSON".encode())
        except Exception as e:
            logging.error(f"Error processing webhook: {e}")
            # Avoid sending 500 if possible, Telegram might retry
            # Still send OK if we can, log the error server-side.
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            # Acknowledge receipt even if processing fails later
            self.wfile.write("OK".encode())
