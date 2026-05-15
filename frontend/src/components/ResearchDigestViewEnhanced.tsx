import { useState } from 'react';
import { ResearchPaperCard } from './ResearchPaperCard';

interface ResearchPaperRef {
  arxiv_id: string;
  title: string;
  authors: string[];
  abstract: string;
  published_date: string;
  categories: string[];
  pdf_url: string;
  relevance_score: number;
}

interface ResearchDigestFinding {
  topic: string;
  finding: string;
  evidence_papers: string[];
}

interface ResearchDigestTrend {
  trend: string;
  direction: 'increasing' | 'decreasing' | 'stable';
  recent_papers: string[];
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

interface ResearchDigestViewProps {
  digest: ResearchDigestFull;
  query: string;
  isLoading?: boolean;
}

export function ResearchDigestViewEnhanced({ digest, query, isLoading }: ResearchDigestViewProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'findings' | 'papers' | 'trends'>('overview');

  if (isLoading) {
    return (
      <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-12 text-center">
        <div className="inline-block animate-spin text-4xl">⚙️</div>
        <p className="mt-4 text-lg text-gray-600 font-medium">Generating research digest...</p>
        <p className="mt-2 text-sm text-gray-500">This may take 20-30 seconds</p>
      </div>
    );
  }

  const getTrendIcon = (direction: string) => {
    switch (direction) {
      case 'increasing': return '📈';
      case 'decreasing': return '📉';
      default: return '➡️';
    }
  };

  const getRelevanceStats = () => {
    const scores = digest.papers_cited.map(p => p.relevance_score);
    return {
      avg: (scores.reduce((a, b) => a + b) / scores.length * 100).toFixed(0),
      max: (Math.max(...scores) * 100).toFixed(0),
      min: (Math.min(...scores) * 100).toFixed(0),
    };
  };

  const stats = getRelevanceStats();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl p-6 text-white">
        <h2 className="text-2xl font-bold mb-2">Research Digest</h2>
        <p className="text-blue-100">{query}</p>
        <div className="mt-4 flex gap-6 text-sm">
          <div>
            <span className="opacity-75">Papers Reviewed</span>
            <p className="text-xl font-bold">{digest.total_papers_reviewed}</p>
          </div>
          <div>
            <span className="opacity-75">Avg Relevance</span>
            <p className="text-xl font-bold">{stats.avg}%</p>
          </div>
          <div>
            <span className="opacity-75">Duration</span>
            <p className="text-xl font-bold">{digest.search_duration_seconds}s</p>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-2 border-b border-gray-200">
        {(['overview', 'findings', 'papers', 'trends'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-3 font-medium border-b-2 transition ${
              activeTab === tab
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-600 hover:text-gray-900'
            }`}
          >
            {tab === 'overview' && '📋 Overview'}
            {tab === 'findings' && '🔍 Key Findings'}
            {tab === 'papers' && '📚 Papers'}
            {tab === 'trends' && '📊 Trends'}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div>
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Summary */}
            <div className="bg-white rounded-lg p-6 border border-gray-200">
              <h3 className="text-lg font-semibold mb-3">Executive Summary</h3>
              <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">
                {digest.summary}
              </p>
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4 border border-green-200">
                <p className="text-sm text-green-900 font-medium">Total Papers</p>
                <p className="text-3xl font-bold text-green-600 mt-2">
                  {digest.total_papers_reviewed}
                </p>
              </div>
              <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4 border border-blue-200">
                <p className="text-sm text-blue-900 font-medium">Key Findings</p>
                <p className="text-3xl font-bold text-blue-600 mt-2">
                  {digest.key_findings.length}
                </p>
              </div>
              <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4 border border-purple-200">
                <p className="text-sm text-purple-900 font-medium">Research Areas</p>
                <p className="text-3xl font-bold text-purple-600 mt-2">
                  {digest.methodologies.length}
                </p>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'findings' && (
          <div className="space-y-4">
            {digest.key_findings.length === 0 ? (
              <p className="text-gray-500 italic">No key findings extracted</p>
            ) : (
              digest.key_findings.map((finding, idx) => (
                <div
                  key={idx}
                  className="bg-white rounded-lg p-5 border border-gray-200 hover:shadow-md transition"
                >
                  <div className="flex items-start gap-3">
                    <span className="text-2xl">🔍</span>
                    <div className="flex-1">
                      <h4 className="font-semibold text-gray-900 mb-1">
                        {finding.topic}
                      </h4>
                      <p className="text-gray-700 mb-3">{finding.finding}</p>
                      <div className="flex gap-2 flex-wrap">
                        {finding.evidence_papers.slice(0, 3).map((paperId) => (
                          <span
                            key={paperId}
                            className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded"
                          >
                            {paperId}
                          </span>
                        ))}
                        {finding.evidence_papers.length > 3 && (
                          <span className="px-2 py-1 text-xs bg-gray-100 text-gray-800 rounded">
                            +{finding.evidence_papers.length - 3} more
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === 'papers' && (
          <div className="space-y-4">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-sm text-blue-900">
                📄 Showing {digest.papers_cited.length} papers sorted by relevance
              </p>
            </div>
            {digest.papers_cited.map((paper, idx) => (
              <ResearchPaperCard
                key={idx}
                arxivId={paper.arxiv_id}
                title={paper.title}
                authors={paper.authors}
                abstract={paper.abstract}
                publishedDate={paper.published_date}
                categories={paper.categories}
                pdfUrl={paper.pdf_url}
                relevanceScore={paper.relevance_score}
              />
            ))}
          </div>
        )}

        {activeTab === 'trends' && (
          <div className="space-y-4">
            {digest.trends.length === 0 ? (
              <p className="text-gray-500 italic">No trends identified</p>
            ) : (
              digest.trends.map((trend, idx) => (
                <div
                  key={idx}
                  className="bg-white rounded-lg p-5 border border-gray-200 hover:shadow-md transition"
                >
                  <div className="flex items-start gap-3">
                    <span className="text-2xl">{getTrendIcon(trend.direction)}</span>
                    <div className="flex-1">
                      <h4 className="font-semibold text-gray-900 mb-1">
                        {trend.trend}
                      </h4>
                      <div className="inline-block px-3 py-1 rounded-full text-xs font-medium mt-2"
                        style={{
                          backgroundColor: trend.direction === 'increasing' ? '#dbeafe' : '#fecaca',
                          color: trend.direction === 'increasing' ? '#1e40af' : '#991b1b',
                        }}
                      >
                        {trend.direction === 'increasing' ? '📈 Increasing' : trend.direction === 'decreasing' ? '📉 Decreasing' : '➡️ Stable'}
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>

      {/* Limitations */}
      {digest.limitations.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-5">
          <h3 className="font-semibold text-amber-900 mb-3">⚠️ Research Limitations</h3>
          <ul className="space-y-2">
            {digest.limitations.map((limitation, idx) => (
              <li key={idx} className="text-sm text-amber-800 flex items-start gap-2">
                <span>•</span>
                <span>{limitation}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Export Options */}
      <div className="flex gap-2 justify-center pt-4">
        <button
          onClick={() => {
            const json = JSON.stringify(digest, null, 2);
            const blob = new Blob([json], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `research-digest-${Date.now()}.json`;
            a.click();
          }}
          className="px-4 py-2 bg-blue-100 text-blue-700 font-medium rounded-lg hover:bg-blue-200 transition"
        >
          📥 Export as JSON
        </button>
        <button
          onClick={() => window.print()}
          className="px-4 py-2 bg-gray-100 text-gray-700 font-medium rounded-lg hover:bg-gray-200 transition"
        >
          🖨️ Print
        </button>
      </div>
    </div>
  );
}
