import React from 'react';
import { ExternalLink, Clock, Globe, Calendar } from 'lucide-react';

const SearchResults = ({ results, totalCount, query, executionTime, loading }) => {
  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="text-center">
          <div className="loading-spinner mx-auto mb-4"></div>
          <p className="text-gray-600">Searching...</p>
        </div>
      </div>
    );
  }

  if (!query) {
    return (
      <div className="text-center py-12">
        <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <Globe className="w-8 h-8 text-gray-400" />
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          Start Your Search
        </h3>
        <p className="text-gray-600">
          Enter a search term to find websites and content across the web.
        </p>
      </div>
    );
  }

  if (results.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <Globe className="w-8 h-8 text-gray-400" />
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          No Results Found
        </h3>
        <p className="text-gray-600">
          No results found for "{query}". Try different keywords or check your spelling.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Search Info */}
      <div className="bg-gray-50 rounded-lg p-4 mb-6">
        <div className="flex justify-between items-center">
          <div>
            <p className="text-sm text-gray-600">
              Found <span className="font-semibold text-gray-900">{totalCount.toLocaleString()}</span> results
              {executionTime && (
                <span className="ml-2">
                  in <span className="font-semibold">{executionTime.toFixed(2)}s</span>
                </span>
              )}
            </p>
          </div>
          <div className="text-sm text-gray-500">
            Search: "{query}"
          </div>
        </div>
      </div>

      {/* Results */}
      <div className="space-y-4">
        {results.map((result, index) => (
          <SearchResultCard key={index} result={result} />
        ))}
      </div>
    </div>
  );
};

const SearchResultCard = ({ result }) => {
  const formatDate = (dateString) => {
    if (!dateString) return null;
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const formatResponseTime = (time) => {
    if (!time) return null;
    return `${(time * 1000).toFixed(0)}ms`;
  };

  return (
    <div className="result-card">
      <div className="flex justify-between items-start mb-2">
        <h3 className="result-title">
          <a
            href={result.page_url || (result.domain ? `https://${result.domain}` : `http://${result.ip_address}`)}
            target="_blank"
            rel="noopener noreferrer"
            className="hover:underline"
          >
            {result.title || 'Untitled Page'}
          </a>
        </h3>
        <ExternalLink className="w-4 h-4 text-gray-400 flex-shrink-0 ml-2" />
      </div>
      
      <div className="result-url">
        <span className="font-mono text-sm">
          {result.page_url || (result.domain ? `https://${result.domain}` : result.ip_address)}
        </span>
        {result.resolved_domain && result.domain && (
          <span className="ml-2 text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
            DNS: {result.domain}
          </span>
        )}
        {result.page_url && (
          <span className="ml-2 text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
            Full URL
          </span>
        )}
      </div>
      
      {/* Host and Page information */}
      <div className="text-xs text-gray-500 mb-2">
        {result.domain && (
          <span className="mr-3">
            <strong>Host:</strong> {result.domain} ({result.ip_address})
          </span>
        )}
        {!result.domain && (
          <span className="mr-3">
            <strong>Host:</strong> {result.ip_address}
          </span>
        )}
        {result.page_url && result.page_url !== (result.domain ? `https://${result.domain}` : `http://${result.ip_address}`) && (
          <span>
            <strong>Page:</strong> {result.page_url}
          </span>
        )}
      </div>
      
      {/* Page-specific information */}
      {result.page_title && result.page_title !== result.title && (
        <div className="text-sm text-gray-600 mb-2">
          <strong>Page Title:</strong> {result.page_title}
        </div>
      )}
      
      {result.page_description && result.page_description !== result.description && (
        <p className="result-description text-sm text-gray-600 mb-2">
          {result.page_description}
        </p>
      )}
      
      {result.description && (
        <p className="result-description">
          {result.description}
        </p>
      )}
      
      <div className="result-meta">
        {result.response_time && (
          <div className="flex items-center space-x-1">
            <Clock className="w-3 h-3" />
            <span>{formatResponseTime(result.response_time)}</span>
          </div>
        )}
        
        {result.last_crawled && (
          <div className="flex items-center space-x-1">
            <Calendar className="w-3 h-3" />
            <span>Crawled {formatDate(result.last_crawled)}</span>
          </div>
        )}
        
        {result.page_status && (
          <div className="flex items-center space-x-1">
            <span className={`text-xs px-2 py-1 rounded ${
              result.page_status >= 200 && result.page_status < 300 
                ? 'bg-green-100 text-green-800' 
                : result.page_status >= 300 && result.page_status < 400
                ? 'bg-yellow-100 text-yellow-800'
                : 'bg-red-100 text-red-800'
            }`}>
              Status: {result.page_status}
            </span>
          </div>
        )}
        
        {result.page_load_time && (
          <div className="flex items-center space-x-1">
            <span className="text-xs bg-gray-100 text-gray-800 px-2 py-1 rounded">
              Page Load: {formatResponseTime(result.page_load_time)}
            </span>
          </div>
        )}
        
        <div className="flex items-center space-x-1">
          <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
            Score: {result.score.toFixed(2)}
          </span>
        </div>
      </div>
    </div>
  );
};

export default SearchResults;
