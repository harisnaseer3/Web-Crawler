import React, { useEffect } from 'react';
import { useSearch } from '../services/SearchContext';
import SearchBar from '../components/SearchBar';
import SearchResults from '../components/SearchResults';
import Pagination from '../components/Pagination';

const SearchPage = () => {
  const {
    searchResults,
    totalCount,
    query,
    loading,
    error,
    currentPage,
    resultsPerPage,
    search,
    setPage,
    setResultsPerPage,
  } = useSearch();

  const totalPages = Math.ceil(totalCount / resultsPerPage);

  const handleSearch = (searchQuery) => {
    if (searchQuery) {
      search(searchQuery, 1, resultsPerPage);
    }
  };

  const handlePageChange = (page) => {
    if (page >= 1 && page <= totalPages) {
      search(query, page, resultsPerPage);
    }
  };

  const handleResultsPerPageChange = (e) => {
    const newLimit = parseInt(e.target.value);
    setResultsPerPage(newLimit);
    if (query) {
      search(query, 1, newLimit);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Search Section */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Web Crawler Search Engine
          </h1>
          <p className="text-lg text-gray-600 mb-8">
            Search across millions of web pages with advanced crawling technology
          </p>
          
          <div className="max-w-2xl mx-auto">
            <SearchBar
              onSearch={handleSearch}
              loading={loading}
              placeholder="Search for websites, content, or domains..."
            />
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="error-message">
            <p>{error}</p>
          </div>
        )}

        {/* Results Section */}
        <div className="bg-white rounded-lg shadow-sm">
          <div className="p-6">
            {/* Results Controls */}
            {totalCount > 0 && (
              <div className="flex justify-between items-center mb-6">
                <div className="flex items-center space-x-4">
                  <label className="text-sm font-medium text-gray-700">
                    Results per page:
                  </label>
                  <select
                    value={resultsPerPage}
                    onChange={handleResultsPerPageChange}
                    className="border border-gray-300 rounded-md px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value={10}>10</option>
                    <option value={25}>25</option>
                    <option value={50}>50</option>
                    <option value={100}>100</option>
                  </select>
                </div>
              </div>
            )}

            {/* Search Results */}
            <SearchResults
              results={searchResults}
              totalCount={totalCount}
              query={query}
              executionTime={0} // This would come from the search context
              loading={loading}
            />

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="mt-8 pt-6 border-t border-gray-200">
                <Pagination
                  currentPage={currentPage}
                  totalPages={totalPages}
                  onPageChange={handlePageChange}
                  totalCount={totalCount}
                  resultsPerPage={resultsPerPage}
                />
              </div>
            )}
          </div>
        </div>

        {/* Popular Keywords Section */}
        {!query && (
          <div className="mt-12">
            <div className="text-center mb-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                Popular Search Terms
              </h2>
              <p className="text-gray-600">
                Discover what others are searching for
              </p>
            </div>
            <PopularKeywords />
          </div>
        )}
      </div>
    </div>
  );
};

// Popular Keywords Component
const PopularKeywords = () => {
  const [keywords, setKeywords] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const { search } = useSearch();

  useEffect(() => {
    const fetchKeywords = async () => {
      try {
        const response = await fetch('/api/search/keywords/popular?limit=12');
        const data = await response.json();
        setKeywords(data.keywords || []);
      } catch (error) {
        console.error('Error fetching keywords:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchKeywords();
  }, []);

  const handleKeywordClick = (keyword) => {
    search(keyword, 1, 10);
  };

  if (loading) {
    return (
      <div className="flex justify-center">
        <div className="loading-spinner"></div>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
      {keywords.map((item, index) => (
        <button
          key={index}
          onClick={() => handleKeywordClick(item.keyword)}
          className="bg-white border border-gray-200 rounded-lg p-3 text-left hover:border-blue-300 hover:shadow-sm transition-all"
        >
          <div className="font-medium text-gray-900 truncate">
            {item.keyword}
          </div>
          <div className="text-sm text-gray-500">
            {item.total_occurrences} occurrences
          </div>
        </button>
      ))}
    </div>
  );
};

export default SearchPage;
