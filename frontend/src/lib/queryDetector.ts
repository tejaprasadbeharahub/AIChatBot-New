/**
 * Smart Chat Handler - Routes queries to research agent or general chat
 * Intelligent detection based on query keywords and patterns
 */

export interface QueryType {
  type: 'research' | 'chat';
  confidence: number;
  reason: string;
}

const RESEARCH_KEYWORDS = [
  // Academic/Research terms
  'research', 'paper', 'study', 'findings', 'methodology', 'analysis',
  'survey', 'review', 'literature', 'arxiv', 'scholarly', 'academic',
  'investigation', 'experiment', 'hypothesis', 'thesis', 'dissertation',
  'journal', 'publication', 'peer review', 'citation',
  
  // Scientific queries
  'discovery', 'advances', 'innovations', 'breakthroughs', 'developments',
  'trends', 'state of the art', 'emerging', 'latest', 'recent',
  'cutting edge', 'frontier', 'new techniques', 'novel approach',
  
  // Question patterns
  'what is the latest', 'what are the recent', 'what is happening in',
  'how has changed', 'whats new in', 'recent advances', 'current trends',
  'what are the key', 'what do papers say', 'what have researchers',
  'what is being studied', 'what technologies are',
  
  // Domain-specific terms
  'machine learning', 'deep learning', 'neural', 'algorithm', 'data science',
  'artificial intelligence', 'quantum', 'physics', 'biology', 'chemistry',
  'medicine', 'healthcare', 'genetics', 'climate', 'astronomy'
];

const CHAT_KEYWORDS = [
  'hello', 'hi', 'how are you', 'thanks', 'thank you', 'please', 'help',
  'tell me', 'explain', 'what is', 'how do', 'why', 'can you',
  'would you', 'could you', 'should i', 'what should', 'advice',
  'opinion', 'think about', 'do you think', 'your thoughts'
];

export function detectQueryType(query: string): QueryType {
  const lowerQuery = query.toLowerCase();
  const words = lowerQuery.split(/\s+/);
  
  // Count keyword matches
  const researchMatches = words.filter(word => 
    RESEARCH_KEYWORDS.some(kw => kw.includes(word) || word.includes(kw))
  ).length;
  
  const chatMatches = words.filter(word =>
    CHAT_KEYWORDS.some(kw => kw.includes(word) || word.includes(kw))
  ).length;
  
  // Heuristics for research vs chat
  const isResearch = 
    researchMatches > chatMatches ||
    lowerQuery.includes('arxiv') ||
    lowerQuery.includes('paper') ||
    lowerQuery.includes('research') ||
    lowerQuery.includes('study') ||
    lowerQuery.includes('trends') ||
    lowerQuery.includes('advances') ||
    lowerQuery.includes('innovations') ||
    (lowerQuery.startsWith('what') && (
      lowerQuery.includes('latest') ||
      lowerQuery.includes('recent') ||
      lowerQuery.includes('emerging') ||
      lowerQuery.includes('trends')
    ));
  
  const confidence = Math.min(1.0, Math.abs(researchMatches - chatMatches) / 10);
  
  return {
    type: isResearch ? 'research' : 'chat',
    confidence,
    reason: isResearch 
      ? `Detected research query (${researchMatches} research keywords)`
      : `Detected general chat (${chatMatches} chat keywords)`
  };
}
