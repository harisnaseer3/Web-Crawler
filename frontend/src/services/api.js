import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    console.log(`Making ${config.method?.toUpperCase()} request to ${config.url}`);
    return config;
  },
  (error) => {
    console.error('Request error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('Response error:', error);
    if (error.response) {
      // Server responded with error status
      console.error('Error data:', error.response.data);
    } else if (error.request) {
      // Request was made but no response received
      console.error('No response received:', error.request);
    } else {
      // Something else happened
      console.error('Error:', error.message);
    }
    return Promise.reject(error);
  }
);

// Search API
export const searchAPI = {
  search: async (query, limit = 10, offset = 0) => {
    const response = await api.post('/search/', {
      query,
      limit,
      offset,
    });
    return response.data;
  },

  searchByDomain: async (domain, limit = 10, offset = 0) => {
    const response = await api.get(`/search/domain/${domain}`, {
      params: { limit, offset },
    });
    return response.data;
  },

  getPopularKeywords: async (limit = 20) => {
    const response = await api.get('/search/keywords/popular', {
      params: { limit },
    });
    return response.data;
  },

  getHostDetails: async (ipAddress) => {
    const response = await api.get(`/search/host/${ipAddress}`);
    return response.data;
  },

  getSearchAnalytics: async (limit = 50) => {
    const response = await api.get('/search/analytics', {
      params: { limit },
    });
    return response.data;
  },
};

// Crawler API
export const crawlerAPI = {
  startCrawl: async (network = '0.0.0.0/0', maxIps = null) => {
    const response = await api.post('/crawl/start', {
      network,
      max_ips: maxIps,
    });
    return response.data;
  },

  stopCrawl: async () => {
    const response = await api.post('/crawl/stop');
    return response.data;
  },

  getStatus: async () => {
    const response = await api.get('/crawl/status');
    return response.data;
  },

  getStats: async () => {
    const response = await api.get('/crawl/stats');
    return response.data;
  },

  pauseCrawl: async () => {
    const response = await api.post('/crawl/pause');
    return response.data;
  },

  resumeCrawl: async () => {
    const response = await api.post('/crawl/resume');
    return response.data;
  },

  populateQueue: async (network = '0.0.0.0/0', count = 1000) => {
    const response = await api.post('/crawl/queue/populate', null, {
      params: { network, count },
    });
    return response.data;
  },

  getQueueStats: async () => {
    const response = await api.get('/crawl/queue/stats');
    return response.data;
  },

  listPositives: async (limit = 20, offset = 0) => {
    const response = await api.get('/crawl/positives', {
      params: { limit, offset },
    });
    return response.data;
  },

  addUrlToQueue: async (url, startIfStopped = false) => {
    const response = await api.post('/crawl/queue/add_url', {
      url,
      start_if_stopped: startIfStopped,
    });
    return response.data;
  },

  getRecentDetectedIps: async (limit = 50) => {
    const response = await api.get('/crawl/live/positives_ips', { params: { limit } });
    return response.data;
  },
};

// Health check
export const healthAPI = {
  check: async () => {
    const response = await api.get('/health');
    return response.data;
  },
};

export default api;
