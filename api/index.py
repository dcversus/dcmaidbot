import json
import logging
import asyncio
from http.server import BaseHTTPRequestHandler
from aiogram import Bot, types
from bot import get_bot_token, setup_dispatcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)

bot_token = get_bot_token()
dp = setup_dispatcher()
bot = Bot(token=bot_token)


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
