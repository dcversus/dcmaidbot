# DCMaid Bot

A Telegram bot for creating pools of activities with a fair random selection mechanism. Perfect for teams or groups who need to assign tasks or activities fairly.

## Features

- **Pool Management**: Create, join, exit, and view pools
- **Activity Management**: Add and list activities (including text and images) within pools
- **Smart Selection**: Fair and random selection of activities with penalty system
- **Invitation System**: Only pool creators can invite other users to their pools
- **Penalty System**: Ensures all activities are used equally over time
- **Media Support**: Add images to activities for richer content

## Technical Details

- **Language**: Python 3.9+
- **Framework**: aiogram 3.x (Telegram Bot API)
- **Linting**: Ruff
- **Storage**: JSON file-based storage / Redis storage (configurable via `REDIS_URL` env var)
- **Deployment**: Vercel serverless functions (optional)

## Project Structure

```
dcmaidbot/
├── api/                  # Vercel serverless functions
├── handlers/             # Command and callback handlers
├── middlewares/          # Request processing middlewares
├── models/               # Data models (Pydantic)
├── services/             # Business logic and utilities
├── tests/                # Pytest test files
├── .env                  # Environment variables (not in repo)
├── .env.example          # Example environment file
├── .gitignore            # Git ignore file
├── bot.py                # Bot entry point for local development
├── requirements.txt      # Python dependencies
├── ruff.toml             # Ruff linter configuration
├── package.json          # For Vercel deployment
├── vercel.json           # Vercel configuration (optional)
└── README.md             # This file
```

## Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/yourusername/dcmaidbot.git # Replace with your repo URL
    cd dcmaidbot
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**
    - Copy `.env.example` to `.env`:
      ```bash
      cp .env.example .env
      ```
    - Edit `.env` and add your Telegram Bot Token:
      ```env
      BOT_TOKEN=your_telegram_bot_token_here
      # REDIS_URL=redis://user:password@host:port # Optional: Uncomment and set if using Redis
      ```

## Running the Bot Locally

1.  **Activate the virtual environment** (if not already active):
    ```bash
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

2.  **Run the bot:**
    ```bash
    python bot.py
    ```
    The bot will start polling for updates. Data will be saved in `storage/storage.json` by default, or use Redis if `REDIS_URL` is set.

## Bot Commands

- `/start` - Initialize the bot and show quick guide
- `/help` - Display help information
- `/create_pool` - Create a new activity pool
- `/join_pool [код]` - Join an existing pool using an invite code
- `/invite` - Generate invite codes for pools you created
- `/exit_pool` - Leave a pool you are participating in
- `/my_pools` - List all pools you are participating in
- `/add_activity` - Add a new activity (text or text+image) to a pool
- `/list_activities` - List all activities in a pool
- `/remove_activity` - Remove an activity from a pool
- `/select [номер_пула]` - Select a random activity from one or more pools (specify pool numbers like `1` or `1,3`)
- `/pool_info [название_пула]` - Display detailed information about a pool
- `/penalties` - Show penalty information for users in your pools

## Development

### Running Tests

1.  Activate the virtual environment:
    ```bash
    source venv/bin/activate # On Windows use `venv\Scripts\activate`
    ```
2.  Run pytest:
    ```bash
    pytest tests/
    ```

### Linting

This project uses [Ruff](https://docs.astral.sh/ruff/) for linting and formatting.

1.  Activate the virtual environment:
    ```bash
    source venv/bin/activate # On Windows use `venv\Scripts\activate`
    ```
2.  Check for linting issues:
    ```bash
    ruff check .
    ```
3.  Automatically fix fixable issues:
    ```bash
    ruff check . --fix
    ```
4.  Format code:
    ```bash
    ruff format .
    ```

## Vercel Deployment (Optional)

This bot can be deployed as a serverless function on Vercel using webhooks.

1.  **Install Vercel CLI:**
    ```bash
    npm install -g vercel
    ```

2.  **Login to Vercel:**
    ```bash
    vercel login
    ```

3.  **Configure Environment Variables in Vercel:**
    - Go to your project settings on the Vercel dashboard.
    - Navigate to "Environment Variables".
    - Add `BOT_TOKEN` with your Telegram Bot Token.
    - Optionally, add `REDIS_URL` if you want to use Redis for storage on Vercel.

4.  **Deploy:**
    ```bash
    vercel
    ```
    Vercel will provide you with deployment URLs.

5.  **Set the Webhook:**
    Use the `verify_webhook.py` script (remember to activate your venv first) to set the webhook URL provided by Vercel. Make sure to use the `/api/webhook` endpoint.
    ```bash
    source venv/bin/activate
    python verify_webhook.py --set https://your-deployment-url.vercel.app/api/webhook
    ```

6.  **Verify Webhook:**
    ```bash
    python verify_webhook.py --info
    python verify_webhook.py --test https://your-deployment-url.vercel.app/api/webhook
    ```

### Webhook Management Script

The `verify_webhook.py` script helps manage the Telegram webhook:

```bash
# Activate venv first!
source venv/bin/activate

# Show current webhook info
python verify_webhook.py --info

# Test if a webhook URL is accessible
python verify_webhook.py --test https://dcmaidbot.vercel.app/webhook

# Set a new webhook URL
python verify_webhook.py --set https://dcmaidbot.vercel.app/webhook

# Delete the current webhook
python verify_webhook.py --delete
```

## License

This project is licensed under the MIT License. 