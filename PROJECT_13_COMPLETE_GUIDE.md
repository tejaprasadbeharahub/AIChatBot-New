# Project 13: N8N Workflow Automation System – Complete Implementation Guide

## Overview

This document describes the complete implementation of Project 13, which consists of three integrated APIs designed to work together within an N8N workflow automation system:

1. **API 1 — Workflow Trigger API** (`POST /api/workflow/task`)
2. **API 2 — AI Classification API** (`POST /api/agent/classify`)
3. **API 3 — Research Agent API** (`POST /api/research/analyze`)

---

## Architecture: Three-Stage N8N Pipeline

```
┌──────────────────────────────────────────────────────────────────┐
│                      N8N WORKFLOW AUTOMATION                      │
└──────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │  API 1: Task Creation   │
                    │   /api/workflow/task    │
                    │                         │
                    │ Input: user_id, message │
                    │ Output: request_id      │
                    │ Status: PENDING         │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │ API 2: Classification   │
                    │  /api/agent/classify    │
                    │                         │
                    │ Input: message          │
                    │ Output: priority,       │
                    │         category,       │
                    │         confidence      │
                    │ Status: CLASSIFIED      │
                    └────────────┬────────────┘
                                 │
                  ┌──────────────┴──────────────┐
                  │                             │
              (HIGH+RESEARCH)            (OTHER)
                  │                             │
                  ▼                             ▼
         ┌─────────────────────┐    ┌──────────────────┐
         │ API 3: Research     │    │  Other Workflows │
         │  /api/research/     │    │  (Email, Slack,  │
         │      analyze        │    │   Logging, etc)  │
         │                     │    │                  │
         │ Input: request_id   │    └──────────────────┘
         │ Output: analysis    │
         │ Status:             │
         │ RESEARCH_COMPLETED  │
         └─────────────────────┘
```

---

## API Implementation Details

### API 1: Workflow Trigger API

**Endpoint:** `POST /api/workflow/task`

**Purpose:** Entry point for N8N; creates a task request record.

**Request:**
```json
{
  "user_id": "user@example.com",
  "message": "Implement multi-agent orchestration pattern"
}
```

**Response:**
```json
{
  "success": true,
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Workflow request created successfully",
  "status": "PENDING"
}
```

**Database State:**
- Creates row in `workflow_requests` table
- Status: `PENDING`
- Fields: `id`, `user_id`, `user_message`, `category` (null), `priority` (null), `confidence_score` (null), `workflow_status` (PENDING), `created_at`

**Key Files:**
- Route: [backend/app/api/workflow.py](backend/app/api/workflow.py)
- Schema: [backend/app/schemas/workflow.py](backend/app/schemas/workflow.py)
- Service: [backend/app/services/workflow/workflow_service.py](backend/app/services/workflow/workflow_service.py)
- Model: [backend/app/models/workflow_request.py](backend/app/models/workflow_request.py)

---

### API 2: AI Classification API

**Endpoint:** `POST /api/agent/classify`

**Purpose:** Classifies the workflow message using LiteLLM; extracts priority, category, and confidence.

**Request:**
```json
{
  "message": "Implement multi-agent orchestration pattern"
}
```

**Response:**
```json
{
  "success": true,
  "priority": "HIGH",
  "category": "RESEARCH",
  "confidence": 92,
  "workflow_status": "CLASSIFIED"
}
```

**Classification Categories:**
- **Priority:** HIGH | MEDIUM | LOW
- **Category:** RESEARCH | BUG | FEATURE | SUPPORT | DOCUMENTATION | GENERAL

**Business Logic:**
1. Accepts message
2. Calls LiteLLM with strict JSON prompt
3. Extracts priority, category, confidence from AI response
4. Finds latest PENDING workflow request with matching message
5. Updates workflow request: sets priority, category, confidence, status→CLASSIFIED
6. Returns structured response

**Database State:**
- Updates matching row in `workflow_requests`
- Status: `CLASSIFIED`
- Populated: `priority`, `category`, `confidence_score`

**Key Files:**
- Route: [backend/app/api/agent.py](backend/app/api/agent.py)
- Schema: [backend/app/schemas/agent.py](backend/app/schemas/agent.py)
- Service: [backend/app/services/workflow/classification_service.py](backend/app/services/workflow/classification_service.py)
- Prompt: [backend/app/agents/classification_prompt.py](backend/app/agents/classification_prompt.py)

---

### API 3: Research Agent API

**Endpoint:** `POST /api/research/analyze`

**Purpose:** Triggered ONLY for HIGH priority + RESEARCH category; performs deep AI research analysis.

**Request:**
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Research latest LangGraph multi-agent orchestration patterns"
}
```

**Response:**
```json
{
  "success": true,
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "workflow_status": "RESEARCH_COMPLETED",
  "research_result": {
    "summary": "Comprehensive summary of multi-agent patterns...",
    "key_points": [
      "LangGraph supports hierarchical agent coordination",
      "Router agents distribute tasks efficiently",
      "State management via checkpoints enables fault tolerance"
    ],
    "recommendations": [
      "Use supervisor pattern for task routing",
      "Implement streaming for real-time updates",
      "Add retry logic for resilience"
    ],
    "risks": [
      "Token limits on large context windows",
      "Cascading failures in complex orchestration",
      "Performance degradation with many agents"
    ],
    "next_steps": [
      "Prototype with 3-agent orchestration",
      "Benchmark performance metrics",
      "Document best practices"
    ],
    "confidence_score": 94
  }
}
```

**Database State:**
- Creates row in `research_results` table
- Updates workflow request: status → RESEARCH_COMPLETED
- Fields: `id`, `request_id`, `summary`, `key_points`, `recommendations`, `risks`, `next_steps`, `confidence_score`, `created_at`

**Key Files:**
- Route: [backend/app/api/research.py](backend/app/api/research.py)
- Schema: [backend/app/schemas/research.py](backend/app/schemas/research.py)
- Service: [backend/app/services/workflow/research_service.py](backend/app/services/workflow/research_service.py)
- Prompt: [backend/app/agents/research_prompt.py](backend/app/agents/research_prompt.py)
- Model: [backend/app/models/research_result.py](backend/app/models/research_result.py)

---

## N8N Workflow Configuration

### Step 1: Webhook Trigger (Entry Point)

```yaml
Trigger: Webhook
Method: POST
Route: /workflow-task
Purpose: Receives workflow requests from frontend/external systems
```

### Step 2: Call API 1 — Create Task

```yaml
HTTP Request Node:
  URL: http://localhost:8000/api/workflow/task
  Method: POST
  Body:
    user_id: "{{ $json.user_id }}"
    message: "{{ $json.message }}"
  
Extract:
  request_id = response.request_id
  Save for next steps
```

### Step 3: Call API 2 — Classify

```yaml
HTTP Request Node:
  URL: http://localhost:8000/api/agent/classify
  Method: POST
  Body:
    message: "{{ $json.message }}"
  
Extract:
  priority = response.priority
  category = response.category
  confidence = response.confidence
```

### Step 4: Branch by Classification

```yaml
IF Node - Decision Logic:
  Condition: priority === "HIGH" AND category === "RESEARCH"
  
  YES Branch:
    → Call API 3 (Research Agent)
    
  NO Branch:
    → Route to other workflows
    → Log to database
    → Send notification
```

### Step 5: Call API 3 — Research (HIGH+RESEARCH only)

```yaml
HTTP Request Node:
  URL: http://localhost:8000/api/research/analyze
  Method: POST
  Body:
    request_id: "{{ $json.request_id }}"
    message: "{{ $json.message }}"
  
Extract:
  research_result = response.research_result
  confidence = response.research_result.confidence_score
```

### Step 6: Store & Notify

```yaml
# Option A: Database Insert
Insert into research_results_summary:
  - request_id
  - priority
  - category
  - summary (first 500 chars)
  - confidence_score
  - completed_at

# Option B: Send Notification
Send Email/Slack/Webhook:
  - Research completed
  - Summary
  - Key findings
  - Confidence score
```

---

## Database Schema

### workflow_requests Table

```sql
CREATE TABLE workflow_requests (
  id UUID PRIMARY KEY,
  user_id VARCHAR(255) NOT NULL,
  user_message TEXT NOT NULL,
  category VARCHAR(100),          -- RESEARCH, BUG, FEATURE, etc.
  priority VARCHAR(50),            -- HIGH, MEDIUM, LOW
  confidence_score FLOAT,          -- 0-100
  workflow_status VARCHAR(30),     -- PENDING → CLASSIFIED → RESEARCH_COMPLETED
  created_at TIMESTAMP WITH TIME ZONE,
  INDEX idx_user_id (user_id),
  INDEX idx_workflow_status (workflow_status)
);
```

### research_results Table

```sql
CREATE TABLE research_results (
  id UUID PRIMARY KEY,
  request_id UUID FOREIGN KEY,
  summary TEXT NOT NULL,
  key_points JSON NOT NULL,        -- ["point1", "point2", ...]
  recommendations JSON NOT NULL,   -- ["rec1", "rec2", ...]
  risks JSON NOT NULL,             -- ["risk1", "risk2", ...]
  next_steps JSON NOT NULL,        -- ["step1", "step2", ...]
  confidence_score INTEGER,        -- 0-100
  created_at TIMESTAMP WITH TIME ZONE,
  INDEX idx_request_id (request_id),
  INDEX idx_created_at (created_at)
);
```

---

## LiteLLM Integration

### Configuration

```env
# .env file
LITELLM_PROXY_URL=http://litellm.amzur.com:4000
LITELLM_API_KEY=your-api-key

# Classification
N8N_CLASSIFICATION_MODEL=gemini/gemini-2.5-flash
N8N_CLASSIFICATION_TIMEOUT_SECONDS=15
N8N_CLASSIFICATION_RETRY_ATTEMPTS=3
N8N_CLASSIFICATION_ENABLE_FALLBACK=true
```

### API 2 Classification Prompt

```
System:
  You are an enterprise workflow triage model.
  Classify tasks into priority/category with confidence.
  Return ONLY JSON with: priority, category, confidence (0-100)

User:
  Task: "{{ message }}"
  
Expected Output:
{
  "priority": "HIGH",
  "category": "RESEARCH",
  "confidence": 92
}
```

### API 3 Research Prompt

```
System:
  You are an expert AI research analyst.
  Provide comprehensive research analysis with:
  - summary (2-3 paragraphs)
  - key_points (array, min 3 items)
  - recommendations (array, min 3 items)
  - risks (array, min 3 items)
  - next_steps (array, min 3 items)
  - confidence_score (0-100)
  
  Return ONLY valid JSON.

User:
  Research: "{{ message }}"
  
Expected Output:
{
  "summary": "...",
  "key_points": ["...", "...", "..."],
  "recommendations": ["...", "...", "..."],
  "risks": ["...", "...", "..."],
  "next_steps": ["...", "...", "..."],
  "confidence_score": 85
}
```

---

## Implementation Checklist

- [x] API 1 — Workflow Trigger (`POST /api/workflow/task`)
- [x] API 2 — Classification (`POST /api/agent/classify`)
- [x] API 3 — Research Agent (`POST /api/research/analyze`)
- [x] Database Models: WorkflowRequest, ResearchResult
- [x] Alembic Migrations
- [x] Pydantic Schemas with validation
- [x] LiteLLM Integration with retry/timeout
- [x] Async/await architecture
- [x] Structured logging
- [x] Error handling and fallback
- [x] FastAPI route registration
- [x] Environment configuration
- [x] Production-ready code quality

---

## Usage Example: End-to-End Flow

```bash
# 1. Create workflow request (API 1)
curl -X POST http://localhost:8000/api/workflow/task \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "alice@example.com",
    "message": "Research latest LangGraph orchestration patterns for production systems"
  }'

# Response:
{
  "success": true,
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Workflow request created successfully",
  "status": "PENDING"
}

# 2. Classify the request (API 2)
curl -X POST http://localhost:8000/api/agent/classify \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Research latest LangGraph orchestration patterns for production systems"
  }'

# Response:
{
  "success": true,
  "priority": "HIGH",
  "category": "RESEARCH",
  "confidence": 92,
  "workflow_status": "CLASSIFIED"
}

# 3. If HIGH+RESEARCH, call research API (API 3)
curl -X POST http://localhost:8000/api/research/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "message": "Research latest LangGraph orchestration patterns for production systems"
  }'

# Response:
{
  "success": true,
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "workflow_status": "RESEARCH_COMPLETED",
  "research_result": {
    "summary": "LangGraph enables sophisticated multi-agent orchestration...",
    "key_points": [...],
    "recommendations": [...],
    "risks": [...],
    "next_steps": [...],
    "confidence_score": 94
  }
}
```

---

## Error Handling & Resilience

### API 2 Classification Failures

- **Timeout (>15s):** Retry with exponential backoff, fallback to LOW/GENERAL if all retries fail
- **JSON Parse Error:** Regex extraction fallback, confidence reduced to 35
- **Provider Error:** Logged with full context, fallback classification used

### API 3 Research Failures

- **LiteLLM Timeout:** Retry up to 3 times, 0.3s exponential backoff
- **JSON Parse Error:** Fallback research with confidence 45
- **Database Error:** Transaction rollback, error logged with request context
- **Missing Workflow Request:** HTTP 400 with descriptive error

---

## Next Steps & Future Enhancements

1. **Streaming Results:** Stream research analysis progress to N8N via Server-Sent Events (SSE)
2. **Advanced Routing:** Use confidence scores for additional branching logic
3. **Analytics Dashboard:** Track classification accuracy and research quality
4. **Feedback Loop:** Store user ratings of research quality for model fine-tuning
5. **Multi-Model Support:** A/B test different LLM models for classification vs. research
6. **Caching Layer:** Cache research results for common topics
7. **Webhook Notifications:** Send completed research to external systems

---

## References

- FastAPI: https://fastapi.tiangolo.com/
- SQLAlchemy: https://www.sqlalchemy.org/
- LiteLLM: https://docs.litellm.ai/
- Pydantic: https://docs.pydantic.dev/
- N8N: https://n8n.io/docs/
