import json
import os
import sys
import logging
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

# Primary handler for Vercel serverless functions
def handler(request):
    """Handle HTTP requests for Vercel"""
    # Get request method
    method = request.get('method', '')
    
    # Support for different Vercel event formats
    if not method:
        # Try to extract method from httpMethod
        method = request.get('httpMethod', 'GET')
    
    # Get request body
    body = request.get('body', '{}')
    
    # For GET requests, return a simple status page
    if method == 'GET':
        return {
            'statusCode': 200,
            'body': 'Bot webhook is active!'
        }
    
    # For POST requests, process the Telegram update
    elif method == 'POST':
        try:
            # Parse the update data
            update_data = json.loads(body) if isinstance(body, str) else body
            
            # Process the update
            result = asyncio.run(process_update(update_data))
            
            # Return appropriate response
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
    
    # For unsupported methods, return 405 Method Not Allowed
    else:
        return {
            'statusCode': 405,
            'body': 'Method not allowed'
        }

# For local testing
if __name__ == "__main__":
    from http.server import BaseHTTPRequestHandler, HTTPServer
    
    class TestHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            result = handler({'method': 'GET'})
            self.send_response(result['statusCode'])
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(result['body'].encode())
        
        def do_POST(self):
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            
            result = handler({'method': 'POST', 'body': post_data})
            
            self.send_response(result['statusCode'])
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(result['body'].encode())
    
    # Start local test server
    port = int(os.environ.get("PORT", 8000))
    server = HTTPServer(('', port), TestHandler)
    print(f"Starting server on port {port}...")
    server.serve_forever() 