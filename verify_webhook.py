#!/usr/bin/env python
"""
Script to verify webhook configuration with Telegram.
"""
import os
import sys
import requests
import json
import argparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get token from environment
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    print("Error: BOT_TOKEN environment variable is not set.")
    sys.exit(1)

def get_webhook_info():
    """Get current webhook information from Telegram"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
    response = requests.get(url)
    return response.json()

def set_webhook(webhook_url):
    """Set webhook URL for the bot"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
    params = {
        "url": webhook_url,
        "allowed_updates": ["message", "callback_query"]
    }
    response = requests.post(url, json=params)
    return response.json()

def delete_webhook():
    """Delete the current webhook"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"
    response = requests.get(url)
    return response.json()

def test_webhook(webhook_url):
    """Test if the webhook URL is accessible"""
    try:
        response = requests.get(webhook_url)
        return {
            "status_code": response.status_code,
            "content": response.text
        }
    except Exception as e:
        return {
            "error": str(e)
        }

def main():
    parser = argparse.ArgumentParser(description="Verify and manage Telegram webhook")
    parser.add_argument("--info", action="store_true", help="Get current webhook info")
    parser.add_argument("--set", metavar="URL", help="Set webhook URL")
    parser.add_argument("--delete", action="store_true", help="Delete current webhook")
    parser.add_argument("--test", metavar="URL", help="Test if webhook URL is accessible")
    
    args = parser.parse_args()
    
    # Default action is to show info if no arguments provided
    if len(sys.argv) == 1:
        args.info = True
    
    # Get current webhook info
    if args.info:
        info = get_webhook_info()
        print("Current webhook information:")
        print(json.dumps(info, indent=2))
    
    # Set webhook URL
    if args.set:
        webhook_url = args.set.rstrip("/")
        
        # Test if the webhook URL is accessible
        test_result = test_webhook(webhook_url)
        print(f"Testing webhook URL: {webhook_url}")
        if "error" in test_result:
            print(f"Warning: Could not access webhook URL: {test_result['error']}")
        else:
            print(f"Webhook URL is accessible. Status code: {test_result['status_code']}")
            print(f"Content: {test_result['content']}")
        
        # Ask for confirmation
        confirm = input("Do you want to set this webhook URL? (y/n): ").lower()
        if confirm == "y":
            # If webhook URL doesn't end with "/webhook", suggest adding it
            if not webhook_url.endswith("/webhook"):
                suggested_url = f"{webhook_url}/webhook"
                suggestion = input(f"Suggested webhook URL: {suggested_url}. Use this instead? (y/n): ").lower()
                if suggestion == "y":
                    webhook_url = suggested_url
            
            result = set_webhook(webhook_url)
            print("Webhook set result:")
            print(json.dumps(result, indent=2))
            
            # Show updated webhook info
            info = get_webhook_info()
            print("\nNew webhook information:")
            print(json.dumps(info, indent=2))
        else:
            print("Webhook not set.")
    
    # Delete webhook
    if args.delete:
        confirm = input("Are you sure you want to delete the current webhook? (y/n): ").lower()
        if confirm == "y":
            result = delete_webhook()
            print("Webhook delete result:")
            print(json.dumps(result, indent=2))
        else:
            print("Webhook not deleted.")
    
    # Test webhook URL
    if args.test:
        webhook_url = args.test.rstrip("/")
        test_result = test_webhook(webhook_url)
        print(f"Testing webhook URL: {webhook_url}")
        if "error" in test_result:
            print(f"Error: Could not access webhook URL: {test_result['error']}")
        else:
            print(f"Webhook URL is accessible. Status code: {test_result['status_code']}")
            print(f"Content: {test_result['content']}")

if __name__ == "__main__":
    main() 