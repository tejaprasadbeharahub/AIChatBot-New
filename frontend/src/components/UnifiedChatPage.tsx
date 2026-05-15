import { useState, useRef, useEffect } from 'react';
import { UnifiedChatInput } from './UnifiedChatInput';
import { ResearchDigestViewEnhanced } from './ResearchDigestViewEnhanced';
import { ResearchDigestStream } from './ResearchDigestStream';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  type: 'chat' | 'research';
  timestamp: Date;
}

interface ResearchDigest {
  summary: string;
  key_findings: Array<{ topic: string; finding: string; evidence_papers: string[] }>;
  methodologies: Array<{ name: string; frequency: number; papers: string[] }>;
  limitations: string[];
  trends: Array<{ trend: string; direction: 'increasing' | 'decreasing' | 'stable'; recent_papers: string[] }>;
  total_papers_reviewed: number;
  papers_cited: Array<any>;
  search_duration_seconds: number;
}

interface ResearchMessage extends Message {
  digest?: ResearchDigest;
}

export function UnifiedChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [streamingEvents, setStreamingEvents] = useState<any[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingEvents]);

  const handleResearchQuery = async (query: string, depth: string, maxPapers: number) => {
    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: query,
      type: 'research',
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setStreamingEvents([]);

    try {
      const response = await fetch('http://localhost:8000/api/research-agent/research-stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token') || ''}`,
        },
        body: JSON.stringify({
          query,
          depth,
          max_papers: maxPapers,
        }),
      });

      if (!response.body) throw new Error('No response body');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let digest: ResearchDigest | null = null;

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const text = decoder.decode(value);
        const lines = text.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const eventData = JSON.parse(line.slice(6));
              setStreamingEvents(prev => [...prev, eventData]);

              // Extract digest from completed event
              if (eventData.event === 'completed' && eventData.data.digest) {
                digest = eventData.data.digest;
              }
            } catch (e) {
              // Ignore parse errors
            }
          }
        }
      }

      // Add assistant message with digest
      if (digest) {
        const assistantMessage: ResearchMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: 'Research completed',
          type: 'research',
          timestamp: new Date(),
          digest,
        };
        setMessages(prev => [...prev, assistantMessage]);
      }
    } catch (error) {
      console.error('Research failed:', error);
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Error: ${error instanceof Error ? error.message : 'Research failed'}`,
        type: 'research',
        timestamp: new Date(),
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleChatQuery = async (message: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: message,
      type: 'chat',
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token') || ''}`,
        },
        body: JSON.stringify({
          message,
          chat_id: localStorage.getItem('chat_id'),
        }),
      });

      const data = await response.json();

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.response || 'No response',
        type: 'chat',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Chat failed:', error);
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Error: ${error instanceof Error ? error.message : 'Chat failed'}`,
        type: 'chat',
        timestamp: new Date(),
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-4 shadow-sm">
        <h1 className="text-2xl font-bold text-gray-900">
          🤖 AI Research & Chat Assistant
        </h1>
        <p className="text-sm text-gray-600 mt-1">
          Ask research questions or chat naturally - I'll handle both!
        </p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="text-6xl mb-4">🤖</div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Welcome!</h2>
              <p className="text-gray-600 max-w-md">
                You can ask research questions to analyze papers from arXiv, or have a general conversation.
                The system will automatically detect what you need!
              </p>
            </div>
          </div>
        ) : (
          <>
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {msg.role === 'assistant' && (
                  <div className="w-full">
                    {msg.type === 'research' ? (
                      <div className="bg-white rounded-lg shadow-md p-6">
                        {(msg as ResearchMessage).digest ? (
                          <ResearchDigestViewEnhanced
                            digest={(msg as ResearchMessage).digest!}
                            query={messages.find(m => m.id < msg.id && m.role === 'user')?.content || 'Research'}
                            isLoading={false}
                          />
                        ) : (
                          <p className="text-gray-700">{msg.content}</p>
                        )}
                      </div>
                    ) : (
                      <div className="max-w-2xl bg-white rounded-lg shadow-md p-4 text-gray-800">
                        <p className="whitespace-pre-wrap">{msg.content}</p>
                      </div>
                    )}
                  </div>
                )}

                {msg.role === 'user' && (
                  <div className="max-w-2xl">
                    <div className={`rounded-lg shadow-md p-4 ${
                      msg.type === 'research'
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-600 text-white'
                    }`}>
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                      <span className="text-xs opacity-75 mt-2 block">
                        {msg.type === 'research' ? '🔬 Research' : '💬 Chat'}
                      </span>
                    </div>
                  </div>
                )}
              </div>
            ))}

            {/* Streaming events */}
            {isLoading && streamingEvents.length > 0 && (
              <div className="bg-white rounded-lg shadow-md p-6">
                <ResearchDigestStream
                  isActive={isLoading}
                />
              </div>
            )}

            {isLoading && streamingEvents.length === 0 && (
              <div className="flex justify-center">
                <div className="text-center">
                  <div className="inline-block animate-spin text-2xl mb-2">⚙️</div>
                  <p className="text-gray-600">Processing your query...</p>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input */}
      <div className="bg-white border-t border-gray-200 p-6 shadow-lg">
        <UnifiedChatInput
          onResearchQuery={handleResearchQuery}
          onChatQuery={handleChatQuery}
          isLoading={isLoading}
        />
      </div>
    </div>
  );
}
