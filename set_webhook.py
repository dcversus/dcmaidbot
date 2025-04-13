#!/usr/bin/env python
import os
import sys
import logging
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

def main():
    """Set webhook for the bot"""
    # Get token from environment
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        logging.error("BOT_TOKEN is not set in environment variables")
        sys.exit(1)

    # Get webhook URL from command line arguments
    if len(sys.argv) < 2:
        logging.error("Usage: python set_webhook.py <webhook_url>")
        sys.exit(1)
    webhook_url = sys.argv[1]

    # Make sure the URL has no trailing slash
    webhook_url = webhook_url.rstrip('/')

    # Validate webhook URL
    if not webhook_url.startswith("https://"):
        logging.error("Webhook URL must start with https://")
        sys.exit(1)

    # Set webhook
    api_url = f"https://api.telegram.org/bot{bot_token}/setWebhook"
    params = {
        "url": webhook_url,
        "allowed_updates": ["message", "callback_query"],
    }

    try:
        logging.info(f"Setting webhook to: {webhook_url}")
        response = requests.post(api_url, json=params)
        response.raise_for_status()
        result = response.json()
        
        if result.get("ok"):
            logging.info(f"Webhook set successfully: {webhook_url}")
            logging.info(f"Response: {result}")
        else:
            logging.error(f"Failed to set webhook: {result}")
            sys.exit(1)
    except Exception as e:
        logging.error(f"Error setting webhook: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 