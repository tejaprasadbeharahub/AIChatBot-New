# System Architecture - Unified Research & Chat UI

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React + TypeScript)             │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              UnifiedChatPage (Main Component)            │   │
│  │                                                           │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │ Header - Title & Description                       │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  │                                                           │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │ Messages Area (Scrollable)                         │  │   │
│  │  │                                                     │  │   │
│  │  │ ┌──────────────────────────────────────────────┐   │  │   │
│  │  │ │ User Message (Blue/Gray bubble)              │   │  │   │
│  │  │ └──────────────────────────────────────────────┘   │  │   │
│  │  │                                                     │  │   │
│  │  │ ┌──────────────────────────────────────────────┐   │  │   │
│  │  │ │ Assistant Message                            │   │  │   │
│  │  │ │ ├─ Type: RESEARCH                            │   │  │   │
│  │  │ │ │  └─ ResearchDigestViewEnhanced             │   │  │   │
│  │  │ │ │     ├─ Overview Tab                        │   │  │   │
│  │  │ │ │     ├─ Key Findings Tab                    │   │  │   │
│  │  │ │ │     ├─ Papers Tab                          │   │  │   │
│  │  │ │ │     └─ Trends Tab                          │   │  │   │
│  │  │ │ └─ Type: CHAT                                │   │  │   │
│  │  │ │    └─ Text Bubble                            │   │  │   │
│  │  │ └──────────────────────────────────────────────┘   │  │   │
│  │  │                                                     │  │   │
│  │  │ ┌──────────────────────────────────────────────┐   │  │   │
│  │  │ │ ResearchDigestStream (During Processing)     │   │  │   │
│  │  │ │ ├─ Progress Header (papers, relevance, etc)  │   │  │   │
│  │  │ │ ├─ Event Timeline                            │   │  │   │
│  │  │ │ └─ Tips Section                              │   │  │   │
│  │  │ └──────────────────────────────────────────────┘   │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  │                                                           │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │ UnifiedChatInput Component                         │  │   │
│  │  │                                                     │  │   │
│  │  │ ┌──────────────────────────────────────────────┐   │  │   │
│  │  │ │ Textarea (Multi-line Input)                  │   │  │   │
│  │  │ │ └─ Query Type Badge (Auto-updated)           │   │  │   │
│  │  │ └──────────────────────────────────────────────┘   │  │   │
│  │  │                                                     │  │   │
│  │  │ ┌──────────────────────────────────────────────┐   │  │   │
│  │  │ │ Advanced Options (Conditional for Research)  │   │  │   │
│  │  │ │ ├─ Depth Selector                            │   │  │   │
│  │  │ │ ├─ Max Papers Slider                         │   │  │   │
│  │  │ │ └─ Toggle Button                             │   │  │   │
│  │  │ └──────────────────────────────────────────────┘   │  │   │
│  │  │                                                     │  │   │
│  │  │ ┌──────────────────────────────────────────────┐   │  │   │
│  │  │ │ Action Buttons                               │   │  │   │
│  │  │ │ ├─ Submit (colored by type)                  │   │  │   │
│  │  │ │ └─ Toggle Button                             │   │  │   │
│  │  │ └──────────────────────────────────────────────┘   │  │   │
│  │  │                                                     │  │   │
│  │  │ ┌──────────────────────────────────────────────┐   │  │   │
│  │  │ │ Tips Section (Context-aware hints)           │   │  │   │
│  │  │ └──────────────────────────────────────────────┘   │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  │                                                           │   │
│  └──────────────────────────────────────────────────────────┘  │   │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Query Detection Layer                       │   │
│  │           (queryDetector.ts - Utility)                   │   │
│  │                                                           │   │
│  │  detectQueryType(query) → { type, confidence, reason }   │   │
│  │  ├─ Research Keywords (80+ terms)                        │   │
│  │  ├─ Chat Keywords (40+ terms)                            │   │
│  │  └─ Pattern Matching & Scoring                           │   │
│  │                                                           │   │
│  └──────────────────────────────────────────────────────────┘  │   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                                                                     
                    ┌──────────────────────┐                        
                    │   LocalStorage       │                        
                    ├──────────────────────┤                        
                    │ token (JWT)          │                        
                    │ chat_id              │                        
                    └──────────────────────┘                        
                            │                                       
                            ▼                                       
┌─────────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────┐                               │
│  │ POST /api/chat               │                               │
│  ├──────────────────────────────┤                               │
│  │ Request:                      │                               │
│  │ {                             │                               │
│  │   message: string             │                               │
│  │   chat_id?: string            │                               │
│  │ }                             │                               │
│  │ Response:                     │                               │
│  │ { response: string }          │                               │
│  └──────────────────────────────┘                               │
│                                                                   │
│  ┌──────────────────────────────┐                               │
│  │ POST /api/research-agent/    │                               │
│  │       research-stream        │                               │
│  ├──────────────────────────────┤                               │
│  │ Request:                      │                               │
│  │ {                             │                               │
│  │   query: string               │                               │
│  │   depth: "quick"|"balanced"   │                               │
│  │          |"deep"              │                               │
│  │   max_papers: number          │                               │
│  │ }                             │                               │
│  │ Response: SSE Stream          │                               │
│  │ Events:                       │                               │
│  │ - initialized                 │                               │
│  │ - searching                   │                               │
│  │ - papers_found                │                               │
│  │ - analyzing                   │                               │
│  │ - refining                    │                               │
│  │ - generating_digest           │                               │
│  │ - completed                   │                               │
│  └──────────────────────────────┘                               │
│                                                                   │
│  ┌──────────────────────────────┐                               │
│  │ POST /api/research-agent/    │                               │
│  │       research                │                               │
│  ├──────────────────────────────┤                               │
│  │ Request: (same as above)      │                               │
│  │ Response:                     │                               │
│  │ {                             │                               │
│  │   digest: ResearchDigestFull  │                               │
│  │ }                             │                               │
│  └──────────────────────────────┘                               │
│                                                                   │
│  ┌────────────────────────────────────────┐                     │
│  │ Internal Services                      │                     │
│  ├────────────────────────────────────────┤                     │
│  │ • arxiv_service: Paper discovery       │                     │
│  │ • digest_service: Report generation    │                     │
│  │ • agent.py: LangGraph orchestration    │                     │
│  │ • chat_service: Conversation logic     │                     │
│  │ • auth: JWT validation                 │                     │
│  └────────────────────────────────────────┘                     │
│                                                                   │
│  ┌────────────────────────────────────────┐                     │
│  │ External Services                      │                     │
│  ├────────────────────────────────────────┤                     │
│  │ • ArXiv API: Paper search               │                     │
│  │ • LLM (OpenAI/Claude): Analysis        │                     │
│  │ • PostgreSQL: Data persistence         │                     │
│  └────────────────────────────────────────┘                     │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow Diagrams

### Research Query Flow

```
User Input
    │
    ▼
┌─────────────────────────────────┐
│ UnifiedChatInput detects type   │
└─────────────────────────────────┘
    │
    ├─ Query Detection
    │  └─ queryDetector.detectQueryType()
    │
    ▼
┌─────────────────────────────────┐
│ Type = RESEARCH?                │
└─────────────────────────────────┘
    │ YES
    ▼
┌─────────────────────────────────┐
│ Show Advanced Options           │
│ • Depth selector               │
│ • Max papers slider            │
└─────────────────────────────────┘
    │
    ▼ User submits with options
┌─────────────────────────────────────────────────────┐
│ POST /api/research-agent/research-stream (SSE)      │
│ Body: {query, depth, max_papers}                    │
└─────────────────────────────────────────────────────┘
    │
    ▼ Backend Processing
┌──────────────────────────────────────────────────┐
│ LangGraph Workflow (agent.py)                     │
│ ├─ search_papers: Query ArXiv API                 │
│ ├─ analyze_papers: Score relevance (LLM)         │
│ ├─ decide_continue: Evaluate sufficiency          │
│ ├─ refine_search: Generate related terms (LLM)   │
│ ├─ generate_digest: Create report (LLM)          │
│ └─ error_handler: Handle failures                 │
└──────────────────────────────────────────────────┘
    │
    ├─ SSE Event 1: initialized
    ├─ SSE Event 2: searching
    ├─ SSE Event 3: papers_found (15 papers)
    ├─ SSE Event 4: analyzing
    ├─ SSE Event 5: papers_found (25 papers)
    ├─ SSE Event 6: refining
    ├─ SSE Event 7: papers_found (32 papers)
    ├─ SSE Event 8: generating_digest
    └─ SSE Event 9: completed (with digest)
    │
    ▼ Frontend Processing
┌──────────────────────────────────────┐
│ ResearchDigestStream                 │
│ ├─ Progress Header (live updates)    │
│ ├─ Event Timeline                    │
│ └─ Tips Section                      │
└──────────────────────────────────────┘
    │
    ▼ Final Rendering
┌──────────────────────────────────────┐
│ ResearchDigestViewEnhanced           │
│ ├─ Overview Tab                      │
│ ├─ Key Findings Tab                  │
│ ├─ Papers Tab (with cards)           │
│ ├─ Trends Tab                        │
│ ├─ Limitations Section               │
│ └─ Export Buttons                    │
└──────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────┐
│ Message added to history             │
│ ├─ User message (query)              │
│ └─ Assistant message (digest view)   │
└──────────────────────────────────────┘
```

### Chat Query Flow

```
User Input
    │
    ▼
┌─────────────────────────────────┐
│ UnifiedChatInput detects type   │
└─────────────────────────────────┘
    │
    ├─ Query Detection
    │  └─ queryDetector.detectQueryType()
    │
    ▼
┌─────────────────────────────────┐
│ Type = CHAT?                    │
└─────────────────────────────────┘
    │ YES
    ▼
┌─────────────────────────────────┐
│ Hide Advanced Options           │
│ Show simple submit button       │
└─────────────────────────────────┘
    │
    ▼ User submits
┌─────────────────────────────────────────────────────┐
│ POST /api/chat                                      │
│ Body: {message, chat_id?}                           │
└─────────────────────────────────────────────────────┘
    │
    ▼ Backend Processing
┌──────────────────────────────────────────────────┐
│ Chat Service                                      │
│ ├─ Load conversation history (if chat_id exists) │
│ ├─ Generate response with LLM                    │
│ └─ Save message to database                      │
└──────────────────────────────────────────────────┘
    │
    ▼ Receive response
┌──────────────────────────────────────┐
│ Assistant response text              │
└──────────────────────────────────────┘
    │
    ▼ Frontend Rendering
┌──────────────────────────────────────┐
│ Chat Bubble (Gray)                   │
│ └─ Text response                     │
└──────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────┐
│ Message added to history             │
│ ├─ User message (chat)               │
│ └─ Assistant message (chat)          │
└──────────────────────────────────────┘
```

## Component Dependencies

```
UnifiedChatPage
├── imports UnifiedChatInput
├── imports ResearchDigestViewEnhanced
├── imports ResearchDigestStream
└── uses queryDetector (indirectly via UnifiedChatInput)
    │
    ├─ UnifiedChatInput
    │  ├── imports queryDetector
    │  └── calls detectQueryType()
    │
    ├─ ResearchDigestViewEnhanced
    │  ├── imports ResearchPaperCard
    │  └── displays ResearchDigestFull data
    │
    └─ ResearchDigestStream
       └── shows SSE event timeline
```

## State Management Flow

```
UnifiedChatPage State:
├─ messages: Message[] (history)
├─ isLoading: boolean (loading state)
└─ streamingEvents: any[] (SSE events)

UnifiedChatInput State:
├─ input: string (textarea value)
├─ queryType: 'research' | 'chat' (auto-detected)
├─ showAdvanced: boolean (toggle advanced options)
├─ depth: 'quick' | 'balanced' | 'deep'
└─ maxPapers: number (5-50)

ResearchDigestViewEnhanced State:
└─ activeTab: 'overview' | 'findings' | 'papers' | 'trends'

ResearchDigestStream State:
├─ events: StreamEvent[] (timeline)
└─ currentStatus: string (latest event type)
```

## API Contract

### Research Endpoint (Streaming)
```
POST /api/research-agent/research-stream
Authorization: Bearer {token}
Content-Type: application/json

Request:
{
  "query": "string (5-2000 chars)",
  "depth": "quick|balanced|deep",
  "max_papers": number (1-50),
  "chat_id"?: string (optional)
}

Response: text/event-stream
data: {"event": "initialized", "data": {...}}
data: {"event": "searching", "data": {...}}
data: {"event": "papers_found", "data": {"papers_count": 15, ...}}
data: {"event": "analyzing", "data": {...}}
data: {"event": "refining", "data": {...}}
data: {"event": "generating_digest", "data": {...}}
data: {"event": "completed", "data": {"digest": ResearchDigestFull}}
```

### Chat Endpoint
```
POST /api/chat
Authorization: Bearer {token}
Content-Type: application/json

Request:
{
  "message": "string",
  "chat_id"?: "string"
}

Response:
{
  "response": "string",
  "chat_id": "string (optional)",
  "message_id": "string (optional)"
}
```

## Performance Considerations

1. **Message Rendering**: O(n) where n = number of messages
   - Consider virtualizing for 1000+ messages
   - Use React.memo for message components

2. **Query Detection**: O(m) where m = input length
   - Debounce detection to avoid re-calculating on every keystroke
   - Cache results for duplicate inputs

3. **SSE Streaming**: Real-time events
   - Efficient event parsing (trim whitespace)
   - Clean up intervals/listeners on component unmount

4. **Digest Rendering**: O(p) where p = papers count
   - Lazy-load paper cards
   - Pagination for large paper lists

## Security Considerations

1. **Authentication**: JWT Bearer token required
   - Stored in localStorage (not HttpOnly - adjust for better security)
   - Included in Authorization header for all requests

2. **Input Validation**: Query length limits (5-2000 chars)
   - Textarea maxlength enforced
   - Backend validation required

3. **CORS**: Frontend-backend communication
   - Configure CORS on backend
   - Allow credentials for cross-origin requests

4. **XSS Prevention**: React escaping
   - All user input rendered through React (no innerHTML)
   - Markdown/HTML should be sanitized if rendered

---

**Architecture Version**: 1.0
**Last Updated**: Current Session
**Status**: ✅ Complete and documented
