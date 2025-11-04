# 🎮 DC Maidbot Game Creator - Webapp

## Overview

This is a Telegram webapp mini-game creator system designed for admins. It provides a sandbox environment where dcmaidbot can write files, execute commands, and create interactive games with token-protected access.

## Features

### 🔐 Admin Authentication
- Token-based authentication system
- Secure token generation and validation
- Admin-only access control

### 🎮 Game Creation
- Interactive child-like interface
- Multiple game templates (Quiz, Story, Puzzle, Adventure)
- Real-time file editing
- Game preview and testing

### 📁 File Operations (Domik Tool)
- Safe sandboxed file operations
- File read/write capabilities
- Directory management
- JSON validation for game files

### 📊 Event System
- Real-time event collection from webapp
- Event processing for dcmaidbot
- Unread/read status management
- Comprehensive event tracking

## File Structure

```
/static/tgapp/
├── index.html          # Main webapp interface
├── style.css           # Child-like naive styling
├── app.js              # Event emitter and Telegram SDK
├── README.md           # This file
└── assets/             # Images and resources
    ├── buttons/        # Interactive button assets
    └── backgrounds/    # Playful backgrounds
```

## Usage

### For Admins

1. **Access the Webapp**: Open the webapp through Telegram or direct URL
2. **Authenticate**: Enter your admin token to access the workshop
3. **Create Games**: Choose from templates or create custom games
4. **Edit Files**: Use the Domik tool to edit game files directly
5. **Test Games**: Preview and test your creations

### For Developers

#### API Endpoints

- `POST /api/events` - Collect webapp events
- `GET /api/events` - Retrieve events for processing
- `POST /api/auth/validate` - Validate admin tokens
- `POST /api/files/read` - Read files from sandbox
- `POST /api/files/write` - Write files to sandbox
- `POST /api/files/list` - List directory contents

#### Services

- `TokenService` - Token authentication and management
- `EventService` - Event collection and processing
- `DomikService` - Safe sandbox file operations
- `DomikTool` - dcmaidbot integration tool

## Security Features

- **Token Authentication**: Secure bearer token system
- **Sandbox Isolation**: File operations restricted to safe directories
- **Input Validation**: JSON validation and file type restrictions
- **Size Limits**: File and directory size quotas
- **Path Validation**: Directory traversal prevention

## Game Templates

### Quiz Game
```json
{
  "type": "quiz",
  "title": "My Awesome Quiz",
  "questions": [
    {
      "question": "What is 2 + 2?",
      "options": ["3", "4", "5", "6"],
      "correct": 1,
      "points": 10
    }
  ]
}
```

### Story Game
```json
{
  "type": "story",
  "title": "My Adventure Story",
  "start_scene": "beginning",
  "scenes": {
    "beginning": {
      "text": "You are at the beginning of an adventure...",
      "choices": [
        {"text": "Go left", "next_scene": "left_path"},
        {"text": "Go right", "next_scene": "right_path"}
      ]
    }
  }
}
```

### Puzzle Game
```json
{
  "type": "puzzle",
  "title": "My Fun Puzzle",
  "difficulty": "medium",
  "puzzle_type": "pattern",
  "grid_size": [4, 4],
  "solution": [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 0]]
}
```

## Event Flow

1. **User Interaction**: User clicks buttons or interacts with interface
2. **Event Emission**: JavaScript emits events to `/api/events` endpoint
3. **Event Storage**: Events are stored in database via EventService
4. **Event Processing**: dcmaidbot reads events via DomikTool
5. **Response**: dcmaidbot can respond or take actions based on events

## Integration with dcmaidbot

The webapp integrates seamlessly with dcmaidbot through:

- **Event System**: Real-time communication via events
- **Domik Tool**: File operations for game creation
- **Token Service**: Shared authentication system
- **Sandbox**: Safe environment for creative experimentation

## Testing

Run tests to verify functionality:

```bash
# Unit tests for token authentication
python3 -m pytest tests/unit/test_token_auth.py -v

# E2E tests for webapp integration
python3 -m pytest tests/e2e/test_webapp_events.py -v
```

## Development Notes

- **Child-like Design**: Intentionally naive and playful UI for accessibility
- **Mobile-First**: Optimized for Telegram mobile interface
- **Progressive Enhancement**: Works with or without Telegram Web Apps SDK
- **Error Handling**: Comprehensive error handling and user feedback
- **Performance**: Optimized for mobile devices and slow connections

## Future Enhancements

- [ ] Real-time collaboration features
- [ ] Advanced game templates
- [ ] Game asset management
- [ ] Multiplayer game support
- [ ] Analytics and insights
- [ ] Export/import functionality

## Support

For issues and questions:
1. Check the console for JavaScript errors
2. Verify admin token is valid and not expired
3. Check network connectivity
4. Review event logs for processing errors

---

Made with 💜 for the DC Maidbot project!
