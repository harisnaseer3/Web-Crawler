import React, { createContext, useContext, useReducer, useEffect } from 'react';
import { crawlerAPI } from './api';

const CrawlerContext = createContext();

const initialState = {
  active: false,
  status: 'stopped',
  stats: {
    active_hosts: 0,
    total_hosts: 0,
    total_keywords: 0,
    total_pages: 0,
    crawl_status: 'stopped',
    total_crawled: 0,
    last_update: null,
    queue_size: 0,
  },
  loading: false,
  error: null,
  threadCount: 0,
  queueSize: 0,
};

const crawlerReducer = (state, action) => {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    case 'SET_ERROR':
      return { ...state, error: action.payload, loading: false };
    case 'SET_STATUS':
      return {
        ...state,
        active: action.payload.active,
        status: action.payload.status,
        threadCount: action.payload.thread_count,
        queueSize: action.payload.queue_size,
        error: null,
      };
    case 'SET_STATS':
      return {
        ...state,
        stats: action.payload,
        error: null,
      };
    case 'CLEAR_ERROR':
      return { ...state, error: null };
    default:
      return state;
  }
};

export const CrawlerProvider = ({ children }) => {
  const [state, dispatch] = useReducer(crawlerReducer, initialState);

  // Poll for status updates when crawler is active
  useEffect(() => {
    let interval;
    
    if (state.active) {
      interval = setInterval(async () => {
        try {
          const statusResponse = await crawlerAPI.getStatus();
          const statsResponse = await crawlerAPI.getStats();
          
          dispatch({
            type: 'SET_STATUS',
            payload: {
              active: statusResponse.active,
              status: statusResponse.active ? 'running' : 'stopped',
              thread_count: statusResponse.thread_count,
              queue_size: statusResponse.queue_size,
            },
          });
          
          dispatch({
            type: 'SET_STATS',
            payload: statsResponse,
          });
        } catch (error) {
          console.error('Error polling crawler status:', error);
        }
      }, 2000); // Poll every 2 seconds
    }

    return () => {
      if (interval) {
        clearInterval(interval);
      }
    };
  }, [state.active]);

  const startCrawl = async (network = '0.0.0.0/0', maxIps = null) => {
    dispatch({ type: 'SET_LOADING', payload: true });
    dispatch({ type: 'SET_ERROR', payload: null });

    try {
      const response = await crawlerAPI.startCrawl(network, maxIps);
      
      if (response.status === 'started') {
        dispatch({
          type: 'SET_STATUS',
          payload: {
            active: true,
            status: 'running',
            thread_count: 0,
            queue_size: 0,
          },
        });
      } else if (response.status === 'already_running') {
        dispatch({ type: 'SET_ERROR', payload: 'Crawler is already running' });
      }
      
      dispatch({ type: 'SET_LOADING', payload: false });
      return response;
    } catch (error) {
      console.error('Start crawl error:', error);
      dispatch({
        type: 'SET_ERROR',
        payload: error.response?.data?.detail || 'Failed to start crawler',
      });
      dispatch({ type: 'SET_LOADING', payload: false });
      throw error;
    }
  };

  const stopCrawl = async () => {
    dispatch({ type: 'SET_LOADING', payload: true });
    dispatch({ type: 'SET_ERROR', payload: null });

    try {
      const response = await crawlerAPI.stopCrawl();
      
      dispatch({
        type: 'SET_STATUS',
        payload: {
          active: false,
          status: 'stopped',
          thread_count: 0,
          queue_size: 0,
        },
      });
      
      dispatch({ type: 'SET_LOADING', payload: false });
      return response;
    } catch (error) {
      console.error('Stop crawl error:', error);
      dispatch({
        type: 'SET_ERROR',
        payload: error.response?.data?.detail || 'Failed to stop crawler',
      });
      dispatch({ type: 'SET_LOADING', payload: false });
      throw error;
    }
  };

  const pauseCrawl = async () => {
    dispatch({ type: 'SET_LOADING', payload: true });
    dispatch({ type: 'SET_ERROR', payload: null });

    try {
      const response = await crawlerAPI.pauseCrawl();
      
      dispatch({
        type: 'SET_STATUS',
        payload: {
          active: true,
          status: 'paused',
          thread_count: state.threadCount,
          queue_size: state.queueSize,
        },
      });
      
      dispatch({ type: 'SET_LOADING', payload: false });
      return response;
    } catch (error) {
      console.error('Pause crawl error:', error);
      dispatch({
        type: 'SET_ERROR',
        payload: error.response?.data?.detail || 'Failed to pause crawler',
      });
      dispatch({ type: 'SET_LOADING', payload: false });
      throw error;
    }
  };

  const resumeCrawl = async () => {
    dispatch({ type: 'SET_LOADING', payload: true });
    dispatch({ type: 'SET_ERROR', payload: null });

    try {
      const response = await crawlerAPI.resumeCrawl();
      
      dispatch({
        type: 'SET_STATUS',
        payload: {
          active: true,
          status: 'running',
          thread_count: state.threadCount,
          queue_size: state.queueSize,
        },
      });
      
      dispatch({ type: 'SET_LOADING', payload: false });
      return response;
    } catch (error) {
      console.error('Resume crawl error:', error);
      dispatch({
        type: 'SET_ERROR',
        payload: error.response?.data?.detail || 'Failed to resume crawler',
      });
      dispatch({ type: 'SET_LOADING', payload: false });
      throw error;
    }
  };

  const refreshStats = async () => {
    try {
      const response = await crawlerAPI.getStats();
      dispatch({
        type: 'SET_STATS',
        payload: response,
      });
    } catch (error) {
      console.error('Refresh stats error:', error);
      dispatch({
        type: 'SET_ERROR',
        payload: error.response?.data?.detail || 'Failed to refresh stats',
      });
    }
  };

  const populateQueue = async (network = '0.0.0.0/0', count = 1000) => {
    dispatch({ type: 'SET_LOADING', payload: true });
    dispatch({ type: 'SET_ERROR', payload: null });

    try {
      const response = await crawlerAPI.populateQueue(network, count);
      dispatch({ type: 'SET_LOADING', payload: false });
      return response;
    } catch (error) {
      console.error('Populate queue error:', error);
      dispatch({
        type: 'SET_ERROR',
        payload: error.response?.data?.detail || 'Failed to populate queue',
      });
      dispatch({ type: 'SET_LOADING', payload: false });
      throw error;
    }
  };

  const clearError = () => {
    dispatch({ type: 'CLEAR_ERROR' });
  };

  const value = {
    ...state,
    startCrawl,
    stopCrawl,
    pauseCrawl,
    resumeCrawl,
    refreshStats,
    populateQueue,
    clearError,
  };

  return (
    <CrawlerContext.Provider value={value}>
      {children}
    </CrawlerContext.Provider>
  );
};

export const useCrawler = () => {
  const context = useContext(CrawlerContext);
  if (!context) {
    throw new Error('useCrawler must be used within a CrawlerProvider');
  }
  return context;
};
