from webhook import handler

# Vercel uses the index.py file in the api directory as the entry point
def lambda_handler(event, context):
    """AWS Lambda style handler that Vercel uses"""
    # Convert event to the format expected by our handler
    request = {
        'method': event.get('httpMethod', ''),
        'body': event.get('body', '{}'),
        'headers': event.get('headers', {}),
        'path': event.get('path', ''),
        'query': event.get('queryStringParameters', {})
    }
    
    # Call the main handler
    response = handler(request, context)
    
    # Return response in the format Lambda expects
    return response 