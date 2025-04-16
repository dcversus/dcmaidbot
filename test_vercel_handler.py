#!/usr/bin/env python
"""
Test script for the Vercel serverless function handler.
This simulates Vercel's environment locally.
"""

import json
from dotenv import load_dotenv
from api.index import handler

# Load environment variables
load_dotenv()


def test_get_request():
    """Test a GET request to the handler"""
    print("Testing GET request...")
    event = {"httpMethod": "GET"}
    context = {}

    result = handler(event, context)
    print(f"Status code: {result.get('statusCode')}")
    print(f"Body: {result.get('body')}")
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
            "date": 1715013371,
            "text": "/start",
        },
    }

    event = {"httpMethod": "POST", "body": json.dumps(mock_update)}
    context = {}

    result = handler(event, context)
    print(f"Status code: {result.get('statusCode')}")
    print(f"Body: {result.get('body')}")
    print("-" * 50)


def test_invalid_method():
    """Test an invalid HTTP method"""
    print("Testing invalid HTTP method...")
    event = {"httpMethod": "PUT"}
    context = {}

    result = handler(event, context)
    print(f"Status code: {result.get('statusCode')}")
    print(f"Body: {result.get('body')}")
    print("-" * 50)


if __name__ == "__main__":
    print("Testing Vercel serverless function handler\n")

    # Run tests
    test_get_request()
    test_post_request()
    test_invalid_method()

    print("All tests completed.")
