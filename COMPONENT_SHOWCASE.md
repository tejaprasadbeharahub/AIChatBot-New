# Component Showcase & Usage Examples

## Visual Component Layout

### 1. UnifiedChatPage Layout

```
┌─────────────────────────────────────────────────────┐
│     🤖 AI Research & Chat Assistant                │ ← Header
├─────────────────────────────────────────────────────┤
│                                                      │
│  Ask research questions or chat naturally - I'll    │
│  handle both!                                        │
│                                                      │
├─────────────────────────────────────────────────────┤
│                                                      │
│                    💬 Message Area                   │
│                                                      │
│  ┌────────────────────────────────────────────┐    │
│  │ User (right):                              │    │
│  │ ┌──────────────────────────┐               │    │
│  │ │ What are recent advances  │ 🔬 Research  │    │
│  │ │ in quantum computing?     │               │    │
│  │ └──────────────────────────┘               │    │
│  └────────────────────────────────────────────┘    │
│                                                      │
│  ┌────────────────────────────────────────────┐    │
│  │ Assistant (left):                          │    │
│  │                                             │    │
│  │ 📋 Research Digest                          │    │
│  │ ════════════════════════════════════════    │    │
│  │ Query: What are recent advances...         │    │
│  │                                             │    │
│  │ [Tabs] Overview │ Findings │ Papers │ Trends │  │
│  │ ...                                         │    │
│  │ [Export as JSON] [Print]                   │    │
│  │                                             │    │
│  └────────────────────────────────────────────┘    │
│                                                      │
├─────────────────────────────────────────────────────┤
│                                                      │
│              📝 Input Area                           │
│                                                      │
│  ┌─────────────────────────────────────────────┐   │
│  │ Ask a research question... (🔬 Research)    │   │
│  │ 200/2000 characters                         │   │
│  │ [⚙️ Advanced Options]                        │   │
│  │                                              │   │
│  │ [🔬 Research] [↔️]                           │   │
│  │                                              │   │
│  │ 💡 Tips:                                     │   │
│  │ • Use keywords like \"advances\", \"trends\" │   │
│  │ • Be specific for better results            │   │
│  │ • The system auto-detects query type        │   │
│  │                                              │   │
│  └─────────────────────────────────────────────┘   │
│                                                      │
└─────────────────────────────────────────────────────┘
```

### 2. UnifiedChatInput States

#### Default State (Chat)
```
┌────────────────────────────────────────────┐
│ Ask anything... (💬 Chat)            [⚙️]  │
│ Your question here...                      │
│ 35/2000 characters                         │
│                                             │
│                         [💬 Chat] [↔️]     │
│                                             │
│ 💡 Tips:                                   │
│ • Ask general questions naturally         │
│ • Have a conversation                     │
│ • System auto-detects research queries    │
└────────────────────────────────────────────┘
```

#### Research Mode with Advanced Options
```
┌────────────────────────────────────────────┐
│ Ask a research question... (🔬 Research)   │
│ latest advances in [textarea autofills]    │
│ 50/2000 characters                         │
│                                             │
│ ⚙️ Advanced Options                        │
│ ┌──────────────────────────────────────┐   │
│ │ Search Depth                         │   │
│ │ ○ Quick   (10 papers)               │   │
│ │ ● Balanced (20 papers) ← recommended│   │
│ │ ○ Deep    (50 papers)               │   │
│ │ • Quick: Fast search, fewer papers  │   │
│ │ • Balanced: Good mix (recommended)  │   │
│ │ • Deep: Comprehensive (may timeout) │   │
│ │                                     │   │
│ │ Max Papers: 20                       │   │
│ │ |─────●─────────| 5    50           │   │
│ │ Collect between 5-50 papers         │   │
│ │                                     │   │
│ │ [✕ Hide Advanced Options]            │   │
│ └──────────────────────────────────────┘   │
│                                             │
│                    [🔬 Research] [↔️]      │
│                                             │
│ 💡 Tips:                                   │
│ • Use keywords like \"advances\", \"trends\"│
│ • Ask about specific topics               │
│ • Be specific for better results          │
└────────────────────────────────────────────┘
```

### 3. ResearchDigestStream (Progress Visualization)

```
┌─────────────────────────────────────────┐
│ 🔬 Research in Progress                 │
│                                         │
│  Papers Found: 32   Avg Relevance: 78%  │
│  Status: Generating Digest              │
│                                         │
│  [████████████░░░░░░] 89% Complete      │
│                                         │
│ Event Timeline                          │
│ ─────────────────                       │
│                                         │
│ 🚀 Initialized                 12:34:56 │
│    Starting research workflow...        │
│                                         │
│ 🔍 Searching Papers             12:34:57│
│    Searching arXiv...                   │
│                                         │
│ 📄 Papers Found                 12:34:59│
│    📄 15 papers, ⭐ 65% avg relevance   │
│                                         │
│ 📊 Analyzing                    12:35:01│
│    Analyzing relevance scores...        │
│                                         │
│ 📄 Papers Found                 12:35:03│
│    📄 25 papers, ⭐ 72% avg relevance   │
│                                         │
│ 🔧 Refining Search              12:35:05│
│    Refining search criteria...          │
│                                         │
│ 📄 Papers Found                 12:35:07│
│    📄 32 papers, ⭐ 78% avg relevance   │
│                                         │
│ ✍️ Generating Digest            12:35:09│
│    Generating research digest...        │
│                                         │
│ ⏳ Processing...                 12:35:10│
│                                         │
│ 💡 What's happening?                    │
│ • 🔍 Searching: Looking for papers     │
│ • 📊 Analyzing: Computing relevance     │
│ • 🔧 Refining: Adjusting search terms   │
│ • ✍️ Generating: Creating digest        │
└─────────────────────────────────────────┘
```

### 4. ResearchDigestViewEnhanced (Results Display)

#### Overview Tab
```
┌─────────────────────────────────────────────┐
│ Research Digest                             │
│ Quantum Computing: Latest Advances          │
│ 📊 Papers Reviewed: 32 | Avg Relevance: 78% │ 
│ ⏱️ Search Duration: 45s                     │
├─────────────────────────────────────────────┤
│                                              │
│ [Overview] Findings │ Papers │ Trends      │
│                                              │
│ Executive Summary                           │
│ ┌────────────────────────────────────────┐  │
│ │ This research digest synthesizes 32    │  │
│ │ recent papers from arXiv focusing on   │  │
│ │ quantum computing advances. Key areas  │  │
│ │ include: error correction, quantum     │  │
│ │ algorithms, and hardware implementations. │
│ │                                         │  │
│ │ The field shows significant progress   │  │
│ │ with emphasis on practical applications.│  │
│ └────────────────────────────────────────┘  │
│                                              │
│ Quick Stats                                  │
│ ┌──────┐  ┌──────┐  ┌──────────┐           │
│ │ 32   │  │ 8    │  │ 5        │           │
│ │Papers│  │Find. │  │Research  │           │
│ │ 📊   │  │🔍   │  │Areas     │           │
│ │      │  │      │  │          │           │
│ └──────┘  └──────┘  └──────────┘           │
│                                              │
│                      [📥 Export] [🖨️ Print] │
└─────────────────────────────────────────────┘
```

#### Key Findings Tab
```
┌─────────────────────────────────────────────┐
│ [Overview] Findings │ Papers │ Trends      │
│                                              │
│ 🔍 Error Correction Advances                │
│    Recent breakthroughs in quantum error    │
│    correction show promise for practical    │
│    applications. Surface codes and         │
│    topological approaches dominate.        │
│    [arxiv-1234] [arxiv-5678] [arxiv-91011] │
│    (+2 more)                                │
│                                              │
│ 🔍 Algorithm Development                    │
│    New quantum algorithms demonstrate      │
│    potential for solving optimization      │
│    problems with applications in           │
│    chemistry and materials science.        │
│    [arxiv-1111] [arxiv-2222]               │
│                                              │
│ 🔍 Hardware Scaling                         │
│    Industry leaders report increased        │
│    qubit counts with improved stability.    │
│    Multi-supplier landscape emerging.       │
│    [arxiv-3333] [arxiv-4444] [arxiv-5555]  │
│    (+1 more)                                │
│                                              │
│ 🔍 Applications in Industry                 │
│    Growing interest in quantum machine      │
│    learning and drug discovery.             │
│    Early pilots underway at major firms.    │
│    [arxiv-6666]                             │
│                                              │
└─────────────────────────────────────────────┘
```

#### Papers Tab
```
┌─────────────────────────────────────────────┐
│ [Overview] Findings │ Papers │ Trends      │
│                                              │
│ 📄 Showing 32 papers sorted by relevance    │
│                                              │
│ ┌──────────────────────────────────────────┐│
│ │ 📖 Surface Codes for Scalable Quantum   ││
│ │    Computing                            ││
│ │                                         ││
│ │ ✍️ Smith, J., Johnson, K., et al.     ││
│ │ 📅 Published: 2024-03-15               ││
│ │ 🏷️  quantum-error-correction, scalable ││
│ │                                         ││
│ │ 📋 This paper presents novel approaches ││
│ │    to surface code implementation...    ││
│ │                                         ││
│ │ ⭐ Relevance: 95%  📥 [View PDF]       ││
│ └──────────────────────────────────────────┘│
│                                              │
│ ┌──────────────────────────────────────────┐│
│ │ 📖 Hybrid Quantum-Classical Algorithms  ││
│ │    for Optimization                     ││
│ │                                         ││
│ │ ✍️ Williams, A., Chen, L., et al.     ││
│ │ 📅 Published: 2024-02-28               ││
│ │ 🏷️  optimization, hybrid, algorithms    ││
│ │                                         ││
│ │ ⭐ Relevance: 92%  📥 [View PDF]       ││
│ └──────────────────────────────────────────┘│
│                                              │
│ [More papers...]                            │
│                                              │
└─────────────────────────────────────────────┘
```

#### Trends Tab
```
┌─────────────────────────────────────────────┐
│ [Overview] Findings │ Papers │ Trends      │
│                                              │
│ 📈 Error Correction Importance              │
│    Direction: INCREASING                    │
│    Papers shifting focus toward error       │
│    mitigation techniques                    │
│                                              │
│ ➡️ Hardware Advancement                     │
│    Direction: STABLE                        │
│    Steady progress in qubit count and      │
│    coherence time improvements              │
│                                              │
│ 📈 Application Development                  │
│    Direction: INCREASING                    │
│    Growing emphasis on practical use cases  │
│    in industry                              │
│                                              │
│ 📉 Theoretical Foundations                  │
│    Direction: DECREASING                    │
│    Shift from pure theory to applied work   │
│                                              │
│ 📈 Hybrid Approaches                        │
│    Direction: INCREASING                    │
│    Increasing papers on quantum-classical   │
│    hybrid algorithms                        │
│                                              │
│ ⚠️ Research Limitations                     │
│ • Limited datasets for training             │
│ • Noise levels still significant            │
│ • Scalability concerns remain               │
│ • Limited commercial applications           │
│ • Hardware accessibility restrictions       │
│                                              │
└─────────────────────────────────────────────┘
```

## Component Props & Interface

### UnifiedChatInput Props

```typescript
interface UnifiedChatInputProps {
  onResearchQuery: (query: string, depth: string, maxPapers: number) => void;
  onChatQuery: (message: string) => void;
  isLoading?: boolean;
}
```

### ResearchDigestViewEnhanced Props

```typescript
interface ResearchDigestViewEnhancedProps {
  digest: ResearchDigestFull;
  query: string;
  isLoading?: boolean;
}

interface ResearchDigestFull {
  summary: string;
  key_findings: ResearchDigestFinding[];
  methodologies: { name: string; frequency: number; papers: string[] }[];
  limitations: string[];
  trends: ResearchDigestTrend[];
  total_papers_reviewed: number;
  papers_cited: ResearchPaperRef[];
  search_duration_seconds: number;
}
```

### UnifiedChatPage State

```typescript
interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  type: 'chat' | 'research';
  timestamp: Date;
  digest?: ResearchDigestFull; // For research messages
}
```

## Usage Example Code

### Basic Implementation

```typescript
import { UnifiedChatPage } from './components/UnifiedChatPage';
import './App.css';

function App() {
  return (
    <div className="h-screen flex flex-col">
      <UnifiedChatPage />
    </div>
  );
}

export default App;
```

### Custom Integration with Auth

```typescript
import { UnifiedChatPage } from './components/UnifiedChatPage';
import { useAuth } from './contexts/AuthContext';
import { Navigate } from 'react-router-dom';

function ChatPage() {
  const { isAuthenticated, user } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }

  return (
    <div>
      <header className="bg-white border-b p-4">
        <p>Welcome, {user?.name}!</p>
      </header>
      <UnifiedChatPage />
    </div>
  );
}

export default ChatPage;
```

### With Custom Error Boundary

```typescript
import { UnifiedChatPage } from './components/UnifiedChatPage';
import { ErrorBoundary } from './components/ErrorBoundary';

function App() {
  return (
    <ErrorBoundary fallback={<div>Something went wrong</div>}>
      <UnifiedChatPage />
    </ErrorBoundary>
  );
}

export default App;
```

## Styling Customization

### Change Primary Color (Research)

Edit CSS or Tailwind config:

```typescript
// In component
className={queryType === 'research' ? 'bg-purple-50 border-purple-300' : '...'}
```

### Add Custom Font

```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

body {
  font-family: 'Inter', sans-serif;
}
```

### Enable Dark Mode

```typescript
// In UnifiedChatPage.tsx
<div className="dark:bg-gray-900 dark:text-white">
  {/* Components */}
</div>
```

## Performance Optimization

### Memoized Components

```typescript
import { memo } from 'react';

const MemoizedResearchCard = memo(ResearchPaperCard);

// In parent component
<MemoizedResearchCard 
  {...props}
  key={paperId}
/>
```

### Lazy Loading

```typescript
import { lazy, Suspense } from 'react';

const ResearchDigestViewEnhanced = lazy(() =>
  import('./components/ResearchDigestViewEnhanced')
);

// In UnifiedChatPage
<Suspense fallback={<div>Loading...</div>}>
  <ResearchDigestViewEnhanced {...props} />
</Suspense>
```

### Debounced Query Detection

```typescript
import { debounce } from 'lodash-es';
import { useCallback } from 'react';

const handleInputChange = useCallback(
  debounce((text: string) => {
    const detected = detectQueryType(text);
    setQueryType(detected.type);
  }, 300),
  []
);
```

## Testing Examples

### Query Detector Test

```typescript
import { detectQueryType } from '../lib/queryDetector';

describe('queryDetector', () => {
  it('should detect research queries accurately', () => {
    const testCases = [
      { input: 'latest advances in quantum computing', expected: 'research' },
      { input: 'recent trends in machine learning', expected: 'research' },
      { input: 'what papers are trending in AI?', expected: 'research' },
      { input: 'hello, how are you?', expected: 'chat' },
      { input: 'tell me a joke', expected: 'chat' },
    ];

    testCases.forEach(({ input, expected }) => {
      const result = detectQueryType(input);
      expect(result.type).toBe(expected);
    });
  });

  it('should provide confidence scores', () => {
    const result = detectQueryType('latest quantum computing papers');
    expect(result.confidence).toBeGreaterThan(0.7);
  });
});
```

### Component Integration Test

```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { UnifiedChatPage } from '../components/UnifiedChatPage';

describe('UnifiedChatPage', () => {
  it('should route research queries', async () => {
    render(<UnifiedChatPage />);
    
    const input = screen.getByPlaceholderText(/ask a research question/i);
    await userEvent.type(input, 'latest advances in quantum');
    
    expect(screen.getByText(/🔬 Research/)).toBeInTheDocument();
  });

  it('should display results after research', async () => {
    render(<UnifiedChatPage />);
    
    const input = screen.getByPlaceholderText(/ask a research question/i);
    await userEvent.type(input, 'quantum computing');
    
    const submitBtn = screen.getByRole('button', { name: /research/i });
    fireEvent.click(submitBtn);
    
    await waitFor(() => {
      expect(screen.getByText(/Research in Progress/i)).toBeInTheDocument();
    });
  });
});
```

---

**Component Showcase Complete!** 🎉

These visual layouts and code examples should give you a clear picture of how each component looks and functions. Refer back to this document when implementing or customizing the UI.
