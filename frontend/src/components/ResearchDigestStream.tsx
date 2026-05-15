import { useEffect, useState } from 'react';

interface StreamEvent {
  event: string;
  data: {
    papers_count?: number;
    avg_relevance?: number;
    status?: string;
    message?: string;
    error?: string;
    [key: string]: any;
  };
  timestamp?: number;
}

interface ResearchDigestStreamProps {
  isActive?: boolean;
}

export function ResearchDigestStream({ isActive = true }: ResearchDigestStreamProps) {
  const [events, setEvents] = useState<StreamEvent[]>([]);
  const [currentStatus, setCurrentStatus] = useState<string>('initializing');

  useEffect(() => {
    if (!isActive) return;

    const simulatedEvents = [
      { event: 'initialized', data: { message: 'Starting research workflow...' } },
      { event: 'searching', data: { papers_count: 0, message: 'Searching arXiv...' } },
      { event: 'papers_found', data: { papers_count: 15, message: 'Found 15 papers' } },
      { event: 'analyzing', data: { message: 'Analyzing relevance scores...' } },
      { event: 'papers_found', data: { papers_count: 25, avg_relevance: 0.72 } },
      { event: 'refining', data: { message: 'Refining search criteria...' } },
      { event: 'papers_found', data: { papers_count: 32, avg_relevance: 0.78 } },
      { event: 'generating_digest', data: { message: 'Generating research digest...' } },
      { event: 'completed', data: { message: 'Research complete!' } },
    ];

    let eventIndex = 0;
    const interval = setInterval(() => {
      if (eventIndex < simulatedEvents.length) {
        const event = {
          ...simulatedEvents[eventIndex],
          timestamp: Date.now(),
        };
        setEvents(prev => [...prev, event]);
        setCurrentStatus(event.event);
        eventIndex++;
      } else {
        clearInterval(interval);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [isActive]);

  const getEventIcon = (event: string) => {
    const icons: Record<string, string> = {
      initialized: '🚀',
      searching: '🔍',
      papers_found: '📄',
      analyzing: '📊',
      refining: '🔧',
      generating_digest: '✍️',
      completed: '✅',
      error: '❌',
    };
    return icons[event] || '⚙️';
  };

  const getEventLabel = (event: string) => {
    const labels: Record<string, string> = {
      initialized: 'Initialized',
      searching: 'Searching Papers',
      papers_found: 'Papers Found',
      analyzing: 'Analyzing',
      refining: 'Refining Search',
      generating_digest: 'Generating Digest',
      completed: 'Completed',
      error: 'Error',
    };
    return labels[event] || event;
  };

  const latestPapersEvent = events.find(e => e.event === 'papers_found');
  const currentPaperCount = latestPapersEvent?.data.papers_count || 0;
  const currentRelevance = latestPapersEvent?.data.avg_relevance || 0;

  return (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-lg p-5 text-white">
        <h3 className="text-lg font-semibold mb-4">🔬 Research in Progress</h3>
        
        <div className="grid grid-cols-3 gap-4 mb-4">
          <div>
            <p className="text-blue-100 text-sm">Papers Found</p>
            <p className="text-2xl font-bold">{currentPaperCount}</p>
          </div>
          <div>
            <p className="text-blue-100 text-sm">Avg Relevance</p>
            <p className="text-2xl font-bold">{(currentRelevance * 100).toFixed(0)}%</p>
          </div>
          <div>
            <p className="text-blue-100 text-sm">Status</p>
            <p className="text-lg font-semibold capitalize">{getEventLabel(currentStatus)}</p>
          </div>
        </div>

        <div className="w-full bg-blue-400 rounded-full h-2 overflow-hidden">
          <div
            className="bg-white h-full transition-all duration-500 ease-out"
            style={{
              width: `${Math.min(100, (events.length / 9) * 100)}%`,
            }}
          />
        </div>
      </div>

      <div className="space-y-3">
        <h4 className="font-semibold text-gray-900 text-sm">Event Timeline</h4>
        <div className="space-y-2">
          {events.map((event, idx) => (
            <div key={idx} className="flex gap-3">
              <div className="flex-shrink-0 text-2xl">
                {getEventIcon(event.event)}
              </div>
              <div className="flex-1 bg-gray-50 rounded-lg p-3">
                <div className="flex items-center justify-between">
                  <span className="font-medium text-gray-900">
                    {getEventLabel(event.event)}
                  </span>
                  <span className="text-xs text-gray-500">
                    {event.timestamp
                      ? new Date(event.timestamp).toLocaleTimeString()
                      : '-'}
                  </span>
                </div>
                
                {event.data.message && (
                  <p className="text-sm text-gray-700 mt-1">{event.data.message}</p>
                )}
                
                {event.data.papers_count !== undefined && (
                  <div className="mt-2 flex gap-4 text-xs">
                    <span className="text-gray-600">
                      📄 <strong>{event.data.papers_count}</strong> papers
                    </span>
                    {event.data.avg_relevance !== undefined && (
                      <span className="text-gray-600">
                        ⭐ <strong>{(event.data.avg_relevance * 100).toFixed(0)}%</strong> avg relevance
                      </span>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
        <p className="text-sm font-medium text-amber-900 mb-2">💡 What's happening?</p>
        <ul className="text-xs text-amber-800 space-y-1">
          <li>• 🔍 Searching: Looking for relevant papers on arXiv</li>
          <li>• 📊 Analyzing: Computing relevance scores</li>
          <li>• 🔧 Refining: Adjusting search terms if needed</li>
          <li>• ✍️ Generating: Creating the final research digest</li>
        </ul>
      </div>
    </div>
  );
}
