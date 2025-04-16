#!/usr/bin/env python
"""
Test script for the Vercel serverless function handler.
This simulates Vercel's environment locally by running a simple HTTP server.
"""

import json
import threading
import time
import requests
from http.server import HTTPServer
from dotenv import load_dotenv
from api.index import handler  # Import your handler class

# Load environment variables
load_dotenv()

# Configuration
PORT = 8888  # Use a free port
SERVER_ADDRESS = ("localhost", PORT)
BASE_URL = f"http://{SERVER_ADDRESS[0]}:{SERVER_ADDRESS[1]}"

# --- Server Setup ---
_server_thread = None
_httpd = None


def start_server():
    """Starts the HTTP server in a background thread."""
    global _httpd, _server_thread
    _httpd = HTTPServer(SERVER_ADDRESS, handler)
    _server_thread = threading.Thread(target=_httpd.serve_forever)
    _server_thread.daemon = (
        True  # Allow main thread to exit even if server thread is running
    )
    _server_thread.start()
    print(f"Test server started on {BASE_URL}")
    time.sleep(0.5)  # Give server a moment to start


def stop_server():
    """Stops the HTTP server."""
    global _httpd, _server_thread
    if _httpd:
        _httpd.shutdown()
        _httpd.server_close()
        print("Test server stopped.")
    if _server_thread:
        _server_thread.join(timeout=1)


# --- Test Functions ---


def test_get_request():
    """Test a GET request to the handler"""
    print("Testing GET request...")
    try:
        response = requests.get(BASE_URL)
        response.raise_for_status()  # Raise an exception for bad status codes
        print(f"Status code: {response.status_code}")
        print(f"Body: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"GET request failed: {e}")
    print("-" * 50)


def test_post_request():
    """Test a POST request with a mock update"""
    print("Testing POST request with mock update...")

    # Simulate a simple Telegram message update
    mock_update = {
        "update_id": 12345,
        "message": {
            "message_id": 1,
            "from": {
                "id": 123456789,
                "is_bot": False,
                "first_name": "Test",
                "username": "testuser",
            },
            "chat": {
                "id": 123456789,
                "type": "private",
                "first_name": "Test",
                "username": "testuser",
            },
            "date": int(time.time()),  # Use current time
            "text": "/start",
        },
    }

    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(
            BASE_URL, headers=headers, data=json.dumps(mock_update)
        )
        response.raise_for_status()
        print(f"Status code: {response.status_code}")
        print(f"Body: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"POST request failed: {e}")

    print("-" * 50)


def test_invalid_method():
    """Test an invalid HTTP method (should be handled by BaseHTTPRequestHandler)"""
    print("Testing PUT request (invalid method)...")
    try:
        response = requests.put(
            BASE_URL
        )  # Use PUT, which your handler doesn't implement
        print(f"Status code: {response.status_code}")  # Expect 405 or similar
        print(f"Body: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"PUT request failed: {e}")
    print("-" * 50)


if __name__ == "__main__":
    print("Testing Vercel serverless function handler locally\n")
    start_server()
    try:
        # Run tests
        test_get_request()
        test_post_request()
        test_post_request()
        test_post_request()
        test_invalid_method()
    finally:
        stop_server()

    print("\nLocal handler testing completed.")
