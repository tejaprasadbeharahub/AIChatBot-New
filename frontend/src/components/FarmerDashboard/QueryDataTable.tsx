import React from 'react';
import type { FarmQuery } from '../../api/farm';
import { ExpandableQueryRow } from './ExpandableQueryRow';

interface QueryDataTableProps {
  queries: FarmQuery[];
  expandedRows: Set<string>;
  onToggleRow: (id: string) => void;
  isLoading: boolean;
}

export const QueryDataTable: React.FC<QueryDataTableProps> = ({
  queries,
  expandedRows,
  onToggleRow,
  isLoading,
}) => {
  if (isLoading && queries.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6 text-center">
        <p className="text-gray-500">⏳ Loading queries...</p>
      </div>
    );
  }

  if (queries.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-8 text-center border border-gray-200">
        <p className="text-gray-500 text-lg">📭 No queries submitted yet</p>
        <p className="text-gray-400 text-sm mt-2">Submit a query above to get AI analysis</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden border border-gray-200">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-100 border-b border-gray-300">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">ID</th>
              <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Query</th>
              <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Crop</th>
              <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Risk Level</th>
              <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Market Action</th>
              <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Confidence</th>
              <th className="px-4 py-3 text-left text-sm font-semibold text-gray-700">Date</th>
              <th className="px-4 py-3 text-center text-sm font-semibold text-gray-700">Details</th>
            </tr>
          </thead>
          <tbody>
            {queries.map((query) => (
              <ExpandableQueryRow
                key={query.id}
                query={query}
                isExpanded={expandedRows.has(query.id)}
                onToggle={onToggleRow}
              />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
