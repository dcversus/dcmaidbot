"""
Simple logging utility for Vercel serverless functions.
This file makes it easier to debug serverless deployments.
"""

import json
import logging
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    force=True,
)


def log_request(event):
    """Log request details"""
    try:
        # Get HTTP method
        method = event.get("httpMethod", "UNKNOWN")

        # Get path
        path = event.get("path", "/")

        # Build log message
        log_message = f"Received {method} request to {path}"

        # Log headers if present
        headers = event.get("headers", {})
        if headers:
            log_message += f"\nHeaders: {json.dumps(headers, indent=2)}"

        # Log query parameters if present
        query = event.get("queryStringParameters", {})
        if query:
            log_message += f"\nQuery params: {json.dumps(query, indent=2)}"

        # Log body if present (truncated)
        body = event.get("body")
        if body:
            if isinstance(body, str) and len(body) > 200:
                log_message += f"\nBody (truncated): {body[:200]}..."
            else:
                log_message += f"\nBody: {body}"

        # Log the message
        logging.info(log_message)
    except Exception as e:
        logging.error(f"Error logging request: {str(e)}")


def log_exception(exc):
    """Log exception details"""
    logging.error(f"Exception: {str(exc)}")
    logging.error(f"Traceback: {traceback.format_exc()}")


def log_response(response):
    """Log response details"""
    status_code = response.get("statusCode", "UNKNOWN")
    body = response.get("body", "")

    logging.info(f"Responding with status {status_code}")
    if body and len(body) < 200:
        logging.info(f"Response body: {body}")
    else:
        logging.info("Response body is too large to log")


def log_info(message):
    """Log informational message"""
    logging.info(message)


def log_error(message):
    """Log error message"""
    logging.error(message)
