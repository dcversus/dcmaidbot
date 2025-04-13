import json
import os
import sys
import logging
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update
from http import HTTPStatus

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

def handler(event, context):
    """Vercel serverless function handler"""
    try:
        # Log the event for debugging
        logging.info(f"Received event: {event}")
        
        # Get HTTP method
        method = event.get('httpMethod', 'GET') 
        logging.info(f"HTTP Method: {method}")
        
        # For GET requests, return a simple status page
        if method == 'GET':
            logging.info("Processing GET request")
            return {
                'statusCode': 200,
                'body': 'Bot webhook is active!'
            }
        
        # For POST requests, process the Telegram update
        elif method == 'POST':
            logging.info("Processing POST request")
            
            # Parse request body
            body = event.get('body', '{}')
            logging.info(f"Request body: {body[:100]}...")  # Log first 100 chars
            
            update_data = json.loads(body) if isinstance(body, str) else body
            logging.info(f"Update ID: {update_data.get('update_id', 'unknown')}")
            
            # Process the update using asyncio
            logging.info("Running update processing")
            result = asyncio.run(process_update(update_data))
            logging.info(f"Processing result: {result}")
            
            # Return response based on result
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
        
        # For other methods, return method not allowed
        else:
            logging.info(f"Unsupported method: {method}")
            return {
                'statusCode': 405,
                'body': 'Method not allowed'
            }
    except Exception as e:
        # Catch and log any unexpected errors
        logging.error(f"Unhandled exception in handler: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': f'Internal server error: {str(e)}'
        } 