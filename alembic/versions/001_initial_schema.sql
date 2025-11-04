-- Initial database schema
-- Revision ID: 001_initial_schema

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create sequences
CREATE SEQUENCE IF NOT EXISTS users_id_seq;
CREATE SEQUENCE IF NOT EXISTS messages_id_seq;
CREATE SEQUENCE IF NOT EXISTS categories_id_seq;
CREATE SEQUENCE IF NOT EXISTS jokes_id_seq;
CREATE SEQUENCE IF NOT EXISTS memories_id_seq;
CREATE SEQUENCE IF NOT EXISTS memory_links_id_seq;
CREATE SEQUENCE IF NOT EXISTS lessons_id_seq;
CREATE SEQUENCE IF NOT EXISTS stats_id_seq;
CREATE SEQUENCE IF NOT EXISTS user_relationships_id_seq;
CREATE SEQUENCE IF NOT EXISTS bot_moods_id_seq;
CREATE SEQUENCE IF NOT EXISTS events_id_seq;
CREATE SEQUENCE IF NOT EXISTS game_sessions_id_seq;
CREATE SEQUENCE IF NOT EXISTS player_states_id_seq;
CREATE SEQUENCE IF NOT EXISTS tool_executions_id_seq;
CREATE SEQUENCE IF NOT EXISTS api_keys_id_seq;

-- Create tables
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY DEFAULT nextval('users_id_seq'),
    telegram_id BIGINT NOT NULL UNIQUE,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    is_friend BOOLEAN DEFAULT FALSE,
    language_code VARCHAR(10),
    is_bot BOOLEAN DEFAULT FALSE,
    is_premium BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY DEFAULT nextval('messages_id_seq'),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    chat_id BIGINT NOT NULL,
    message_id INTEGER NOT NULL,
    text TEXT NOT NULL,
    language VARCHAR(10),
    message_type VARCHAR(20) DEFAULT 'user',
    reply_to_message_id INTEGER,
    forward_from BIGINT,
    created_at TIMESTAMP,
    UNIQUE(chat_id, message_id)
);

CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY DEFAULT nextval('categories_id_seq'),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    parent_id INTEGER REFERENCES categories(id),
    created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS jokes (
    id SERIAL PRIMARY KEY DEFAULT nextval('jokes_id_seq'),
    setup TEXT NOT NULL,
    punchline TEXT NOT NULL,
    category_id INTEGER REFERENCES categories(id),
    rating FLOAT,
    language VARCHAR(10) DEFAULT 'en',
    created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS memories (
    id SERIAL PRIMARY KEY DEFAULT nextval('memories_id_seq'),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    category VARCHAR(100),
    tags TEXT,
    valence FLOAT,
    arousal FLOAT,
    dominance FLOAT,
    admin_id BIGINT,
    chat_id BIGINT,
    message_id INTEGER,
    embedding TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS memory_links (
    id SERIAL PRIMARY KEY DEFAULT nextval('memory_links_id_seq'),
    source_memory_id INTEGER NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
    target_memory_id INTEGER NOT NULL REFERENCES memories(id) ON DELETE CASCADE,
    link_type VARCHAR(50) DEFAULT 'related',
    strength FLOAT DEFAULT 1.0,
    created_by BIGINT,
    created_at TIMESTAMP,
    UNIQUE(source_memory_id, target_memory_id)
);

CREATE TABLE IF NOT EXISTS lessons (
    id SERIAL PRIMARY KEY DEFAULT nextval('lessons_id_seq'),
    content TEXT NOT NULL,
    admin_id BIGINT NOT NULL,
    "order" INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS stats (
    id SERIAL PRIMARY KEY DEFAULT nextval('stats_id_seq'),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    stat_type VARCHAR(100) NOT NULL,
    value INTEGER NOT NULL,
    extra_data TEXT,
    created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_relationships (
    id SERIAL PRIMARY KEY DEFAULT nextval('user_relationships_id_seq'),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    target_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    relationship_type VARCHAR(20) NOT NULL,
    created_by BIGINT,
    created_at TIMESTAMP,
    UNIQUE(user_id, target_user_id)
);

CREATE TABLE IF NOT EXISTS bot_moods (
    id SERIAL PRIMARY KEY DEFAULT nextval('bot_moods_id_seq'),
    mood_name VARCHAR(50) NOT NULL UNIQUE,
    valence_target FLOAT,
    arousal_target FLOAT,
    dominance_target FLOAT,
    response_patterns TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY DEFAULT nextval('events_id_seq'),
    event_type VARCHAR(100) NOT NULL,
    source VARCHAR(50),
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    chat_id BIGINT,
    data TEXT,
    created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS game_sessions (
    id VARCHAR(100) PRIMARY KEY,
    game_name VARCHAR(100) NOT NULL,
    game_master_id INTEGER NOT NULL REFERENCES users(id),
    state TEXT,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS player_states (
    id SERIAL PRIMARY KEY DEFAULT nextval('player_states_id_seq'),
    session_id VARCHAR(100) NOT NULL REFERENCES game_sessions(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    character_data TEXT,
    last_action TEXT,
    joined_at TIMESTAMP,
    UNIQUE(session_id, user_id)
);

CREATE TABLE IF NOT EXISTS tool_executions (
    id SERIAL PRIMARY KEY DEFAULT nextval('tool_executions_id_seq'),
    tool_name VARCHAR(100) NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    chat_id BIGINT,
    input_data TEXT,
    output_data TEXT,
    execution_time_ms INTEGER,
    status VARCHAR(20),
    error_message TEXT,
    created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS api_keys (
    id SERIAL PRIMARY KEY DEFAULT nextval('api_keys_id_seq'),
    key_id VARCHAR(100) NOT NULL UNIQUE,
    key_hash VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    permissions TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    last_used_at TIMESTAMP,
    created_at TIMESTAMP,
    expires_at TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_messages_user_id ON messages(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages(chat_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);
CREATE INDEX IF NOT EXISTS idx_categories_parent_id ON categories(parent_id);
CREATE INDEX IF NOT EXISTS idx_jokes_category_id ON jokes(category_id);
CREATE INDEX IF NOT EXISTS idx_jokes_language ON jokes(language);
CREATE INDEX IF NOT EXISTS idx_memories_user_id ON memories(user_id);
CREATE INDEX IF NOT EXISTS idx_memories_category ON memories(category);
CREATE INDEX IF NOT EXISTS idx_memories_created_at ON memories(created_at);
CREATE INDEX IF NOT EXISTS idx_memories_valence ON memories(valence);
CREATE INDEX IF NOT EXISTS idx_memories_admin_id ON memories(admin_id);
CREATE INDEX IF NOT EXISTS idx_memory_links_source ON memory_links(source_memory_id);
CREATE INDEX IF NOT EXISTS idx_memory_links_target ON memory_links(target_memory_id);
CREATE INDEX IF NOT EXISTS idx_lessons_order ON lessons("order");
CREATE INDEX IF NOT EXISTS idx_lessons_active ON lessons(is_active);
CREATE INDEX IF NOT EXISTS idx_stats_user_type ON stats(user_id, stat_type);
CREATE INDEX IF NOT EXISTS idx_stats_created_at ON stats(created_at);
CREATE INDEX IF NOT EXISTS idx_relationships_user ON user_relationships(user_id);
CREATE INDEX IF NOT EXISTS idx_relationships_target ON user_relationships(target_user_id);
CREATE INDEX IF NOT EXISTS idx_bot_moods_active ON bot_moods(is_active);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_source ON events(source);
CREATE INDEX IF NOT EXISTS idx_events_created_at ON events(created_at);
CREATE INDEX IF NOT EXISTS idx_game_sessions_status ON game_sessions(status);
CREATE INDEX IF NOT EXISTS idx_game_sessions_master ON game_sessions(game_master_id);
CREATE INDEX IF NOT EXISTS idx_player_states_session ON player_states(session_id);
CREATE INDEX IF NOT EXISTS idx_tool_executions_tool ON tool_executions(tool_name);
CREATE INDEX IF NOT EXISTS idx_tool_executions_status ON tool_executions(status);
CREATE INDEX IF NOT EXISTS idx_tool_executions_created_at ON tool_executions(created_at);
CREATE INDEX IF NOT EXISTS idx_api_keys_user ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_active ON api_keys(is_active);

-- Insert default data
INSERT INTO categories (name, description) VALUES
    ('general', 'General purpose memories'),
    ('personal', 'Personal information about users'),
    ('technical', 'Technical knowledge and facts'),
    ('emotional', 'Emotional context and feelings')
ON CONFLICT (name) DO NOTHING;

INSERT INTO bot_moods (mood_name, valence_target, arousal_target, dominance_target)
VALUES ('neutral', 0.0, 0.5, 0.5)
ON CONFLICT (mood_name) DO NOTHING;
