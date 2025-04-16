#!/usr/bin/env python
import os
import logging
import asyncio
from aiohttp import web
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)

# Get bot token from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")

async def test_handler(request):
    """Simple handler to test API functionality"""
    if request.method == 'GET':
        return web.Response(text="Bot webhook is active!")
    
    elif request.method == 'POST':
        try:
            # Get request data
            update_data = await request.json()
            
            logging.info(f"Received update: {update_data}")
            
            # In a real scenario, this would process the update with the bot
            # For testing, we just acknowledge receipt
            
            return web.Response(text="OK")
        except Exception as e:
            logging.error(f"Error processing update: {e}")
            return web.Response(text=f"Error: {str(e)}", status=500)
    
    else:
        return web.Response(text="Method not allowed", status=405)

async def main():
    # Create aiohttp app
    app = web.Application()
    
    # Add routes
    app.router.add_get('/', test_handler)
    app.router.add_post('/', test_handler)
    
    # Start the server
    logging.info("Starting test server on http://localhost:8000")
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 8000)
    await site.start()
    
    print("Server started at http://localhost:8000")
    print("Press Ctrl+C to stop")
    
    # Keep the server running
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped") 