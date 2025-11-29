# Task 5.2: Message Reactions & Emoji Support

**Status**: ✅ Completed  
**LOC**: ~1,800 lines  
**Date**: 2025-11-26

## Overview

Implemented comprehensive emoji reaction system for messages, similar to Slack/Discord/GitHub. Users can react to messages with emojis, see reaction counts, and browse popular reactions in conversations.

## Features

### Core Functionality
- ✅ Add emoji reactions to messages
- ✅ Remove reactions
- ✅ Toggle reactions (single-click convenience)
- ✅ View reactions grouped by emoji
- ✅ See who reacted with what emoji
- ✅ Popular reactions in conversations
- ✅ Reaction count badges
- ✅ 70+ supported emoji with shortcodes

### Technical Features
- ✅ Automatic reaction count updates (PostgreSQL trigger)
- ✅ Materialized view for fast queries
- ✅ Unique constraint (one emoji type per user per message)
- ✅ Real-time WebSocket broadcasts
- ✅ Redis Pub/Sub integration
- ✅ Comprehensive error handling
- ✅ Permission validation (participant-only)

## Architecture

### Database Schema

```sql
-- Reactions table
CREATE TABLE message_reactions (
    id SERIAL PRIMARY KEY,
    message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    emoji VARCHAR(50) NOT NULL,  -- Shortcode (e.g., "thumbs_up")
    emoji_unicode VARCHAR(20),    -- Unicode (e.g., "👍")
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(message_id, user_id, emoji)  -- One emoji type per user
);

-- Indexes
CREATE INDEX ix_message_reactions_message_id ON message_reactions(message_id);
CREATE INDEX ix_message_reactions_user_id ON message_reactions(user_id);
CREATE INDEX ix_message_reactions_emoji ON message_reactions(emoji);
CREATE INDEX ix_message_reactions_message_emoji ON message_reactions(message_id, emoji);

-- Add to messages table
ALTER TABLE messages ADD COLUMN reaction_count INTEGER DEFAULT 0;
CREATE INDEX ix_messages_reaction_count ON messages(reaction_count);

-- Materialized view for fast summaries
CREATE MATERIALIZED VIEW message_reaction_summaries AS
SELECT 
    message_id,
    emoji,
    COUNT(*) as reaction_count,
    ARRAY_AGG(user_id) as user_ids,
    MAX(created_at) as latest_reaction_at
FROM message_reactions
GROUP BY message_id, emoji;

-- Auto-update trigger
CREATE OR REPLACE FUNCTION update_message_reaction_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE messages 
        SET reaction_count = reaction_count + 1 
        WHERE id = NEW.message_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE messages 
        SET reaction_count = reaction_count - 1 
        WHERE id = OLD.message_id;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_reaction_count
AFTER INSERT OR DELETE ON message_reactions
FOR EACH ROW EXECUTE FUNCTION update_message_reaction_count();
```

### Service Layer

```python
# app/messenger/reactions.py

class ReactionsService:
    """Service for managing message reactions."""
    
    @staticmethod
    async def add_reaction(
        db: AsyncSession,
        message_id: UUID,
        user_id: int,
        emoji: str,
    ) -> MessageReaction:
        """Add emoji reaction to message."""
        
    @staticmethod
    async def remove_reaction(
        db: AsyncSession,
        message_id: UUID,
        user_id: int,
        emoji: str,
    ) -> bool:
        """Remove emoji reaction from message."""
        
    @staticmethod
    async def toggle_reaction(
        db: AsyncSession,
        message_id: UUID,
        user_id: int,
        emoji: str,
    ) -> Dict:
        """Toggle reaction (add if not exists, remove if exists)."""
        
    @staticmethod
    async def get_message_reactions(
        db: AsyncSession,
        message_id: UUID,
        user_id: int,
    ) -> Dict:
        """Get all reactions on message grouped by emoji."""
        
    @staticmethod
    async def get_reaction_summary(
        db: AsyncSession,
        message_id: UUID,
    ) -> Dict:
        """Get quick summary (count only)."""
```

## REST API Endpoints

### 1. Add Reaction
```http
POST /api/v1/messenger/messages/{message_id}/reactions?emoji={emoji}
Authorization: Bearer {token}

Response 200:
{
  "id": 123,
  "message_id": "uuid",
  "emoji": "thumbs_up",
  "emoji_unicode": "👍",
  "user_id": 1,
  "created_at": "2025-11-26T10:00:00Z"
}

Errors:
- 404: Message not found
- 403: User not a participant
- 409: Reaction already exists
```

### 2. Remove Reaction
```http
DELETE /api/v1/messenger/messages/{message_id}/reactions/{emoji}
Authorization: Bearer {token}

Response 204: No Content

Errors:
- 404: Reaction not found
```

### 3. Toggle Reaction
```http
POST /api/v1/messenger/messages/{message_id}/reactions/toggle?emoji={emoji}
Authorization: Bearer {token}

Response 200:
{
  "action": "added" | "removed",
  "message_id": "uuid",
  "emoji": "heart",
  "emoji_unicode": "❤️",  // Only if added
  "reaction_id": 123      // Only if added
}
```

### 4. Get Message Reactions
```http
GET /api/v1/messenger/messages/{message_id}/reactions
Authorization: Bearer {token}

Response 200:
{
  "message_id": "uuid",
  "total_reactions": 5,
  "reactions": [
    {
      "emoji": "thumbs_up",
      "emoji_unicode": "👍",
      "count": 3,
      "users": [1, 2, 3],
      "user_reacted": true  // Current user reacted
    },
    {
      "emoji": "heart",
      "emoji_unicode": "❤️",
      "count": 2,
      "users": [1, 4],
      "user_reacted": true
    }
  ]
}
```

### 5. Get Reaction Summary
```http
GET /api/v1/messenger/messages/{message_id}/reactions/summary

Response 200:
{
  "message_id": "uuid",
  "total_reactions": 5,
  "unique_emoji": 2
}
```

### 6. Get Popular Reactions
```http
GET /api/v1/messenger/conversations/{conversation_id}/reactions/popular?limit=10
Authorization: Bearer {token}

Response 200:
{
  "conversation_id": "uuid",
  "popular_reactions": [
    {
      "emoji": "thumbs_up",
      "emoji_unicode": "👍",
      "count": 42
    },
    {
      "emoji": "heart",
      "emoji_unicode": "❤️",
      "count": 38
    }
  ]
}
```

### 7. Get Supported Emoji
```http
GET /api/v1/messenger/reactions/emoji

Response 200:
{
  "emoji": [
    {"shortcode": "smile", "unicode": "😊"},
    {"shortcode": "thumbs_up", "unicode": "👍"},
    ...
  ],
  "count": 74
}
```

## WebSocket Events

### Client → Server

#### 1. Add Reaction
```json
{
  "type": "reaction.add",
  "message_id": "uuid",
  "emoji": "thumbs_up"
}
```

**Server Response:**
```json
{
  "type": "reaction.confirmed",
  "action": "added",
  "reaction": {
    "id": 123,
    "message_id": "uuid",
    "emoji": "thumbs_up",
    "emoji_unicode": "👍"
  }
}
```

#### 2. Remove Reaction
```json
{
  "type": "reaction.remove",
  "message_id": "uuid",
  "emoji": "thumbs_up"
}
```

**Server Response:**
```json
{
  "type": "reaction.confirmed",
  "action": "removed",
  "message_id": "uuid",
  "emoji": "thumbs_up"
}
```

#### 3. Toggle Reaction
```json
{
  "type": "reaction.toggle",
  "message_id": "uuid",
  "emoji": "heart"
}
```

**Server Response:**
```json
{
  "type": "reaction.confirmed",
  "action": "added" | "removed",
  "message_id": "uuid",
  "emoji": "heart"
}
```

### Server → Client (Broadcasts)

#### Reaction Added
```json
{
  "type": "reaction.added",
  "message_id": "uuid",
  "user_id": 1,
  "emoji": "thumbs_up",
  "emoji_unicode": "👍",
  "reaction_id": 123,
  "timestamp": "2025-11-26T10:00:00Z"
}
```

#### Reaction Removed
```json
{
  "type": "reaction.removed",
  "message_id": "uuid",
  "user_id": 1,
  "emoji": "thumbs_up",
  "timestamp": "2025-11-26T10:00:00Z"
}
```

## Emoji Support

### Shortcode Format
Uses human-readable shortcodes (e.g., `thumbs_up`, `heart_eyes`) similar to Slack/GitHub.

### Unicode Format
Stores actual emoji unicode (e.g., `👍`, `❤️`) for display flexibility.

### Supported Categories
- **Smileys & Emotion** (32 emoji): smile, joy, heart_eyes, thinking, etc.
- **Hearts** (14 emoji): heart, orange_heart, broken_heart, etc.
- **Hands** (19 emoji): thumbs_up, clap, raised_hands, pray, etc.
- **Objects & Symbols** (9 emoji): fire, star, sparkles, bulb, etc.

**Total:** 74 supported emoji

### Full Emoji List
See `EMOJI_MAP` in `app/messenger/reactions.py` for complete mapping.

## Frontend Integration

### React Example

```typescript
// Add reaction
const addReaction = async (messageId: string, emoji: string) => {
  await fetch(`/api/v1/messenger/messages/${messageId}/reactions?emoji=${emoji}`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` }
  });
};

// Toggle reaction (recommended)
const toggleReaction = async (messageId: string, emoji: string) => {
  await fetch(`/api/v1/messenger/messages/${messageId}/reactions/toggle?emoji=${emoji}`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` }
  });
};

// Get reactions for display
const getReactions = async (messageId: string) => {
  const response = await fetch(
    `/api/v1/messenger/messages/${messageId}/reactions`,
    { headers: { 'Authorization': `Bearer ${token}` } }
  );
  return await response.json();
};

// WebSocket listener
websocket.addEventListener('message', (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'reaction.added') {
    // Update UI to show new reaction
    updateReactionBadge(data.message_id, data.emoji);
  } else if (data.type === 'reaction.removed') {
    // Update UI to remove reaction
    removeReactionBadge(data.message_id, data.emoji);
  }
});
```

### UI Components

#### Reaction Picker
```tsx
<ReactionPicker
  onSelect={(emoji) => toggleReaction(message.id, emoji)}
  popularEmoji={['thumbs_up', 'heart', 'fire', 'smile']}
/>
```

#### Reaction Badge
```tsx
<ReactionBadge
  emoji="👍"
  count={3}
  userReacted={true}
  onClick={() => toggleReaction(message.id, 'thumbs_up')}
/>
```

## Testing

### Test Coverage
- ✅ Service layer: 25+ test cases
- ✅ REST API endpoints: 8+ test cases
- ✅ WebSocket handlers: 3+ test cases
- ✅ Database constraints and triggers
- ✅ Edge cases and error handling

### Run Tests
```bash
cd backend
source .venv/bin/activate
pytest tests/test_messenger_reactions.py -v
```

### Test Scenarios
1. Add reaction successfully
2. Add duplicate reaction (should fail)
3. Remove reaction
4. Toggle reaction (add/remove)
5. Get reactions grouped by emoji
6. Get popular reactions
7. Auto-update reaction counts (trigger)
8. Permission checks (participant-only)
9. WebSocket broadcasts
10. Multiple users reacting

## Performance Considerations

### Database Optimizations
- **Indexes**: Multiple indexes on message_id, user_id, emoji for fast lookups
- **Materialized View**: Pre-computed reaction summaries
- **Trigger**: Automatic count updates (no application logic needed)
- **Cascade Delete**: Auto-cleanup when messages deleted

### Query Performance
```sql
-- Fast lookup: Get reactions for a message
SELECT * FROM message_reactions WHERE message_id = ? ORDER BY created_at;

-- Fast summary: Use materialized view
SELECT * FROM message_reaction_summaries WHERE message_id = ?;

-- Fast count: Read from messages table (updated by trigger)
SELECT reaction_count FROM messages WHERE id = ?;
```

### Caching Recommendations
- Cache popular reactions per conversation (Redis, 5 min TTL)
- Cache supported emoji list (static data, long TTL)
- Real-time updates via WebSocket (no polling needed)

## Error Handling

### Common Errors

1. **Duplicate Reaction**
   - Status: 409 Conflict
   - Message: "User has already reacted with {emoji}"
   - Action: Use toggle endpoint instead

2. **Message Not Found**
   - Status: 404 Not Found
   - Message: "Message {id} not found"
   - Action: Verify message ID

3. **Not a Participant**
   - Status: 403 Forbidden
   - Message: "User is not a participant in this conversation"
   - Action: Check conversation membership

4. **Invalid Emoji**
   - Status: 400 Bad Request
   - Message: Validation error
   - Action: Use supported emoji only

## Migration

### Run Migration
```bash
cd backend
source .venv/bin/activate
alembic upgrade 011_add_message_reactions
```

### Rollback
```bash
alembic downgrade 010_add_message_threading
```

### Verify
```sql
-- Check table created
\d message_reactions

-- Check trigger created
SELECT * FROM pg_trigger WHERE tgname = 'trigger_update_reaction_count';

-- Check materialized view
\d message_reaction_summaries
```

## Security

### Access Control
- ✅ Only conversation participants can react
- ✅ Users can only remove their own reactions
- ✅ Permission checks on all operations
- ✅ SQL injection prevention (parameterized queries)

### Rate Limiting Recommendations
- Add reaction: 30 requests/minute per user
- Get reactions: 60 requests/minute per user
- Toggle reaction: 20 requests/minute per user

## Analytics Events

Track the following for analytics:
- `reaction_added`: User adds reaction
- `reaction_removed`: User removes reaction
- `reaction_toggled`: User toggles reaction
- Popular emoji by conversation
- Reaction usage trends

## Future Enhancements

### Phase 6 Candidates
1. **Custom Emoji**: Upload and use organization-specific emoji
2. **Reaction Notifications**: Notify users when their message is reacted to
3. **Reaction Shortcuts**: Quick-react with most recent/favorite emoji
4. **Emoji Search**: Search emoji by keyword in picker
5. **Skin Tone Support**: Emoji variants with different skin tones
6. **Reaction Analytics**: Detailed insights on reaction patterns

## Files Modified/Created

### Created (1,800 LOC)
1. **backend/alembic/versions/011_add_message_reactions.py** (140 LOC)
   - Database migration with table, indexes, trigger, materialized view

2. **backend/app/messenger/reactions.py** (650 LOC)
   - ReactionsService with 10+ methods
   - 74-emoji map with shortcodes
   - Singleton pattern for global access

3. **backend/app/routers/messenger.py** (+400 LOC)
   - 8 REST API endpoints
   - 3 WebSocket event handlers
   - Permission validation
   - Redis Pub/Sub broadcasts

4. **backend/tests/test_messenger_reactions.py** (610 LOC)
   - 25+ test cases
   - Fixtures for users, conversations, messages
   - Service, API, and WebSocket tests

### Modified
5. **backend/app/models/messenger_models.py** (+50 LOC)
   - MessageReaction model
   - Message.reaction_count field
   - Message.reactions relationship

6. **backend/app/models/__init__.py** (+2 LOC)
   - Exported MessageReaction model

## Summary

Successfully implemented comprehensive emoji reaction system with:
- ✅ 74 supported emoji with shortcode/unicode formats
- ✅ REST API (8 endpoints)
- ✅ WebSocket integration (3 event types)
- ✅ Real-time broadcasts via Redis Pub/Sub
- ✅ Automatic count updates (PostgreSQL trigger)
- ✅ Fast queries (indexes + materialized view)
- ✅ Comprehensive tests (25+ cases)
- ✅ Complete documentation

**Total LOC:** ~1,800 lines  
**Completion Date:** 2025-11-26  
**Status:** ✅ Production-ready

---

**Related Tasks:**
- ✅ Task 5.1: Message Threading & Replies
- ⏳ Task 5.3: Advanced Search Filters (Next)
- ⏳ Task 5.4: Message Bookmarks & Pins
