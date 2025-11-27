# WebRTC Signaling Guide

## Overview

DreamSeedAI의 메신저 시스템은 WebRTC 기반 화상/음성 통화를 지원합니다. 이 가이드는 WebRTC 시그널링 프로토콜과 구현 방법을 설명합니다.

## Architecture

```
┌─────────────┐         WebSocket          ┌─────────────┐
│   Client A  │◄───────────────────────────►│   Server    │
│  (Browser)  │    Signaling Messages       │  (FastAPI)  │
└─────────────┘                             └─────────────┘
      │                                            │
      │ WebRTC P2P Media Stream                   │
      │ (after connection established)            │
      ▼                                            ▼
┌─────────────┐         WebSocket          ┌─────────────┐
│   Client B  │◄───────────────────────────►│   Server    │
│  (Browser)  │    Signaling Messages       │  (FastAPI)  │
└─────────────┘                             └─────────────┘
```

**Key Components:**
1. **WebSocket Connection** - 실시간 시그널링 메시지 전달
2. **Redis Pub/Sub** - 멀티 서버 환경에서 시그널링 브로드캐스트
3. **Call Service** - 통화 상태 및 참여자 관리
4. **WebRTC Peer Connection** - 클라이언트 간 P2P 미디어 스트림

## Signaling Flow

### 1. Call Initiation

```javascript
// Client A: 통화 시작
ws.send(JSON.stringify({
  type: "call.initiate",
  conversation_id: "uuid",
  call_type: "video",  // or "audio"
  invited_user_ids: [2, 3, 4]
}));

// Server Response
{
  type: "call.initiated",
  call_id: "uuid",
  data: {
    id: "uuid",
    conversation_id: "uuid",
    initiator_id: 1,
    call_type: "video",
    status: "initiated"
  }
}

// Server broadcasts to invited users
{
  type: "call.invitation",
  call_id: "uuid",
  from_user_id: 1,
  call_type: "video"
}
```

### 2. WebRTC Offer/Answer Exchange

**Step 1: Caller sends SDP Offer**

```javascript
// Client A creates offer
const pc = new RTCPeerConnection(config);
const offer = await pc.createOffer();
await pc.setLocalDescription(offer);

// Send offer via WebSocket
ws.send(JSON.stringify({
  type: "webrtc.offer",
  call_id: "call-uuid",
  sdp: offer.sdp,
  peer_id: "peer-a-uuid"  // Optional WebRTC peer ID
}));
```

**Step 2: Server forwards offer to callee**

```json
{
  "type": "webrtc.offer",
  "call_id": "call-uuid",
  "from_user_id": 1,
  "sdp": "v=0\no=- 123456789 2 IN IP4...",
  "peer_id": "peer-a-uuid"
}
```

**Step 3: Callee sends SDP Answer**

```javascript
// Client B receives offer and creates answer
const pc = new RTCPeerConnection(config);
await pc.setRemoteDescription(new RTCSessionDescription({
  type: "offer",
  sdp: offer.sdp
}));

const answer = await pc.createAnswer();
await pc.setLocalDescription(answer);

// Send answer via WebSocket
ws.send(JSON.stringify({
  type: "webrtc.answer",
  call_id: "call-uuid",
  sdp: answer.sdp,
  to_user_id: 1,  // Send back to caller
  peer_id: "peer-b-uuid"
}));
```

**Step 4: Server forwards answer to caller**

```json
{
  "type": "webrtc.answer",
  "call_id": "call-uuid",
  "from_user_id": 2,
  "sdp": "v=0\no=- 987654321 2 IN IP4...",
  "peer_id": "peer-b-uuid"
}
```

### 3. ICE Candidate Exchange

**ICE Candidate Discovery**

```javascript
// Client A discovers ICE candidates
pc.onicecandidate = (event) => {
  if (event.candidate) {
    ws.send(JSON.stringify({
      type: "webrtc.ice_candidate",
      call_id: "call-uuid",
      candidate: event.candidate.candidate,
      sdpMid: event.candidate.sdpMid,
      sdpMLineIndex: event.candidate.sdpMLineIndex,
      to_user_id: 2  // Optional: specific peer
    }));
  }
};
```

**Server forwards ICE candidates**

```json
{
  "type": "webrtc.ice_candidate",
  "call_id": "call-uuid",
  "from_user_id": 1,
  "candidate": "candidate:1 1 UDP 2130706431 192.168.1.100 54321 typ host",
  "sdpMid": "0",
  "sdpMLineIndex": 0
}
```

**Client adds remote ICE candidate**

```javascript
// Client B receives and adds ICE candidate
ws.onmessage = async (event) => {
  const msg = JSON.parse(event.data);
  
  if (msg.type === "webrtc.ice_candidate") {
    await pc.addIceCandidate(new RTCIceCandidate({
      candidate: msg.candidate,
      sdpMid: msg.sdpMid,
      sdpMLineIndex: msg.sdpMLineIndex
    }));
  }
};
```

### 4. Renegotiation (Screen Sharing, etc.)

```javascript
// Client A starts screen sharing
const screenStream = await navigator.mediaDevices.getDisplayMedia({
  video: true
});

// Add screen track to peer connection
const screenTrack = screenStream.getVideoTracks()[0];
pc.addTrack(screenTrack, screenStream);

// Renegotiate connection
const offer = await pc.createOffer();
await pc.setLocalDescription(offer);

// Send renegotiation offer
ws.send(JSON.stringify({
  type: "webrtc.renegotiate",
  call_id: "call-uuid",
  reason: "screen_sharing_started",
  sdp: offer.sdp
}));
```

### 5. Connection State Monitoring

```javascript
// Monitor connection state
pc.onconnectionstatechange = () => {
  ws.send(JSON.stringify({
    type: "webrtc.connection_state",
    call_id: "call-uuid",
    state: pc.connectionState,  // "connecting", "connected", "disconnected", "failed"
    quality: estimateQuality()  // "excellent", "good", "fair", "poor"
  }));
};

function estimateQuality() {
  // Based on RTCStats
  const stats = await pc.getStats();
  // Analyze packet loss, jitter, RTT
  return "good";
}
```

## REST API Endpoints

### Initiate Call

```http
POST /api/v1/messenger/conversations/{conversation_id}/calls
Content-Type: application/json

{
  "call_type": "video",
  "invited_user_ids": [2, 3, 4]
}
```

### Answer Call

```http
POST /api/v1/messenger/calls/{call_id}/answer
```

### Reject Call

```http
POST /api/v1/messenger/calls/{call_id}/reject
```

### End Call

```http
POST /api/v1/messenger/calls/{call_id}/end
Content-Type: application/json

{
  "end_reason": "completed"  // or "declined", "timeout", "failed"
}
```

### Update Media Settings

```http
PATCH /api/v1/messenger/calls/{call_id}/media
Content-Type: application/json

{
  "video_enabled": true,
  "audio_enabled": true,
  "screen_sharing": true
}
```

### Get Active Call

```http
GET /api/v1/messenger/conversations/{conversation_id}/calls/active
```

### Get Call History

```http
GET /api/v1/messenger/conversations/{conversation_id}/calls/history?limit=20&offset=0
```

## WebSocket Message Types

### Client → Server

| Message Type | Required Fields | Description |
|-------------|----------------|-------------|
| `call.initiate` | `conversation_id`, `call_type`, `invited_user_ids` | 통화 시작 |
| `call.answer` | `call_id` | 통화 수락 |
| `call.reject` | `call_id` | 통화 거절 |
| `call.end` | `call_id`, `end_reason` | 통화 종료 |
| `call.leave` | `call_id` | 통화 나가기 |
| `call.media` | `call_id`, media settings | 미디어 설정 변경 |
| `webrtc.offer` | `call_id`, `sdp`, `peer_id` | SDP Offer 전송 |
| `webrtc.answer` | `call_id`, `sdp`, `to_user_id` | SDP Answer 전송 |
| `webrtc.ice_candidate` | `call_id`, `candidate`, `sdpMid` | ICE Candidate 전송 |
| `webrtc.renegotiate` | `call_id`, `reason`, `sdp` | 재협상 요청 |
| `webrtc.connection_state` | `call_id`, `state`, `quality` | 연결 상태 업데이트 |

### Server → Client

| Message Type | Fields | Description |
|-------------|--------|-------------|
| `call.initiated` | `call_id`, `data` | 통화 생성 확인 |
| `call.invitation` | `call_id`, `from_user_id`, `call_type` | 통화 초대 알림 |
| `call.answered` | `call_id`, `user_id` | 상대방 수락 알림 |
| `call.rejected` | `call_id`, `user_id` | 상대방 거절 알림 |
| `call.ended` | `call_id`, `end_reason` | 통화 종료 알림 |
| `call.participant_left` | `call_id`, `user_id` | 참여자 퇴장 알림 |
| `call.media_updated` | `call_id`, `user_id`, media settings | 미디어 설정 변경 알림 |
| `webrtc.offer` | `call_id`, `from_user_id`, `sdp` | SDP Offer 수신 |
| `webrtc.answer` | `call_id`, `from_user_id`, `sdp` | SDP Answer 수신 |
| `webrtc.ice_candidate` | `call_id`, `from_user_id`, `candidate` | ICE Candidate 수신 |
| `webrtc.renegotiate` | `call_id`, `from_user_id`, `reason` | 재협상 요청 수신 |

## Frontend Integration Example

### Complete Call Flow (React/TypeScript)

```typescript
import { useEffect, useRef, useState } from 'react';

interface CallProps {
  callId: string;
  isInitiator: boolean;
  remoteUserId: number;
}

function VideoCall({ callId, isInitiator, remoteUserId }: CallProps) {
  const localVideoRef = useRef<HTMLVideoElement>(null);
  const remoteVideoRef = useRef<HTMLVideoElement>(null);
  const pcRef = useRef<RTCPeerConnection | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  
  const [localStream, setLocalStream] = useState<MediaStream | null>(null);
  const [remoteStream, setRemoteStream] = useState<MediaStream | null>(null);

  useEffect(() => {
    initializeCall();
    return () => cleanup();
  }, []);

  async function initializeCall() {
    // 1. Connect WebSocket
    const ws = new WebSocket('ws://localhost:8001/api/v1/messenger/ws/1');
    wsRef.current = ws;

    ws.onopen = async () => {
      console.log('WebSocket connected');
      
      // 2. Get local media stream
      const stream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: true
      });
      setLocalStream(stream);
      
      if (localVideoRef.current) {
        localVideoRef.current.srcObject = stream;
      }

      // 3. Create peer connection
      const pc = new RTCPeerConnection({
        iceServers: [
          { urls: 'stun:stun.l.google.com:19302' },
          { urls: 'stun:stun1.l.google.com:19302' }
        ]
      });
      pcRef.current = pc;

      // Add local stream tracks
      stream.getTracks().forEach(track => {
        pc.addTrack(track, stream);
      });

      // Handle incoming tracks
      pc.ontrack = (event) => {
        const [stream] = event.streams;
        setRemoteStream(stream);
        if (remoteVideoRef.current) {
          remoteVideoRef.current.srcObject = stream;
        }
      };

      // Handle ICE candidates
      pc.onicecandidate = (event) => {
        if (event.candidate) {
          ws.send(JSON.stringify({
            type: 'webrtc.ice_candidate',
            call_id: callId,
            candidate: event.candidate.candidate,
            sdpMid: event.candidate.sdpMid,
            sdpMLineIndex: event.candidate.sdpMLineIndex,
            to_user_id: remoteUserId
          }));
        }
      };

      // Monitor connection state
      pc.onconnectionstatechange = () => {
        console.log('Connection state:', pc.connectionState);
        ws.send(JSON.stringify({
          type: 'webrtc.connection_state',
          call_id: callId,
          state: pc.connectionState,
          quality: 'good'
        }));
      };

      // 4. If initiator, create and send offer
      if (isInitiator) {
        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);
        
        ws.send(JSON.stringify({
          type: 'webrtc.offer',
          call_id: callId,
          sdp: offer.sdp,
          peer_id: crypto.randomUUID()
        }));
      }
    };

    // Handle incoming signaling messages
    ws.onmessage = async (event) => {
      const msg = JSON.parse(event.data);
      const pc = pcRef.current;
      if (!pc) return;

      switch (msg.type) {
        case 'webrtc.offer':
          await pc.setRemoteDescription(new RTCSessionDescription({
            type: 'offer',
            sdp: msg.sdp
          }));
          
          const answer = await pc.createAnswer();
          await pc.setLocalDescription(answer);
          
          ws.send(JSON.stringify({
            type: 'webrtc.answer',
            call_id: callId,
            sdp: answer.sdp,
            to_user_id: msg.from_user_id
          }));
          break;

        case 'webrtc.answer':
          await pc.setRemoteDescription(new RTCSessionDescription({
            type: 'answer',
            sdp: msg.sdp
          }));
          break;

        case 'webrtc.ice_candidate':
          await pc.addIceCandidate(new RTCIceCandidate({
            candidate: msg.candidate,
            sdpMid: msg.sdpMid,
            sdpMLineIndex: msg.sdpMLineIndex
          }));
          break;

        case 'call.ended':
          cleanup();
          break;
      }
    };
  }

  function cleanup() {
    localStream?.getTracks().forEach(track => track.stop());
    pcRef.current?.close();
    wsRef.current?.close();
  }

  function toggleVideo() {
    if (localStream) {
      const videoTrack = localStream.getVideoTracks()[0];
      videoTrack.enabled = !videoTrack.enabled;
      
      wsRef.current?.send(JSON.stringify({
        type: 'call.media',
        call_id: callId,
        video_enabled: videoTrack.enabled
      }));
    }
  }

  function toggleAudio() {
    if (localStream) {
      const audioTrack = localStream.getAudioTracks()[0];
      audioTrack.enabled = !audioTrack.enabled;
      
      wsRef.current?.send(JSON.stringify({
        type: 'call.media',
        call_id: callId,
        audio_enabled: audioTrack.enabled
      }));
    }
  }

  function endCall() {
    wsRef.current?.send(JSON.stringify({
      type: 'call.end',
      call_id: callId,
      end_reason: 'completed'
    }));
    cleanup();
  }

  return (
    <div className="video-call">
      <video ref={localVideoRef} autoPlay muted playsInline />
      <video ref={remoteVideoRef} autoPlay playsInline />
      
      <div className="controls">
        <button onClick={toggleVideo}>Toggle Video</button>
        <button onClick={toggleAudio}>Toggle Audio</button>
        <button onClick={endCall}>End Call</button>
      </div>
    </div>
  );
}
```

## Database Schema

### calls Table

```sql
CREATE TABLE calls (
    id UUID PRIMARY KEY,
    conversation_id UUID NOT NULL REFERENCES conversations(id),
    initiator_id INTEGER NOT NULL REFERENCES users(id),
    call_type VARCHAR(10) NOT NULL CHECK (call_type IN ('audio', 'video')),
    status VARCHAR(20) NOT NULL,
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    end_reason VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_calls_conversation ON calls(conversation_id);
CREATE INDEX idx_calls_status ON calls(status);
```

### call_participants Table

```sql
CREATE TABLE call_participants (
    id UUID PRIMARY KEY,
    call_id UUID NOT NULL REFERENCES calls(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id),
    is_initiator BOOLEAN DEFAULT FALSE,
    answered BOOLEAN DEFAULT FALSE,
    video_enabled BOOLEAN DEFAULT TRUE,
    audio_enabled BOOLEAN DEFAULT TRUE,
    screen_sharing BOOLEAN DEFAULT FALSE,
    peer_id VARCHAR(255),  -- WebRTC peer ID
    connection_quality VARCHAR(20),
    joined_at TIMESTAMP,
    left_at TIMESTAMP
);

CREATE INDEX idx_call_participants_call ON call_participants(call_id);
CREATE INDEX idx_call_participants_user ON call_participants(user_id);
```

## Security Considerations

### 1. Authentication
- WebSocket 연결 시 JWT 토큰 검증
- 통화 참여 권한 검증 (대화방 참여자만)

### 2. Rate Limiting
- ICE candidate 메시지 제한 (초당 최대 10개)
- 재협상 요청 제한 (분당 최대 5회)

### 3. STUN/TURN Servers
```javascript
const config = {
  iceServers: [
    { urls: 'stun:stun.l.google.com:19302' },
    {
      urls: 'turn:turn.example.com:3478',
      username: 'user',
      credential: 'pass'
    }
  ]
};
```

## Testing

### Unit Tests

```python
# tests/test_webrtc_signaling.py
import pytest
from app.routers.messenger import (
    handle_webrtc_offer,
    handle_webrtc_answer,
    handle_webrtc_ice_candidate
)

@pytest.mark.asyncio
async def test_webrtc_offer_handling(mock_websocket, mock_db):
    """Test WebRTC offer forwarding"""
    await handle_webrtc_offer(
        websocket=mock_websocket,
        user_id=1,
        call_id=uuid.uuid4(),
        signaling_data={
            "sdp": "v=0\no=...",
            "peer_id": "peer-1"
        }
    )
    # Assert offer was broadcasted
```

### Integration Tests

```bash
# Run WebSocket tests
pytest tests/integration/test_webrtc_flow.py -v

# Expected: All signaling messages properly forwarded
```

## Monitoring & Analytics

### Call Quality Metrics

```python
# app/messenger/analytics.py
class AnalyticsEventType(str, Enum):
    CALL_QUALITY_UPDATE = "call_quality_update"

# Track connection quality
await analytics.track_event(
    event_type=AnalyticsEventType.CALL_QUALITY_UPDATE,
    user_id=user_id,
    metadata={
        "call_id": str(call_id),
        "quality": "good",
        "packet_loss": 0.02,
        "jitter": 15,
        "rtt": 45
    }
)
```

## Troubleshooting

### Common Issues

**1. ICE Candidates not exchanging**
- Check STUN server accessibility
- Verify firewall rules (UDP ports)
- Use TURN server for symmetric NAT

**2. One-way audio/video**
- Check media track directions
- Verify SDP offer/answer exchange
- Inspect browser console for errors

**3. Connection drops**
- Monitor network quality
- Implement reconnection logic
- Use connection state monitoring

## Next Steps

- [ ] Add screen sharing support (완료 - renegotiation 지원)
- [ ] Implement recording functionality
- [ ] Add virtual background support
- [ ] Optimize for mobile networks
- [ ] Add call quality indicators UI
- [ ] Implement call transfer feature

## References

- [WebRTC API - MDN](https://developer.mozilla.org/en-US/docs/Web/API/WebRTC_API)
- [RTCPeerConnection - W3C](https://www.w3.org/TR/webrtc/)
- [STUN/TURN Server Setup](https://github.com/coturn/coturn)
