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

export function ResearchDigestView({ digest, query, isLoading }: ResearchDigestViewProps) {
  if (isLoading) {
    return (
      <div className="bg-gray-50 rounded-lg p-8 text-center">
        <div className="inline-block animate-spin">⚙️</div>
        <p className="mt-4 text-gray-600">Generating research digest...</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6 border border-blue-200">
        <h2 className="text-3xl font-bold text-gray-900">Research Digest</h2>
        <p className="text-lg text-gray-600 mt-2">📚 {query}</p>
        <div className="mt-4 flex gap-6 text-sm">
          <div>
            <span className="font-medium text-gray-700">Papers Analyzed:</span>
            <span className="ml-2 text-blue-600 font-semibold">{digest.total_papers_reviewed}</span>
          </div>
          <div>
            <span className="font-medium text-gray-700">Search Duration:</span>
            <span className="ml-2 text-blue-600 font-semibold">{digest.search_duration_seconds}s</span>
          </div>
        </div>
      </div>

      {/* Executive Summary */}
      <section className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-2xl font-bold text-gray-900 mb-4">📋 Executive Summary</h3>
        <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">{digest.summary}</p>
      </section>

      {/* Key Findings */}
      {digest.key_findings.length > 0 && (
        <section className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-2xl font-bold text-gray-900 mb-4">🔑 Key Findings</h3>
          <div className="space-y-4">
            {digest.key_findings.map((finding, idx) => (
              <div key={idx} className="border-l-4 border-blue-500 pl-4">
                <h4 className="font-semibold text-gray-900">{finding.topic}</h4>
                <p className="text-gray-700 mt-2">{finding.finding}</p>
                {finding.evidence_papers.length > 0 && (
                  <p className="text-xs text-gray-500 mt-2">
                    Evidence: {finding.evidence_papers.slice(0, 3).join(', ')}
                    {finding.evidence_papers.length > 3 && ` +${finding.evidence_papers.length - 3}`}
                  </p>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Methodologies */}
      {digest.methodologies.length > 0 && (
        <section className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-2xl font-bold text-gray-900 mb-4">🔬 Common Methodologies</h3>
          <div className="space-y-3">
            {digest.methodologies.map((method, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between p-3 bg-gray-50 rounded"
              >
                <div>
                  <p className="font-semibold text-gray-900">{method.name}</p>
                  <p className="text-xs text-gray-600">
                    Used in {method.frequency} paper{method.frequency !== 1 ? 's' : ''}
                  </p>
                </div>
                <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-500"
                    style={{
                      width: `${Math.min((method.frequency / 10) * 100, 100)}%`,
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Research Trends */}
      {digest.trends.length > 0 && (
        <section className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-2xl font-bold text-gray-900 mb-4">📈 Research Trends</h3>
          <div className="space-y-3">
            {digest.trends.map((trend, idx) => (
              <div key={idx} className="p-3 bg-gradient-to-r from-purple-50 to-pink-50 rounded">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-semibold text-gray-900">{trend.trend}</p>
                    <p className="text-xs text-gray-600 mt-1">
                      {trend.direction === 'increasing' && '📈 Increasing'}
                      {trend.direction === 'decreasing' && '📉 Decreasing'}
                      {trend.direction === 'stable' && '➡️ Stable'}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Limitations */}
      {digest.limitations.length > 0 && (
        <section className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-2xl font-bold text-gray-900 mb-4">⚠️ Limitations</h3>
          <ul className="space-y-2">
            {digest.limitations.map((limitation, idx) => (
              <li key={idx} className="flex gap-3">
                <span className="text-yellow-500">•</span>
                <span className="text-gray-700">{limitation}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* Papers Cited */}
      <section className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-2xl font-bold text-gray-900 mb-4">
          📚 Papers Cited ({digest.papers_cited.length})
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {digest.papers_cited.map((paper) => (
            <ResearchPaperCard
              key={paper.arxiv_id}
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
      </section>

      {/* Export Options */}
      <section className="bg-blue-50 rounded-lg border border-blue-200 p-6">
        <h3 className="text-lg font-bold text-blue-900 mb-4">💾 Export Options</h3>
        <div className="flex gap-3 flex-wrap">
          <button
            onClick={() => {
              const text = JSON.stringify(digest, null, 2);
              const blob = new Blob([text], { type: 'application/json' });
              const url = URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = url;
              a.download = `research-digest-${Date.now()}.json`;
              a.click();
            }}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
          >
            📥 JSON
          </button>
          <button
            onClick={() => window.print()}
            className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 transition"
          >
            🖨️ Print
          </button>
        </div>
      </section>
    </div>
  );
}
