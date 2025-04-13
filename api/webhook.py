"""
Simple webhook endpoint for testing Telegram webhooks.
"""
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

def handler(request):
    """
    Super simple webhook handler that just returns OK.
    This is intended to troubleshoot Vercel deployment issues.
    """
    return {
        "statusCode": 200,
        "body": "OK"
    } 