# Project 10: Research Digest Agent

## Overview

The Research Digest Agent is an AI-powered autonomous system that searches arXiv for relevant research papers, analyzes their content, and generates structured research digests in real-time using Server-Sent Events (SSE).

## Features

### 🔍 Intelligent Paper Discovery
- **Iterative Search**: Starts with exact phrase matching, then expands search gradually
- **Relevance Scoring**: Uses LLM to evaluate paper relevance to your query
- **Depth Control**: Choose between quick (10), balanced (20), or deep (50) searches

### 📊 Autonomous Analysis
- **Adaptive Stopping Criteria**: Continues searching only if insufficient evidence found
- **Smart Refinement**: Generates related search terms when more papers needed
- **Relevance-Based Sorting**: Prioritizes most relevant papers for digest

### 📝 Structured Output
- **Executive Summary**: 2-3 paragraph overview
- **Key Findings**: Main discoveries with evidence papers
- **Methodologies**: Common research approaches used
- **Trends**: Emerging directions in the field
- **Limitations**: Known gaps and challenges
- **Complete Bibliography**: All cited papers with metadata

### ⚡ Real-Time Streaming
- **SSE Events**: Get live updates as research progresses
  - `searching`: Queries arXiv
  - `found_paper`: New paper discovered
  - `analyzing`: Evaluating relevance
  - `generating_digest`: Creating final report
  - `completed`: Research finished
  - `error`: Issues encountered

## Architecture

### Backend Components

#### 1. **Models** (`backend/app/models/research_session.py`)
- `ResearchSession`: Tracks query, status, papers found, digest, timestamps
- `ResearchPaper`: Stores paper metadata, relevance score, inclusion reason

#### 2. **Schemas** (`backend/app/schemas/research_agent.py`)
- `ResearchQueryRequest`: Query, max_papers, depth, optional chat_id
- `ResearchDigestResponse`: Session results with digest
- `ResearchDigestFull`: Complete structured digest
- `ResearchDigestStreamEvent`: Individual SSE events
- Supporting classes: KeyFinding, Methodology, Trend, PaperRef

#### 3. **Services**
- **arxiv_service.py**: ArXiv API integration
  - `search_papers()`: Single query search
  - `search_papers_iterative()`: Depth-based iterative search
  - `get_paper_details()`: Retrieve specific paper
  
- **agent.py**: Core research logic
  - `ResearchAgent.research()`: Main orchestration
  - Relevance scoring with keyword matching
  - LLM-based stopping criteria and query refinement
  - Paper deduplication and sorting
  
- **digest_service.py**: Report generation
  - `generate_research_digest()`: Creates structured output
  - LLM extraction of key findings, trends, limitations
  - JSON parsing from model responses

#### 4. **API Router** (`backend/app/api/research_agent.py`)
- `POST /api/research-agent/research-stream`: SSE streaming endpoint
- `POST /api/research-agent/research`: Non-streaming endpoint
- Message persistence and session tracking

### Frontend Components

#### 1. **ResearchInput.tsx**
- Query text input (5-2000 characters)
- Depth selector (quick/balanced/deep)
- Max papers slider (1-50)
- Submit button with loading state

#### 2. **ResearchDigestStream.tsx**
- Real-time progress display
- Event-based UI updates
- Status tracking (searching → analyzing → generating → completed)
- Error handling

#### 3. **ResearchPaperCard.tsx**
- Paper metadata display
- Relevance score with color coding
- Links to PDF and arXiv abstract
- Author and category info

#### 4. **ResearchDigestView.tsx**
- Displays full research report
- Executive summary section
- Key findings with evidence
- Methodologies frequency chart
- Trends with direction indicators
- Limitations list
- Complete bibliography
- Export options (JSON, Print)

### Database Schema

```sql
-- Research Sessions
CREATE TABLE research_sessions (
  id UUID PRIMARY KEY,
  chat_id UUID FOREIGN KEY,
  user_id UUID FOREIGN KEY,
  message_id UUID FOREIGN KEY (nullable),
  research_query TEXT NOT NULL,
  status VARCHAR (in_progress|completed|failed),
  papers_found INT DEFAULT 0,
  digest_summary TEXT,
  digest_full TEXT (JSON),
  error_message TEXT,
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  completed_at TIMESTAMP (nullable)
);

-- Research Papers
CREATE TABLE research_papers (
  id UUID PRIMARY KEY,
  session_id UUID FOREIGN KEY,
  arxiv_id VARCHAR NOT NULL,
  title TEXT NOT NULL,
  authors TEXT (JSON array),
  abstract TEXT NOT NULL,
  published_date VARCHAR,
  categories TEXT (comma-separated),
  pdf_url VARCHAR NOT NULL,
  relevance_score FLOAT DEFAULT 0.0,
  inclusion_reason TEXT,
  created_at TIMESTAMP
);
```

## API Endpoints

### 1. POST /api/research-agent/research-stream
**Streaming Research Endpoint (Recommended)**

**Request:**
```json
{
  "query": "machine learning in healthcare",
  "max_papers": 20,
  "depth": "balanced",
  "chat_id": "optional-uuid"
}
```

**Response:** Server-Sent Events stream
```
data: {"event": "started", "session_id": "uuid"}
data: {"event": "searching", "data": {"query": "..."}}
data: {"event": "found_paper", "data": {"arxiv_id": "...", "title": "..."}}
data: {"event": "analyzing", "data": {"message": "..."}}
data: {"event": "generating_digest", "data": {"message": "..."}}
data: {"event": "completed", "data": {"session_id": "...", "papers_found": 15}}
```

### 2. POST /api/research-agent/research
**Non-Streaming Research Endpoint**

**Request:** Same as above

**Response:**
```json
{
  "session_id": "uuid",
  "chat_id": "uuid",
  "user_message_id": "uuid",
  "assistant_message_id": "uuid",
  "query": "...",
  "digest": { /* ResearchDigestFull */ },
  "search_duration_seconds": 45,
  "papers_found": 15
}
```

## Usage Example

### Frontend (React + TypeScript)
```typescript
import { ResearchInput } from './components/ResearchInput';
import { ResearchDigestStream } from './components/ResearchDigestStream';
import { ResearchDigestView } from './components/ResearchDigestView';

export function ResearchPage() {
  const [digest, setDigest] = useState(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [query, setQuery] = useState('');

  const handleSearch = async (q: string, depth: string, maxPapers: number) => {
    setQuery(q);
    setIsStreaming(true);

    try {
      const response = await fetch('/api/research-agent/research', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: q,
          depth,
          max_papers: maxPapers,
        }),
      });

      const data = await response.json();
      setDigest(data.digest);
    } finally {
      setIsStreaming(false);
    }
  };

  return (
    <div className="space-y-6">
      <ResearchInput onSearch={handleSearch} isLoading={isStreaming} />
      <ResearchDigestStream isActive={isStreaming} />
      {digest && <ResearchDigestView digest={digest} query={query} />}
    </div>
  );
}
```

## Configuration

### Environment Variables
```bash
# Backend (backend/.env)
RESEARCH_MAX_PAPERS=20              # Hard limit for papers
RESEARCH_TIMEOUT_SECONDS=120        # Overall timeout
RESEARCH_DEFAULT_DEPTH=balanced     # Default search depth

# ArXiv API
ARXIV_MAX_PAPERS=50                 # API rate limit
ARXIV_TIMEOUT_SECONDS=10           # Per-request timeout
```

### backend/app/core/config.py
```python
research_max_papers: int = 20
research_timeout_seconds: int = 120
research_default_depth: str = "balanced"
```

## Error Handling

### Common Errors

1. **Invalid Query**
   - Status: 400
   - Message: "Query must be at least 3 characters."
   - Solution: Provide a longer, more specific query

2. **API Failure**
   - Status: 503
   - Message: "Failed to reach arXiv API"
   - Solution: Check internet connection, retry after delay

3. **Session Not Found**
   - Status: 404
   - Message: "Research session not found"
   - Solution: Session may have expired (10+ minutes)

4. **Insufficient Papers**
   - Status: 200 + partial results
   - Indicates: Fewer papers found than requested
   - Solution: Query too specific, try broader search

## Performance Considerations

### Timing Expectations
- **Quick (10 papers)**: 5-15 seconds
- **Balanced (20 papers)**: 15-45 seconds
- **Deep (50 papers)**: 60-120 seconds (may timeout)

### Optimization Tips
1. Use **balanced depth** for most queries
2. Limit max_papers to 20-30 for reliability
3. Keep queries focused (3-5 key terms)
4. Avoid too-general topics (e.g., "AI" → "LLM applications")

### Rate Limiting
- ArXiv API: ~1 request/second
- LLM calls: ~5-10 per research session
- No user-level rate limits (add if needed)

## Future Enhancements

1. **Multi-Database Support**
   - Add PubMed, IEEE Xplore, Google Scholar
   - Cross-database deduplication

2. **Citation Network Analysis**
   - Find most-cited papers automatically
   - Build paper dependency graphs

3. **Full-Text Analysis**
   - Download and parse full PDFs
   - Extract methods, results, conclusions

4. **Custom Filters**
   - Date range, conference, author filters
   - Category-based narrowing

5. **Batch Research**
   - Multiple queries simultaneously
   - Comparative research between topics

6. **Export Formats**
   - PDF with formatting
   - BibTeX bibliography
   - Reference managers (Zotero, Mendeley)

## Troubleshooting

### Research Takes Too Long
- Reduce max_papers to 10-15
- Switch to "quick" depth
- Use more specific query terms

### No Papers Found
- Broaden your query (fewer specifics)
- Check query spelling
- Try related terms

### Digest Looks Incomplete
- Ensure papers_found > 0
- Check digest_full JSON field
- Re-run research with different depth

### Frontend Components Not Appearing
- Verify imports: `from '@/components/Research*'`
- Check Tailwind CSS configuration
- Ensure React 18+ compatibility

## Support & Contribution

For issues, improvements, or new features:
1. Check existing GitHub issues
2. Create detailed bug report with:
   - Query used
   - Error message/screenshot
   - Browser/device info
   - Steps to reproduce

3. Submit PRs with tests and documentation

---

**Status**: ✅ Project 10 Implementation Complete
**Last Updated**: 2026-05-15
**Maintainer**: AI Development Team
