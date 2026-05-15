interface ResearchPaperCardProps {
  arxivId: string;
  title: string;
  authors: string[];
  abstract: string;
  publishedDate: string;
  categories: string[];
  pdfUrl: string;
  relevanceScore: number;
}

export function ResearchPaperCard({
  arxivId,
  title,
  authors,
  abstract,
  publishedDate,
  categories,
  pdfUrl,
  relevanceScore,
}: ResearchPaperCardProps) {
  const getRelevanceColor = (score: number): string => {
    if (score >= 0.8) return 'bg-green-100 text-green-800';
    if (score >= 0.6) return 'bg-blue-100 text-blue-800';
    if (score >= 0.4) return 'bg-yellow-100 text-yellow-800';
    return 'bg-gray-100 text-gray-800';
  };

  const getRelevanceLabel = (score: number): string => {
    if (score >= 0.8) return 'Highly Relevant';
    if (score >= 0.6) return 'Relevant';
    if (score >= 0.4) return 'Somewhat Relevant';
    return 'Low Relevance';
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-5 hover:shadow-lg transition">
      {/* Header with relevance badge */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 line-clamp-2 hover:text-blue-600">
            <a href={pdfUrl} target="_blank" rel="noopener noreferrer">
              {title}
            </a>
          </h3>
          <p className="text-xs text-gray-500 mt-1">arXiv:{arxivId}</p>
        </div>
        <div className={`px-3 py-1 rounded text-xs font-medium whitespace-nowrap ml-3 ${getRelevanceColor(relevanceScore)}`}>
          {getRelevanceLabel(relevanceScore)}
          <br />
          {(relevanceScore * 100).toFixed(0)}%
        </div>
      </div>

      {/* Authors */}
      <div className="mb-3">
        <p className="text-sm text-gray-600">
          <span className="font-medium">Authors:</span> {authors.slice(0, 3).join(', ')}
          {authors.length > 3 && ` +${authors.length - 3}`}
        </p>
      </div>

      {/* Published date */}
      <div className="mb-3">
        <p className="text-xs text-gray-500">
          📅 Published: {new Date(publishedDate).toLocaleDateString()}
        </p>
      </div>

      {/* Categories */}
      <div className="mb-3 flex flex-wrap gap-1">
        {categories.map((cat) => (
          <span
            key={cat}
            className="inline-block px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded"
          >
            {cat}
          </span>
        ))}
      </div>

      {/* Abstract */}
      <div className="mb-4">
        <p className="text-sm text-gray-700 line-clamp-3">
          {abstract.substring(0, 200)}...
        </p>
      </div>

      {/* Action buttons */}
      <div className="flex gap-2">
        <a
          href={pdfUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="flex-1 px-3 py-2 bg-blue-100 text-blue-700 text-sm font-medium rounded hover:bg-blue-200 transition text-center"
        >
          📖 Read PDF
        </a>
        <a
          href={`https://arxiv.org/abs/${arxivId}`}
          target="_blank"
          rel="noopener noreferrer"
          className="flex-1 px-3 py-2 bg-gray-100 text-gray-700 text-sm font-medium rounded hover:bg-gray-200 transition text-center"
        >
          View on arXiv
        </a>
      </div>
    </div>
  );
}
