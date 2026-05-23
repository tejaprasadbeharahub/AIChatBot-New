# Project 13 — Setup & Deployment Guide

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Node.js 18+
- N8N (self-hosted or cloud)
- LiteLLM proxy (or direct API keys)

### Environment Setup

#### 1. Backend Configuration

```bash
# Create .env file in backend directory
cd backend
cp .env.example .env

# Edit .env with your values:
LITELLM_PROXY_URL=http://litellm.amzur.com:4000
LITELLM_API_KEY=sk-xxx-your-key
LLM_MODEL=gemini/gemini-2.5-flash
DATABASE_URL=postgresql+psycopg2://postgres:password@localhost:5432/amzur_ai_chat
```

#### 2. Database Setup

```bash
# Run migrations
cd backend
alembic upgrade head

# Verify tables created:
# - workflow_requests
# - research_results
```

#### 3. Install Dependencies

```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend (if needed)
cd frontend
npm install
```

### Running the Application

#### Terminal 1: Backend API

```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

Verify routes:
```bash
curl http://localhost:8000/openapi.json | grep -E '"(/api/workflow|/api/agent|/api/research)"'
```

#### Terminal 2: Frontend (Optional)

```bash
cd frontend
npm run dev
```

#### Terminal 3: N8N (If local)

```bash
# Using Docker
docker run -it --rm \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  n8nio/n8n

# Access: http://localhost:5678
```

---

## API Testing

### Test API 1: Create Workflow Task

```bash
curl -X POST http://localhost:8000/api/workflow/task \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test@example.com",
    "message": "Research modern Python async patterns and best practices"
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Workflow request created successfully",
  "status": "PENDING"
}
```

**Database Check:**
```sql
SELECT id, user_id, user_message, workflow_status FROM workflow_requests 
WHERE user_id = 'test@example.com' 
ORDER BY created_at DESC LIMIT 1;
```

---

### Test API 2: Classify Request

```bash
curl -X POST http://localhost:8000/api/agent/classify \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Research modern Python async patterns and best practices"
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "priority": "HIGH",
  "category": "RESEARCH",
  "confidence": 88,
  "workflow_status": "CLASSIFIED"
}
```

**Database Check:**
```sql
SELECT id, priority, category, confidence_score, workflow_status FROM workflow_requests 
WHERE user_id = 'test@example.com' 
ORDER BY created_at DESC LIMIT 1;
```

Expected: `priority=HIGH, category=RESEARCH, confidence_score=88, workflow_status=CLASSIFIED`

---

### Test API 3: Research Analysis

```bash
curl -X POST http://localhost:8000/api/research/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "message": "Research modern Python async patterns and best practices"
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "workflow_status": "RESEARCH_COMPLETED",
  "research_result": {
    "summary": "Modern Python async patterns...",
    "key_points": ["asyncio library", "structured concurrency", "error handling patterns"],
    "recommendations": ["Use async/await", "Implement proper error handling", "Monitor concurrency"],
    "risks": ["Deadlocks", "Race conditions", "Resource exhaustion"],
    "next_steps": ["Set up structured logging", "Create monitoring dashboards", "Document patterns"],
    "confidence_score": 92
  }
}
```

**Database Check:**
```sql
SELECT id, request_id, summary, confidence_score FROM research_results 
WHERE request_id = '550e8400-e29b-41d4-a716-446655440000';

SELECT id, workflow_status FROM workflow_requests 
WHERE id = '550e8400-e29b-41d4-a716-446655440000';
```

Expected: `workflow_status=RESEARCH_COMPLETED`

---

## N8N Workflow Setup

### Step 1: Import Workflow Template

1. Open N8N Dashboard
2. Click "New Workflow"
3. Click "Import from File" or paste JSON from [N8N_WORKFLOW_TEMPLATE.json](N8N_WORKFLOW_TEMPLATE.json)

### Step 2: Configure Webhook

1. Click "Webhook Trigger" node
2. Set webhook route: `/workflow-task`
3. Copy webhook URL: `https://n8n.example.com/webhook/workflow-task`

### Step 3: Set Environment Variables

In N8N or backend `.env`:
```
WEBHOOK_URL=https://n8n.example.com/webhook/workflow-task
LITELLM_PROXY_URL=http://litellm.amzur.com:4000
LITELLM_API_KEY=sk-xxx
```

### Step 4: Test N8N Workflow

```bash
# Send test request to N8N webhook
curl -X POST https://n8n.example.com/webhook/workflow-task \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "n8n-test@example.com",
    "message": "Investigate distributed tracing for microservices architecture"
  }'
```

Expected flow:
1. N8N webhook captures request
2. API 1 creates task (status: PENDING)
3. API 2 classifies (priority, category, confidence)
4. Branch decision:
   - If HIGH+RESEARCH → API 3 performs research
   - Else → Route to alternate workflow
5. Result stored in database and forwarded

---

## Monitoring & Logging

### View Application Logs

```bash
# Backend logs (if using structured logging)
tail -f logs/api.log | grep research_

# Database queries
psql -U postgres -d amzur_ai_chat -c "SELECT * FROM workflow_requests ORDER BY created_at DESC LIMIT 10;"
```

### Check API Health

```bash
# Health endpoint
curl http://localhost:8000/health

# OpenAPI documentation
curl http://localhost:8000/openapi.json

# Specific routes
curl http://localhost:8000/openapi.json | jq '.paths | keys[]' | grep -E "(workflow|agent|research)"
```

---

## Troubleshooting

### Issue: LiteLLM Connection Timeout

**Error:**
```
litellm.exceptions.APIConnectionError: Request timed out
```

**Solution:**
```bash
# Verify LiteLLM is running
curl http://litellm.amzur.com:4000/health

# Check API key
echo $LITELLM_API_KEY

# Increase timeout in config
N8N_CLASSIFICATION_TIMEOUT_SECONDS=30
```

### Issue: Database Connection Error

**Error:**
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Solution:**
```bash
# Verify PostgreSQL is running
psql -U postgres -c "SELECT version();"

# Check connection string
echo $DATABASE_URL

# Test connection
python -c "from sqlalchemy import create_engine; engine = create_engine('$DATABASE_URL'); print(engine.connect())"
```

### Issue: JSON Parsing Failure

**Error:**
```
json.JSONDecodeError: Expecting value at line 1
```

**Solution:**
- Check LLM response is valid JSON
- Enable fallback: `N8N_CLASSIFICATION_ENABLE_FALLBACK=true`
- Check logs for raw AI response

### Issue: Research Results Not Stored

**Error:**
```
research_result_persistence_failed
```

**Solution:**
```sql
-- Verify research_results table exists
SELECT * FROM information_schema.tables WHERE table_name='research_results';

-- Check for constraint violations
SELECT constraint_name, table_name FROM information_schema.table_constraints 
WHERE constraint_type='FOREIGN KEY';

-- Re-run migrations if needed
alembic upgrade head
```

---

## Performance Tuning

### Connection Pooling

```python
# app/core/config.py
DATABASE_URL = "postgresql+psycopg2://...",
SQLALCHEMY_POOL_SIZE = 20
SQLALCHEMY_POOL_RECYCLE = 3600
```

### LiteLLM Retry Strategy

```env
# Increase for critical workloads
N8N_CLASSIFICATION_RETRY_ATTEMPTS=5
N8N_CLASSIFICATION_TIMEOUT_SECONDS=30

# Disable fallback for higher reliability (vs availability)
N8N_CLASSIFICATION_ENABLE_FALLBACK=false
```

### Database Indexing

```sql
-- Verify indexes exist
SELECT indexname FROM pg_indexes WHERE tablename='workflow_requests';
SELECT indexname FROM pg_indexes WHERE tablename='research_results';

-- Create additional indexes if needed
CREATE INDEX idx_workflow_requests_created_at 
  ON workflow_requests(created_at DESC);
```

---

## Production Deployment

### Docker Compose Setup

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  backend:
    build: ./backend
    environment:
      DATABASE_URL: postgresql+psycopg2://postgres:secure_password@postgres:5432/amzur_ai_chat
      LITELLM_API_KEY: ${LITELLM_API_KEY}
    ports:
      - "8000:8000"
    depends_on:
      - postgres

  n8n:
    image: n8nio/n8n
    environment:
      DB_TYPE: postgresql
      DB_POSTGRESDB_USER: postgres
      DB_POSTGRESDB_PASSWORD: secure_password
      DB_POSTGRESDB_HOST: postgres
    ports:
      - "5678:5678"
    depends_on:
      - postgres
```

```bash
# Deploy
docker-compose up -d

# Verify
docker-compose ps
```

---

## Validation Checklist

- [ ] PostgreSQL running and migrations applied
- [ ] Backend API starts without errors
- [ ] API 1 (`/api/workflow/task`) creates rows in workflow_requests
- [ ] API 2 (`/api/agent/classify`) updates workflow_requests with classification
- [ ] API 3 (`/api/research/analyze`) creates research_results and updates workflow status
- [ ] LiteLLM integration working with proper retry/timeout
- [ ] N8N workflow imported and configured
- [ ] Webhook connection verified between N8N and backend
- [ ] Database transactions properly rolled back on errors
- [ ] Structured logging enabled and capturing events
- [ ] All required environment variables set

---

## Support & Documentation

- **FastAPI Docs:** http://localhost:8000/docs
- **Project 13 Guide:** [PROJECT_13_COMPLETE_GUIDE.md](PROJECT_13_COMPLETE_GUIDE.md)
- **N8N Docs:** https://docs.n8n.io/
- **LiteLLM Docs:** https://docs.litellm.ai/
