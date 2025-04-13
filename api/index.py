import json
import os
import sys
import logging
from http.server import BaseHTTPRequestHandler
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import handlers
from handlers import categories, activities, selection, info
from middlewares.private_only import PrivateChatMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)

# Get bot token from environment variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# For testing purposes only - will be overridden by real token in production
if not BOT_TOKEN:
    logging.warning("No BOT_TOKEN found in environment, using test token")
    BOT_TOKEN = "123456789:TEST_TOKEN_FOR_LOCAL_DEVELOPMENT"

# Make sure storage directory exists
os.makedirs("storage", exist_ok=True)

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

# Vercel serverless function handler
async def handle_vercel_request(method, body_data):
    if method == 'GET':
        return {
            'statusCode': 200,
            'body': 'Bot webhook is active!'
        }
    elif method == 'POST':
        try:
            # Parse the request body
            update_data = json.loads(body_data) if isinstance(body_data, str) else body_data
            
            # Process the update
            result = await process_update(update_data)
            
            # Return response
            if result:
                return {
                    'statusCode': 200, 
                    'body': 'OK'
                }
            else:
                return {
                    'statusCode': 400,
                    'body': 'Failed to process update'
                }
        except Exception as e:
            logging.error(f"Error in webhook handler: {e}")
            return {
                'statusCode': 500,
                'body': f'Internal server error: {str(e)}'
            }
    else:
        return {
            'statusCode': 405,
            'body': 'Method not allowed'
        }

# BaseHTTPRequestHandler for local testing
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write('Bot webhook is active!'.encode())
        
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        # Parse the JSON data
        try:
            update_data = json.loads(post_data.decode('utf-8'))
            # Process the update
            result = asyncio.run(process_update(update_data))
            
            # Send response
            self.send_response(200 if result else 400)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK' if result else b'Failed to process update')
        except Exception as e:
            logging.error(f"Error in webhook handler: {e}")
            self.send_response(500)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(f'Internal server error: {str(e)}'.encode())

# Main entry point for Vercel serverless functions
def handler(event, context):
    """Handle Vercel serverless function requests"""
    try:
        # For Vercel, we need to adapt the event format
        method = event.get('httpMethod', '')
        body = event.get('body', '{}')
        
        # Run the async handler
        response = asyncio.run(handle_vercel_request(method, body))
        
        return {
            'statusCode': response.get('statusCode', 500),
            'body': response.get('body', 'Error')
        }
    except Exception as e:
        logging.error(f"Error in handler: {e}")
        return {
            'statusCode': 500,
            'body': f'Server error: {str(e)}'
        }

# For local testing
if __name__ == "__main__":
    from http.server import HTTPServer
    port = int(os.environ.get("PORT", 8000))
    server = HTTPServer(('', port), Handler)
    print(f"Starting server on port {port}...")
    server.serve_forever() 