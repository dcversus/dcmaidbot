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
    """Simple handler for Vercel"""
    try:
        # Log the request method
        method = request.get('httpMethod', 'UNKNOWN')
        logging.info(f"Webhook received {method} request")
        
        # For GET requests, just return a simple message
        if method == 'GET':
            return {
                "statusCode": 200,
                "body": "Webhook endpoint is active"
            }
        
        # For POST requests, log the body and return OK
        elif method == 'POST':
            # Get the request body
            body = request.get('body', '{}')
            try:
                # Try to parse as JSON
                update = json.loads(body) if isinstance(body, str) else body
                update_id = update.get('update_id', 'unknown')
                logging.info(f"Received update ID: {update_id}")
            except Exception as e:
                logging.error(f"Failed to parse update: {str(e)}")
            
            # Always return OK
            return {
                "statusCode": 200,
                "body": "OK"
            }
        
        # For other methods, return method not allowed
        else:
            return {
                "statusCode": 405,
                "body": "Method not allowed"
            }
    except Exception as e:
        logging.error(f"Webhook error: {str(e)}")
        return {
            "statusCode": 500,
            "body": f"Error: {str(e)}"
        } 