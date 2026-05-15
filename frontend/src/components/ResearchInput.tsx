import { useState } from 'react';

interface ResearchInputProps {
  onSearch: (query: string, depth: string, maxPapers: number) => void;
  isLoading?: boolean;
}

export function ResearchInput({ onSearch, isLoading }: ResearchInputProps) {
  const [query, setQuery] = useState('');
  const [depth, setDepth] = useState<'quick' | 'balanced' | 'deep'>('balanced');
  const [maxPapers, setMaxPapers] = useState(20);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query, depth, maxPapers);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white p-6 rounded-lg shadow-md">
      <div className="mb-4">
        <label htmlFor="query" className="block text-sm font-medium text-gray-700 mb-2">
          Research Query
        </label>
        <textarea
          id="query"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Enter your research question (e.g., 'machine learning applications in healthcare')"
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          rows={3}
          disabled={isLoading}
        />
        <p className="mt-1 text-xs text-gray-500">
          {query.length}/2000 characters • Must be between 5-2000 characters
        </p>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <label htmlFor="depth" className="block text-sm font-medium text-gray-700 mb-2">
            Search Depth
          </label>
          <select
            id="depth"
            value={depth}
            onChange={(e) => setDepth(e.target.value as 'quick' | 'balanced' | 'deep')}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            disabled={isLoading}
          >
            <option value="quick">Quick (10 papers)</option>
            <option value="balanced">Balanced (20 papers)</option>
            <option value="deep">Deep (50 papers)</option>
          </select>
          <p className="mt-1 text-xs text-gray-500">
            More papers = longer search time
          </p>
        </div>

        <div>
          <label htmlFor="maxPapers" className="block text-sm font-medium text-gray-700 mb-2">
            Max Papers: {maxPapers}
          </label>
          <input
            id="maxPapers"
            type="range"
            min="1"
            max="50"
            value={maxPapers}
            onChange={(e) => setMaxPapers(parseInt(e.target.value))}
            className="w-full"
            disabled={isLoading}
          />
        </div>
      </div>

      <button
        type="submit"
        disabled={isLoading || !query.trim()}
        className="w-full px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:bg-gray-400 transition"
      >
        {isLoading ? 'Researching...' : '🔍 Start Research'}
      </button>
    </form>
  );
}
