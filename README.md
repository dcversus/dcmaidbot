# DCMaid Bot

A Telegram bot for creating pools of activities with a fair random selection mechanism. Perfect for teams or groups who need to assign tasks or activities fairly.

## Features

- **Pool Management**: Create, join, exit, and view pools
- **Activity Management**: Add and list activities within pools
- **Smart Selection**: Fair and random selection of activities with penalty system
- **Invitation System**: Only pool creators can invite other users to their pools
- **Penalty System**: Ensures all activities are used equally over time

## Technical Details

- **Language**: Python 3.9+
- **Framework**: aiogram 3.x (Telegram Bot API)
- **Storage**: JSON file-based storage
- **Deployment**: Vercel serverless functions

## Project Structure

```
dcmaidbot/
├── api/                  # Vercel serverless functions
├── handlers/             # Command and callback handlers
├── middlewares/          # Request processing middlewares
├── models/               # Data models
├── services/             # Business logic and utilities
├── storage/              # Data storage
├── tests/                # Test files
├── .env                  # Environment variables (not in repo)
├── .env.example          # Example environment file
├── .gitignore            # Git ignore file
├── bot.py                # Bot entry point for local development
├── requirements.txt      # Python dependencies
└── README.md             # This file
```

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/dcmaidbot.git
   cd dcmaidbot
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file with your bot token:
   ```
   BOT_TOKEN=your_telegram_bot_token_here
   DEBUG=False
   ```

4. Run the bot:
   ```
   python bot.py
   ```

## Bot Commands

- `/start` - Initialize the bot and show quick guide
- `/help` - Display help information
- `/create_pool` - Create a new activity pool
- `/join_pool` - Join an existing pool with an invite code
- `/invite` - Generate invite codes for your created pools (only creators can invite)
- `/exit_pool` - Leave a pool you're participating in
- `/my_pools` - List all pools you're participating in
- `/add_activity` - Add a new activity to a pool
- `/list_activities` - List all activities in a pool
- `/select` - Select a random activity from the pool
- `/pool_info` - Display information about a pool
- `/penalties` - Show and manage penalties for activities

## Development

For local development:

```
python bot.py
```

To test the Vercel serverless function locally:

```
python test_vercel_handler.py
```

## Vercel Deployment

1. Make sure your `vercel.json` file is correctly configured:
   ```json
   {
     "version": 2,
     "builds": [
       { 
         "src": "api/*.py", 
         "use": "@vercel/python",
         "config": {
           "maxLambdaSize": "15mb",
           "runtime": "python3.9"
         }
       }
     ],
     "routes": [
       { "src": "/", "dest": "/api/index.py" },
       { "src": "/webhook", "dest": "/api/webhook.py" },
       { "src": "/(.*)", "dest": "/api/index.py" }
     ]
   }
   ```

2. Create a Vercel account and install the Vercel CLI:
   ```
   npm install -g vercel
   ```

3. Login to Vercel:
   ```
   vercel login
   ```

4. Set up your environment variables in the Vercel dashboard:
   - Go to your project settings
   - Navigate to "Environment Variables"
   - Add `BOT_TOKEN=your_telegram_bot_token_here`

5. Deploy to Vercel:
   ```
   vercel
   ```

6. Verify and set the webhook URL (using the newly deployed URL):
   ```
   python verify_webhook.py --test https://your-project.vercel.app/webhook
   python verify_webhook.py --set https://your-project.vercel.app/webhook
   ```

7. Check if the webhook is properly set:
   ```
   python verify_webhook.py --info
   ```

## Troubleshooting Vercel Deployment

If you encounter issues with your Vercel deployment:

1. Check Vercel logs in the Vercel dashboard
2. Make sure your webhook URL is accessible - use `verify_webhook.py --test URL`
3. Ensure your bot token is properly set in environment variables
4. Try using the `/webhook` endpoint specifically (it's a simpler endpoint)
5. Check your vercel.json configuration to ensure there are no syntax errors
6. Try visiting your Vercel deployment URL directly in a browser to check if it's accessible
7. For storage issues, you might need to use a different storage approach for Vercel (like a database)

## Webhook Management

The `verify_webhook.py` script provides several useful commands:

```
# Show current webhook info
python verify_webhook.py --info

# Test if a webhook URL is accessible
python verify_webhook.py --test https://your-project.vercel.app/webhook

# Set a new webhook URL
python verify_webhook.py --set https://your-project.vercel.app/webhook

# Delete the current webhook
python verify_webhook.py --delete
```

## Testing

Run tests with:

```
pytest tests/
```

## License

This project is licensed under the MIT License. 