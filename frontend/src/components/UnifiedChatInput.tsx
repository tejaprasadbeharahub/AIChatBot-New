import { useState } from 'react';
import { detectQueryType } from '../lib/queryDetector';

interface UnifiedChatInputProps {
  onResearchQuery: (query: string, depth: string, maxPapers: number) => void;
  onChatQuery: (message: string) => void;
  isLoading?: boolean;
}

export function UnifiedChatInput({ 
  onResearchQuery, 
  onChatQuery, 
  isLoading 
}: UnifiedChatInputProps) {
  const [input, setInput] = useState('');
  const [queryType, setQueryType] = useState<'research' | 'chat'>('chat');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [depth, setDepth] = useState<'quick' | 'balanced' | 'deep'>('balanced');
  const [maxPapers, setMaxPapers] = useState(20);

  const handleInputChange = (text: string) => {
    setInput(text);
    if (text.trim()) {
      const detected = detectQueryType(text);
      setQueryType(detected.type);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    if (queryType === 'research') {
      onResearchQuery(input, depth, maxPapers);
    } else {
      onChatQuery(input);
    }
    setInput('');
  };

  const toggleQueryType = () => {
    setQueryType(queryType === 'research' ? 'chat' : 'research');
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      {/* Main input */}
      <div className="relative">
        <div className="flex gap-2">
          <div className="flex-1 relative">
            <textarea
              value={input}
              onChange={(e) => handleInputChange(e.target.value)}
              placeholder={
                queryType === 'research'
                  ? 'Ask a research question... (e.g., "latest advances in quantum computing")'
                  : 'Ask anything... (e.g., "hello, how are you?")'
              }
              className={`w-full px-4 py-3 border-2 rounded-lg focus:outline-none transition ${
                queryType === 'research'
                  ? 'border-blue-300 focus:border-blue-500 bg-blue-50 focus:bg-white'
                  : 'border-gray-300 focus:border-gray-500 bg-white'
              }`}
              rows={3}
              disabled={isLoading}
            />
            
            {/* Query type badge */}
            <div className="absolute top-3 right-3 flex items-center gap-2">
              <span
                className={`px-2 py-1 text-xs font-medium rounded ${
                  queryType === 'research'
                    ? 'bg-blue-200 text-blue-800'
                    : 'bg-gray-200 text-gray-800'
                }`}
              >
                {queryType === 'research' ? '🔬 Research' : '💬 Chat'}
              </span>
            </div>
          </div>
        </div>

        {/* Character counter */}
        <div className="mt-2 text-xs text-gray-500">
          {input.length}/2000 characters
        </div>
      </div>

      {/* Advanced options for research */}
      {queryType === 'research' && !showAdvanced && (
        <button
          type="button"
          onClick={() => setShowAdvanced(true)}
          className="text-sm text-blue-600 hover:text-blue-800 font-medium"
        >
          ⚙️ Advanced Options
        </button>
      )}

      {queryType === 'research' && showAdvanced && (
        <div className="bg-blue-50 p-4 rounded-lg border border-blue-200 space-y-3">
          <div>
            <label htmlFor="depth" className="block text-sm font-medium text-gray-700 mb-2">
              Search Depth
            </label>
            <div className="flex gap-3">
              {(['quick', 'balanced', 'deep'] as const).map((d) => (
                <label key={d} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    value={d}
                    checked={depth === d}
                    onChange={(e) => setDepth(e.target.value as typeof d)}
                    className="w-4 h-4"
                  />
                  <span className="text-sm capitalize">
                    {d} ({d === 'quick' ? '10' : d === 'balanced' ? '20' : '50'} papers)
                  </span>
                </label>
              ))}
            </div>
            <p className="mt-2 text-xs text-gray-600">
              • Quick: Fast search, fewer papers
              <br />• Balanced: Good mix of speed & coverage (recommended)
              <br />• Deep: Comprehensive but slower (may timeout)
            </p>
          </div>

          <div>
            <label htmlFor="maxPapers" className="block text-sm font-medium text-gray-700 mb-2">
              Max Papers: {maxPapers}
            </label>
            <input
              id="maxPapers"
              type="range"
              min="5"
              max="50"
              step="5"
              value={maxPapers}
              onChange={(e) => setMaxPapers(parseInt(e.target.value))}
              className="w-full"
            />
            <p className="mt-1 text-xs text-gray-600">
              Collect between 5-50 papers. More papers = longer processing.
            </p>
          </div>

          <button
            type="button"
            onClick={() => setShowAdvanced(false)}
            className="text-sm text-blue-600 hover:text-blue-800 font-medium"
          >
            ✕ Hide Advanced Options
          </button>
        </div>
      )}

      {/* Action buttons */}
      <div className="flex gap-2">
        <button
          type="submit"
          disabled={isLoading || !input.trim()}
          className={`flex-1 px-4 py-3 font-medium rounded-lg transition ${
            queryType === 'research'
              ? 'bg-blue-600 text-white hover:bg-blue-700 disabled:bg-blue-400'
              : 'bg-gray-600 text-white hover:bg-gray-700 disabled:bg-gray-400'
          }`}
        >
          {isLoading ? (
            <>⏳ Processing...</>
          ) : queryType === 'research' ? (
            <>🔬 Research</>
          ) : (
            <>💬 Chat</>
          )}
        </button>

        <button
          type="button"
          onClick={toggleQueryType}
          disabled={isLoading}
          className="px-4 py-3 bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium rounded-lg transition disabled:opacity-50"
          title="Toggle between research and chat"
        >
          ↔️
        </button>
      </div>

      {/* Tips */}
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
        <p className="text-xs text-amber-900 font-medium mb-1">💡 Tips:</p>
        <ul className="text-xs text-amber-800 space-y-1">
          {queryType === 'research' ? (
            <>
              <li>• Use keywords like "advances", "trends", "latest", "research"</li>
              <li>• Ask about specific topics: "quantum computing", "climate change"</li>
              <li>• Be specific for better results</li>
            </>
          ) : (
            <>
              <li>• Ask general questions and have a conversation</li>
              <li>• Type naturally, as if chatting with a friend</li>
              <li>• The system will detect research queries automatically</li>
            </>
          )}
        </ul>
      </div>
    </form>
  );
}
