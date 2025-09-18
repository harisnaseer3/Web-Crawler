import React, { createContext, useContext, useReducer } from 'react';
import { searchAPI } from './api';

const SearchContext = createContext();

const initialState = {
  searchResults: [],
  totalCount: 0,
  query: '',
  loading: false,
  error: null,
  currentPage: 1,
  resultsPerPage: 10,
  executionTime: 0,
};

const searchReducer = (state, action) => {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    case 'SET_ERROR':
      return { ...state, error: action.payload, loading: false };
    case 'SET_RESULTS':
      return {
        ...state,
        searchResults: action.payload.results,
        totalCount: action.payload.totalCount,
        query: action.payload.query,
        executionTime: action.payload.executionTime,
        loading: false,
        error: null,
      };
    case 'CLEAR_RESULTS':
      return {
        ...state,
        searchResults: [],
        totalCount: 0,
        query: '',
        executionTime: 0,
        error: null,
      };
    case 'SET_PAGE':
      return { ...state, currentPage: action.payload };
    case 'SET_RESULTS_PER_PAGE':
      return { ...state, resultsPerPage: action.payload, currentPage: 1 };
    default:
      return state;
  }
};

export const SearchProvider = ({ children }) => {
  const [state, dispatch] = useReducer(searchReducer, initialState);

  const search = async (query, page = 1, limit = 10) => {
    if (!query.trim()) {
      dispatch({ type: 'CLEAR_RESULTS' });
      return;
    }

    dispatch({ type: 'SET_LOADING', payload: true });
    dispatch({ type: 'SET_ERROR', payload: null });

    try {
      const offset = (page - 1) * limit;
      const response = await searchAPI.search(query, limit, offset);
      
      dispatch({
        type: 'SET_RESULTS',
        payload: {
          results: response.results,
          totalCount: response.total_count,
          query: response.query,
          executionTime: response.execution_time,
        },
      });
      
      dispatch({ type: 'SET_PAGE', payload: page });
    } catch (error) {
      console.error('Search error:', error);
      dispatch({
        type: 'SET_ERROR',
        payload: error.response?.data?.detail || 'Search failed. Please try again.',
      });
    }
  };

  const searchByDomain = async (domain, page = 1, limit = 10) => {
    if (!domain.trim()) {
      dispatch({ type: 'CLEAR_RESULTS' });
      return;
    }

    dispatch({ type: 'SET_LOADING', payload: true });
    dispatch({ type: 'SET_ERROR', payload: null });

    try {
      const offset = (page - 1) * limit;
      const response = await searchAPI.searchByDomain(domain, limit, offset);
      
      dispatch({
        type: 'SET_RESULTS',
        payload: {
          results: response.results,
          totalCount: response.total_count,
          query: response.query,
          executionTime: response.execution_time,
        },
      });
      
      dispatch({ type: 'SET_PAGE', payload: page });
    } catch (error) {
      console.error('Domain search error:', error);
      dispatch({
        type: 'SET_ERROR',
        payload: error.response?.data?.detail || 'Domain search failed. Please try again.',
      });
    }
  };

  const clearResults = () => {
    dispatch({ type: 'CLEAR_RESULTS' });
  };

  const setPage = (page) => {
    dispatch({ type: 'SET_PAGE', payload: page });
  };

  const setResultsPerPage = (limit) => {
    dispatch({ type: 'SET_RESULTS_PER_PAGE', payload: limit });
  };

  const value = {
    ...state,
    search,
    searchByDomain,
    clearResults,
    setPage,
    setResultsPerPage,
  };

  return (
    <SearchContext.Provider value={value}>
      {children}
    </SearchContext.Provider>
  );
};

export const useSearch = () => {
  const context = useContext(SearchContext);
  if (!context) {
    throw new Error('useSearch must be used within a SearchProvider');
  }
  return context;
};
