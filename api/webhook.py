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

# Standard Vercel serverless function handler
async def handle_webhook(request):
    """Handle HTTP request for Vercel"""
    if request.get('method') == 'GET':
        return {
            'statusCode': 200, 
            'body': 'Bot webhook is active!'
        }
    elif request.get('method') == 'POST':
        try:
            body = request.get('body', '{}')
            update_data = json.loads(body) if isinstance(body, str) else body
            
            success = await process_update(update_data)
            if success:
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

# Vercel specific handler
def handler(request, context):
    """Vercel serverless function entry point"""
    return asyncio.run(handle_webhook(request)) 