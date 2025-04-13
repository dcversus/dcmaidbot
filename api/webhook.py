from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update
import asyncio

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from handlers import categories, activities, selection, info
from middlewares.private_only import PrivateChatMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)

# Get bot token from environment variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# Make sure storage directory exists
os.makedirs("storage", exist_ok=True)

# Initialize Bot instance
bot = Bot(token=BOT_TOKEN)

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
        update = Update.model_validate(update_data)
        await dp.feed_update(bot, update)
        return True
    except Exception as e:
        logging.error(f"Error processing update: {e}")
        return False

# For Vercel serverless function
async def handle_request(request):
    if request.get('method') == 'GET':
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'text/plain'},
            'body': 'Bot webhook is active!'
        }
    elif request.get('method') == 'POST':
        try:
            update_data = json.loads(request.get('body', '{}'))
            result = await process_update(update_data)
            
            if result:
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'text/plain'},
                    'body': 'OK'
                }
            else:
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'text/plain'},
                    'body': 'Failed to process update'
                }
        except Exception as e:
            logging.error(f"Error handling request: {e}")
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'text/plain'},
                'body': f'Internal server error: {str(e)}'
            }
    else:
        return {
            'statusCode': 405,
            'headers': {'Content-Type': 'text/plain'},
            'body': 'Method not allowed'
        }

def handler(request, context):
    """Main handler for Vercel serverless function"""
    return asyncio.run(handle_request(request)) 