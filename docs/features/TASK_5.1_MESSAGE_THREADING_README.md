# Task 5.1: Message Threading & Replies

## 📋 Overview

**Status**: ✅ Complete  
**Lines of Code**: ~2,100  
**Completion Date**: 2025-11-26

This task implements a comprehensive message threading system that allows users to reply to specific messages, creating organized conversation threads within messenger conversations.

## 🎯 Objectives

1. ✅ Database schema for message threading (parent_id, thread_id, reply_count)
2. ✅ Threading service with reply management
3. ✅ Nested reply support (replies to replies)
4. ✅ Thread retrieval with nested structure
5. ✅ Thread summaries and metadata
6. ✅ Thread listing (recent, popular, oldest)
7. ✅ Thread deletion (soft delete entire thread)
8. ✅ REST API endpoints (6 endpoints)
9. ✅ WebSocket integration (message.reply event)
10. ✅ Comprehensive test suite (20+ scenarios)

## 🏗️ Architecture

### Threading Model

```
Root Message (thread_id=NULL, parent_id=NULL)
├── Reply 1 (thread_id=Root.id, parent_id=Root.id)
│   ├── Reply 1.1 (thread_id=Root.id, parent_id=Reply1.id)
│   └── Reply 1.2 (thread_id=Root.id, parent_id=Reply1.id)
├── Reply 2 (thread_id=Root.id, parent_id=Root.id)
│   └── Reply 2.1 (thread_id=Root.id, parent_id=Reply2.id)
└── Reply 3 (thread_id=Root.id, parent_id=Root.id)
```

**Key Concepts:**
- **Root Message**: Original message with no parent (`parent_id=NULL`, `thread_id=NULL`)
- **Direct Reply**: Reply to root message (`parent_id=Root.id`, `thread_id=Root.id`)
- **Nested Reply**: Reply to a reply (`parent_id=Reply.id`, `thread_id=Root.id`)
- **Thread**: All messages with the same `thread_id`

### Components

```
Message Threading System
├── Database Layer
│   ├── Migration (010_add_message_threading.py)
│   ├── Message model with threading fields
│   └── Materialized view (thread_summaries)
│
├── Service Layer
│   └── ThreadingService (threading.py - 550 LOC)
│       ├── create_reply()
│       ├── get_thread()
│       ├── get_thread_summary()
│       ├── list_threads()
│       ├── delete_thread()
│       └── get_thread_participants()
│
├── REST API Layer
│   └── 6 threading endpoints (messenger.py - +600 LOC)
│
├── WebSocket Layer
│   └── message.reply event handler (+150 LOC)
│
└── Test Layer
    └── 20+ test scenarios (800 LOC)
```

## 💾 Database Schema

### Message Table Updates

```sql
ALTER TABLE messages ADD COLUMN parent_id UUID REFERENCES messages(id) ON DELETE CASCADE;
ALTER TABLE messages ADD COLUMN thread_id UUID REFERENCES messages(id) ON DELETE CASCADE;
ALTER TABLE messages ADD COLUMN reply_count INTEGER DEFAULT 0;
ALTER TABLE messages ADD COLUMN last_reply_at TIMESTAMP;

-- Indexes for performance
CREATE INDEX ix_messages_parent_id ON messages(parent_id);
CREATE INDEX ix_messages_thread_id ON messages(thread_id);
CREATE INDEX ix_messages_reply_count ON messages(reply_count);
CREATE INDEX ix_messages_thread_id_created_at ON messages(thread_id, created_at);
```

### Message Model Fields

| Field | Type | Description |
|-------|------|-------------|
| `parent_id` | UUID | ID of the message this is replying to (NULL if not a reply) |
| `thread_id` | UUID | ID of the root message in the thread (NULL if this IS the root) |
| `reply_count` | Integer | Number of direct and nested replies |
| `last_reply_at` | DateTime | Timestamp of most recent reply (for sorting) |

### Materialized View (Optimization)

```sql
CREATE MATERIALIZED VIEW thread_summaries AS
SELECT 
    m.id as thread_id,
    m.conversation_id,
    m.sender_id,
    m.content,
    m.reply_count,
    m.last_reply_at,
    COUNT(DISTINCT r.sender_id) as unique_participants,
    MAX(r.created_at) as latest_reply_at
FROM messages m
LEFT JOIN messages r ON r.thread_id = m.id
WHERE m.thread_id IS NULL  -- Only root messages
GROUP BY m.id;
```

**Benefits:**
- Fast thread listing (no complex JOINs)
- Pre-computed participant counts
- Refresh strategy: `REFRESH MATERIALIZED VIEW CONCURRENTLY`

## 🔧 Threading Service

### Core Methods

```python
class ThreadingService:
    async def create_reply(
        db: AsyncSession,
        conversation_id: UUID,
        parent_message_id: UUID,
        sender_id: int,
        content: str,
        message_type: str = "text",
        file_url: Optional[str] = None,
        file_size: Optional[int] = None,
        file_name: Optional[str] = None,
    ) -> Message
    
    async def get_thread(
        db: AsyncSession,
        thread_root_id: UUID,
        user_id: int,
        include_deleted: bool = False,
    ) -> Dict
    
    async def get_thread_summary(
        db: AsyncSession,
        thread_root_id: UUID,
        user_id: int,
    ) -> Dict
    
    async def list_threads(
        db: AsyncSession,
        conversation_id: UUID,
        user_id: int,
        limit: int = 20,
        offset: int = 0,
        sort_by: str = "recent",
    ) -> List[Dict]
    
    async def delete_thread(
        db: AsyncSession,
        thread_root_id: UUID,
        user_id: int,
        is_admin: bool = False,
    ) -> int
    
    async def get_thread_participants(
        db: AsyncSession,
        thread_root_id: UUID,
        user_id: int,
    ) -> List[int]
```

### Reply Creation Logic

```python
# 1. Verify parent message exists
parent_message = await db.get(Message, parent_message_id)

# 2. Determine thread_id
#    - If parent has thread_id, use it
#    - Otherwise, parent IS the root
thread_id = parent_message.thread_id or parent_message.id

# 3. Create reply
reply = Message(
    conversation_id=conversation_id,
    sender_id=sender_id,
    content=content,
    parent_id=parent_message_id,
    thread_id=thread_id,
)

# 4. Update parent reply count
parent_message.reply_count += 1
parent_message.last_reply_at = datetime.utcnow()

# 5. Update root reply count (if nested)
if parent_message.thread_id:
    root_message.reply_count += 1
    root_message.last_reply_at = datetime.utcnow()
```

### Thread Retrieval

Returns nested structure:

```json
{
  "id": "root-message-id",
  "content": "Original message",
  "reply_count": 5,
  "replies": [
    {
      "id": "reply-1-id",
      "content": "First reply",
      "replies": [
        {
          "id": "nested-reply-id",
          "content": "Nested reply",
          "replies": []
        }
      ]
    },
    {
      "id": "reply-2-id",
      "content": "Second reply",
      "replies": []
    }
  ]
}
```

## 📡 REST API Endpoints

### 1. Create Reply

```http
POST /api/v1/messenger/conversations/{conversation_id}/messages/{message_id}/reply

Request Body:
{
    "content": "I agree with that!",
    "message_type": "text"
}

Response (201 Created):
{
    "id": "reply-uuid",
    "conversation_id": "conversation-uuid",
    "sender_id": 1,
    "content": "I agree with that!",
    "message_type": "text",
    "parent_id": "message-uuid",
    "thread_id": "root-message-uuid",
    "created_at": "2025-11-26T10:00:00Z",
    ...
}
```

### 2. List Threads

```http
GET /api/v1/messenger/conversations/{conversation_id}/threads?sort_by=popular&limit=20

Query Parameters:
- limit: 1-100 (default: 20)
- offset: pagination offset
- sort_by: "recent" | "popular" | "oldest"

Response:
{
    "threads": [
        {
            "thread_id": "uuid",
            "content": "Root message",
            "reply_count": 15,
            "last_reply_at": "2025-11-26T10:00:00Z",
            "latest_reply": {
                "id": "uuid",
                "sender_id": 5,
                "content": "Latest reply...",
                "created_at": "2025-11-26T10:00:00Z"
            }
        },
        ...
    ],
    "limit": 20,
    "offset": 0,
    "sort_by": "popular"
}
```

### 3. Get Thread (Nested Structure)

```http
GET /api/v1/messenger/threads/{thread_id}?include_deleted=false

Response:
{
    "id": "root-uuid",
    "content": "Root message",
    "reply_count": 5,
    "replies": [
        {
            "id": "reply-uuid",
            "content": "Reply 1",
            "replies": [...]
        }
    ]
}
```

### 4. Get Thread Summary

```http
GET /api/v1/messenger/threads/{thread_id}/summary

Response:
{
    "thread_id": "uuid",
    "content": "Root message",
    "reply_count": 15,
    "unique_participants": 5,
    "latest_reply": {
        "id": "uuid",
        "sender_id": 5,
        "content": "Latest reply",
        "created_at": "2025-11-26T10:00:00Z"
    }
}
```

### 5. Get Thread Participants

```http
GET /api/v1/messenger/threads/{thread_id}/participants

Response:
{
    "thread_id": "uuid",
    "participants": [1, 5, 12, 23]
}
```

### 6. Delete Thread

```http
DELETE /api/v1/messenger/threads/{thread_id}

Response: 204 No Content

Note:
- Soft deletes root + all replies
- Only thread creator or admin can delete
- Broadcasts thread.deleted event
```

## 🔌 WebSocket Integration

### Message Reply Event

```javascript
// Client sends reply via WebSocket
ws.send(JSON.stringify({
    type: "message.reply",
    parent_id: "parent-message-uuid",
    conversation_id: "conversation-uuid",
    content: "This is a reply",
    message_type: "text"
}));

// Client receives acknowledgment
{
    type: "message.replied",
    message_id: "new-reply-uuid",
    parent_id: "parent-message-uuid",
    thread_id: "root-message-uuid",
    data: { /* full message object */ }
}

// All participants receive broadcast
{
    type: "message.reply",
    data: { /* full message object */ },
    parent_id: "parent-message-uuid",
    thread_id: "root-message-uuid"
}
```

### WebSocket Handler

```python
async def handle_message_reply(
    websocket: WebSocket,
    user_id: int,
    conversation_id: UUID,
    parent_message_id: UUID,
    message_data: dict,
):
    # 1. Create reply using threading service
    reply = await threading_service.create_reply(...)
    
    # 2. Update user presence
    await update_user_activity(user_id)
    
    # 3. Broadcast to conversation
    await pubsub.publish_message(
        conversation_id=conversation_id,
        message_data={
            "type": "message.reply",
            "data": reply_data,
            "parent_id": str(parent_message_id),
            "thread_id": str(reply.thread_id),
        },
    )
    
    # 4. Send ACK to sender
    await websocket.send_json({
        "type": "message.replied",
        "message_id": str(reply.id),
        ...
    })
    
    # 5. Track analytics
    await analytics.track_event(...)
    
    # 6. Send push notifications
    asyncio.create_task(send_push_notifications(...))
```

## 🚀 Usage Examples

### Frontend Integration (JavaScript)

```javascript
// Initialize WebSocket
const ws = new WebSocket('ws://localhost:8000/api/v1/messenger/ws/1');

// Send reply to a message
function replyToMessage(parentId, content) {
    ws.send(JSON.stringify({
        type: 'message.reply',
        parent_id: parentId,
        conversation_id: currentConversationId,
        content: content,
        message_type: 'text'
    }));
}

// Listen for replies
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.type === 'message.reply') {
        // New reply received
        addReplyToThread(data.parent_id, data.data);
    } else if (data.type === 'message.replied') {
        // Your reply was sent
        console.log('Reply sent:', data.message_id);
    }
};

// Fetch thread via REST API
async function loadThread(threadId) {
    const response = await fetch(`/api/v1/messenger/threads/${threadId}`);
    const thread = await response.json();
    
    renderThread(thread);
}

// Render nested thread
function renderThread(thread) {
    const html = `
        <div class="thread">
            <div class="message root">${thread.content}</div>
            <div class="replies">
                ${thread.replies.map(reply => renderReply(reply)).join('')}
            </div>
        </div>
    `;
    
    return html;
}

function renderReply(reply) {
    return `
        <div class="message reply">
            <div class="content">${reply.content}</div>
            <div class="nested-replies">
                ${reply.replies.map(nested => renderReply(nested)).join('')}
            </div>
        </div>
    `;
}

// List hot threads
async function loadHotThreads(conversationId) {
    const response = await fetch(
        `/api/v1/messenger/conversations/${conversationId}/threads?sort_by=popular&limit=10`
    );
    const data = await response.json();
    
    data.threads.forEach(thread => {
        console.log(`Thread: ${thread.content} (${thread.reply_count} replies)`);
    });
}
```

### Backend Integration (Python)

```python
from app.messenger.threading import get_threading_service

# Create a reply
async def create_reply_example():
    threading_service = get_threading_service()
    
    reply = await threading_service.create_reply(
        db=db,
        conversation_id=conversation_id,
        parent_message_id=parent_id,
        sender_id=user_id,
        content="This is a reply",
    )
    
    print(f"Reply created: {reply.id}")
    print(f"Thread ID: {reply.thread_id}")
    print(f"Parent ID: {reply.parent_id}")

# Get thread with all replies
async def get_thread_example():
    threading_service = get_threading_service()
    
    thread = await threading_service.get_thread(
        db=db,
        thread_root_id=root_message_id,
        user_id=user_id,
    )
    
    print(f"Thread has {len(thread['replies'])} direct replies")

# List popular threads
async def list_popular_threads():
    threading_service = get_threading_service()
    
    threads = await threading_service.list_threads(
        db=db,
        conversation_id=conversation_id,
        user_id=user_id,
        sort_by="popular",
        limit=10,
    )
    
    for thread in threads:
        print(f"{thread['content'][:50]}... ({thread['reply_count']} replies)")
```

### React Component Example

```typescript
import React, { useState, useEffect } from 'react';

interface Message {
    id: string;
    content: string;
    sender_id: number;
    created_at: string;
    replies: Message[];
}

function ThreadView({ threadId }: { threadId: string }) {
    const [thread, setThread] = useState<Message | null>(null);
    const [replyText, setReplyText] = useState('');

    useEffect(() => {
        loadThread();
    }, [threadId]);

    const loadThread = async () => {
        const response = await fetch(`/api/v1/messenger/threads/${threadId}`);
        const data = await response.json();
        setThread(data);
    };

    const handleReply = async (parentId: string) => {
        const response = await fetch(
            `/api/v1/messenger/conversations/${thread.conversation_id}/messages/${parentId}/reply`,
            {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    content: replyText,
                    message_type: 'text'
                })
            }
        );

        if (response.ok) {
            setReplyText('');
            loadThread(); // Reload thread
        }
    };

    const renderMessage = (message: Message, depth: number = 0) => (
        <div key={message.id} style={{ marginLeft: depth * 20 }}>
            <div className="message">
                <div className="content">{message.content}</div>
                <div className="meta">
                    {new Date(message.created_at).toLocaleString()}
                </div>
                <button onClick={() => handleReply(message.id)}>
                    Reply
                </button>
            </div>
            {message.replies.map(reply => renderMessage(reply, depth + 1))}
        </div>
    );

    if (!thread) return <div>Loading...</div>;

    return (
        <div className="thread-view">
            {renderMessage(thread)}
            <div className="reply-form">
                <textarea
                    value={replyText}
                    onChange={(e) => setReplyText(e.target.value)}
                    placeholder="Write a reply..."
                />
                <button onClick={() => handleReply(thread.id)}>
                    Send Reply
                </button>
            </div>
        </div>
    );
}

export default ThreadView;
```

## 📈 Performance Considerations

### Query Optimization

```python
# ❌ Bad: N+1 queries
for thread in threads:
    replies = await db.execute(
        select(Message).where(Message.thread_id == thread.id)
    )

# ✅ Good: Single query with joins
threads_with_replies = await db.execute(
    select(Message)
    .options(selectinload(Message.replies))
    .where(Message.conversation_id == conversation_id)
)
```

### Materialized View Refresh

```sql
-- Refresh thread summaries (run periodically)
REFRESH MATERIALIZED VIEW CONCURRENTLY thread_summaries;

-- Or use in cron job
0 * * * * psql -d dreamseed -c "REFRESH MATERIALIZED VIEW CONCURRENTLY thread_summaries;"
```

### Caching Strategy

```python
from app.messenger.analytics import get_analytics_service

analytics = get_analytics_service()

# Cache thread summaries (5 min TTL)
cache_key = f"thread_summary:{thread_id}"
cached = await analytics.redis.get(cache_key)

if cached:
    return json.loads(cached)

summary = await threading_service.get_thread_summary(...)
await analytics.redis.setex(cache_key, 300, json.dumps(summary))
```

### Index Usage

```sql
-- Hot threads query (uses ix_messages_reply_count)
EXPLAIN ANALYZE
SELECT * FROM messages
WHERE conversation_id = '...'
  AND parent_id IS NULL
  AND deleted_at IS NULL
ORDER BY reply_count DESC
LIMIT 10;

-- Recent threads query (uses ix_messages_thread_id_created_at)
EXPLAIN ANALYZE
SELECT * FROM messages
WHERE conversation_id = '...'
  AND parent_id IS NULL
  AND deleted_at IS NULL
ORDER BY last_reply_at DESC, created_at DESC
LIMIT 20;
```

## 🧪 Testing

### Run Tests

```bash
cd backend

# Run all threading tests
pytest tests/test_messenger_threading.py -v

# Run specific test
pytest tests/test_messenger_threading.py::test_create_reply_success -v

# Run with coverage
pytest tests/test_messenger_threading.py --cov=app.messenger.threading --cov-report=html
```

### Test Coverage

- ✅ Reply creation (success, parent not found, not participant)
- ✅ Nested replies (reply to reply)
- ✅ Thread retrieval (nested structure)
- ✅ Thread summaries (metadata, participants)
- ✅ Thread listing (recent, popular, oldest)
- ✅ Thread deletion (permission checks, admin override)
- ✅ Thread participants
- ✅ Singleton pattern
- ✅ Integration tests (optional, requires DB)

## 🔒 Security

### Permission Checks

```python
# 1. User must be conversation participant
participant = await db.get(
    ConversationParticipant,
    conversation_id=conversation_id,
    user_id=user_id
)
if not participant:
    raise ValueError("Not a participant")

# 2. Only sender or admin can delete thread
if message.sender_id != user_id and not is_admin:
    raise ValueError("Permission denied")

# 3. Soft delete preserves data
message.deleted_at = datetime.utcnow()
# Data still in DB for audit/recovery
```

### Data Privacy

- Thread access requires conversation participation
- Deleted threads hidden from non-admins
- RLS policies enforce row-level security
- All operations logged for audit trail

## 📚 Related Features

### Future Enhancements

1. **Thread Subscriptions**
   - Users can subscribe/unsubscribe from threads
   - Notification preferences per thread

2. **Thread Reactions**
   - React to entire threads
   - Show popular threads by reaction count

3. **Thread Search**
   - Full-text search within threads
   - Filter by participant, date range

4. **Thread Exports**
   - Export thread as PDF/Markdown
   - Share thread permalink

5. **Thread Analytics**
   - Most active threads
   - Average response time
   - Participant engagement metrics

6. **Thread Moderation**
   - Pin important threads
   - Lock threads (prevent new replies)
   - Move threads to different conversations

## 🎉 Completion Summary

| Metric | Value |
|--------|-------|
| **Total LOC** | 2,100 |
| **Database Migration** | 120 LOC |
| **Model Updates** | 80 LOC |
| **Threading Service** | 550 LOC |
| **REST API Endpoints** | 600 LOC |
| **WebSocket Integration** | 150 LOC |
| **Tests** | 800 LOC |
| **API Endpoints** | 6 |
| **Test Scenarios** | 20+ |

### Key Achievements

✅ Nested reply support (unlimited depth)  
✅ Efficient thread queries with indexes  
✅ Thread summaries with participant counts  
✅ Multiple sorting options (recent, popular, oldest)  
✅ Thread deletion with permission checks  
✅ REST API + WebSocket integration  
✅ Comprehensive test coverage  
✅ Production-ready with security and performance optimization  
✅ Materialized view for fast thread listings

**Cumulative Project LOC**: 17,630 / 50,000 (35.3% complete)

---

**Task 5.1 Complete!** 🎊

Ready to proceed with:
- Task 5.2: Reactions & Emoji Support
- Task 5.3: Voice/Video Call Integration
- Task 6.1: Message Search Enhancement
- Or other features!
