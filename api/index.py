import os
import json
import sys
import logging
import asyncio
from http.server import BaseHTTPRequestHandler
from aiogram import Bot, types
from dotenv import load_dotenv
from bot import setup_dispatcher, get_bot_token

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables after imports
load_dotenv()

# Get bot token from environment variables
try:
    BOT_TOKEN = get_bot_token()
except ValueError:
    logging.warning("No BOT_TOKEN found in environment, using test token")
    BOT_TOKEN = "123456789:TEST_TOKEN_FOR_LOCAL_DEVELOPMENT"

# Setup dispatcher
dp = setup_dispatcher()


async def process_update(update_data):
    """Process update from Telegram"""
    try:
        # Initialize Bot instance
        bot = Bot(token=BOT_TOKEN)

        update = types.Update.model_validate(update_data)
        await dp.feed_update(bot, update)

        # Close bot session to avoid resource leaks
        await bot.session.close()

        return True
    except Exception as e:
        logging.error(f"Error processing update: {e}")
        return False


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write("Hello from DCMAIDBOT on Vercel!".encode())
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

            try:
                loop.run_until_complete(process_update(update_data))
            finally:
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
