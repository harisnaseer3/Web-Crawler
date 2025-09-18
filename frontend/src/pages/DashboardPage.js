import React, { useEffect, useState } from 'react';
import { useCrawler } from '../services/CrawlerContext';
import { crawlerAPI } from '../services/api';
import { 
  Play, 
  Square, 
  Pause, 
  RefreshCw, 
  Globe, 
  FileText, 
  Tag, 
  Activity,
  Database,
  Server
} from 'lucide-react';

const DashboardPage = () => {
  const {
    active,
    status,
    stats,
    loading,
    error,
    startCrawl,
    stopCrawl,
    pauseCrawl,
    resumeCrawl,
    refreshStats,
    populateQueue,
    clearError,
  } = useCrawler();

  const [network, setNetwork] = useState('0.0.0.0/0');
  const [maxIps, setMaxIps] = useState('');
  const [queueCount, setQueueCount] = useState(1000);
  const [recentIps, setRecentIps] = useState([]);

  useEffect(() => {
    refreshStats();
    const loadIps = async () => {
      try {
        const data = await crawlerAPI.getRecentDetectedIps(50);
        setRecentIps(data.ips || []);
      } catch (e) {
        // ignore network errors in UI
      }
    };
    loadIps();
  }, [refreshStats]);

  const handleStartCrawl = async () => {
    try {
      await startCrawl(network, maxIps ? parseInt(maxIps) : null);
    } catch (error) {
      console.error('Failed to start crawl:', error);
    }
  };

  const handleStopCrawl = async () => {
    try {
      await stopCrawl();
    } catch (error) {
      console.error('Failed to stop crawl:', error);
    }
  };

  const handlePauseCrawl = async () => {
    try {
      await pauseCrawl();
    } catch (error) {
      console.error('Failed to pause crawl:', error);
    }
  };

  const handleResumeCrawl = async () => {
    try {
      await resumeCrawl();
    } catch (error) {
      console.error('Failed to resume crawl:', error);
    }
  };

  const handlePopulateQueue = async () => {
    try {
      await populateQueue(network, queueCount);
    } catch (error) {
      console.error('Failed to populate queue:', error);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'running':
        return 'text-green-600 bg-green-100';
      case 'stopped':
        return 'text-red-600 bg-red-100';
      case 'paused':
        return 'text-yellow-600 bg-yellow-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Crawler Dashboard
          </h1>
          <p className="text-gray-600">
            Monitor and control the web crawler operations
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="error-message mb-6">
            <div className="flex justify-between items-center">
              <p>{error}</p>
              <button
                onClick={clearError}
                className="text-red-600 hover:text-red-800"
              >
                ×
              </button>
            </div>
          </div>
        )}

        {/* Status and Controls */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* Status Card */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Crawler Status
            </h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">Status:</span>
                <span className={`status-indicator ${getStatusColor(status)}`}>
                  <Activity className="w-4 h-4" />
                  {status.charAt(0).toUpperCase() + status.slice(1)}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">Active:</span>
                <span className={active ? 'text-green-600' : 'text-red-600'}>
                  {active ? 'Yes' : 'No'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">Last Update:</span>
                <span className="text-sm text-gray-600">
                  {formatDate(stats.last_update)}
                </span>
              </div>
            </div>
          </div>

          {/* Controls Card */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Crawler Controls
            </h3>
            <div className="space-y-4">
              <div className="flex space-x-2">
                {!active ? (
                  <button
                    onClick={handleStartCrawl}
                    disabled={loading}
                    className="flex-1 bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 disabled:opacity-50 flex items-center justify-center space-x-2"
                  >
                    <Play className="w-4 h-4" />
                    <span>Start</span>
                  </button>
                ) : (
                  <>
                    {status === 'running' ? (
                      <button
                        onClick={handlePauseCrawl}
                        disabled={loading}
                        className="flex-1 bg-yellow-600 text-white px-4 py-2 rounded-md hover:bg-yellow-700 disabled:opacity-50 flex items-center justify-center space-x-2"
                      >
                        <Pause className="w-4 h-4" />
                        <span>Pause</span>
                      </button>
                    ) : (
                      <button
                        onClick={handleResumeCrawl}
                        disabled={loading}
                        className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center space-x-2"
                      >
                        <RefreshCw className="w-4 h-4" />
                        <span>Resume</span>
                      </button>
                    )}
                    <button
                      onClick={handleStopCrawl}
                      disabled={loading}
                      className="flex-1 bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 disabled:opacity-50 flex items-center justify-center space-x-2"
                    >
                      <Square className="w-4 h-4" />
                      <span>Stop</span>
                    </button>
                  </>
                )}
              </div>
              
              <button
                onClick={refreshStats}
                disabled={loading}
                className="w-full bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700 disabled:opacity-50 flex items-center justify-center space-x-2"
              >
                <RefreshCw className="w-4 h-4" />
                <span>Refresh Stats</span>
              </button>
            </div>
          </div>

          {/* Configuration Card */}
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Configuration
            </h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Network Range
                </label>
                <input
                  type="text"
                  value={network}
                  onChange={(e) => setNetwork(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="0.0.0.0/0"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Max IPs (optional)
                </label>
                <input
                  type="number"
                  value={maxIps}
                  onChange={(e) => setMaxIps(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="10000"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Queue Count
                </label>
                <input
                  type="number"
                  value={queueCount}
                  onChange={(e) => setQueueCount(parseInt(e.target.value))}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <button
                onClick={handlePopulateQueue}
                disabled={loading}
                className="w-full bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center space-x-2"
              >
                <Database className="w-4 h-4" />
                <span>Populate Queue</span>
              </button>
            </div>
          </div>
        </div>

        {/* Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard
            title="Active Hosts"
            value={stats.active_hosts?.toLocaleString() || '0'}
            icon={<Globe className="w-6 h-6" />}
            color="text-blue-600"
          />
          <StatCard
            title="Total Hosts"
            value={stats.total_hosts?.toLocaleString() || '0'}
            icon={<Server className="w-6 h-6" />}
            color="text-green-600"
          />
          <StatCard
            title="Total Pages"
            value={stats.total_pages?.toLocaleString() || '0'}
            icon={<FileText className="w-6 h-6" />}
            color="text-purple-600"
          />
          <StatCard
            title="Keywords"
            value={stats.total_keywords?.toLocaleString() || '0'}
            icon={<Tag className="w-6 h-6" />}
            color="text-orange-600"
          />
          <StatCard
            title="Positive Detections"
            value={stats.positive_detections?.toLocaleString() || '0'}
            icon={<Activity className="w-6 h-6" />}
            color="text-red-600"
          />
        </div>

        {/* Additional Stats */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Crawl Progress
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Total Crawled:</span>
                <span className="font-semibold">{stats.total_crawled?.toLocaleString() || '0'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Queue Size:</span>
                <span className="font-semibold">{stats.queue_size?.toLocaleString() || '0'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Success Rate:</span>
                <span className="font-semibold">
                  {stats.total_hosts > 0 
                    ? ((stats.active_hosts / stats.total_hosts) * 100).toFixed(1) + '%'
                    : '0%'
                  }
                </span>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              System Information
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Crawl Status:</span>
                <span className={`font-semibold ${getStatusColor(stats.crawl_status)}`}>
                  {stats.crawl_status?.charAt(0).toUpperCase() + stats.crawl_status?.slice(1) || 'Unknown'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Last Update:</span>
                <span className="text-sm font-semibold">
                  {formatDate(stats.last_update)}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Recent Positive IPs */}
        <div className="bg-white rounded-lg shadow-sm p-6 mt-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Recent Positive IPs</h3>
            <button
              onClick={async () => {
                try {
                  const data = await crawlerAPI.getRecentDetectedIps(50);
                  setRecentIps(data.ips || []);
                } catch {}
              }}
              className="text-sm text-blue-600 hover:text-blue-800 flex items-center gap-1"
            >
              <RefreshCw className="w-4 h-4" /> Refresh
            </button>
          </div>
          {recentIps && recentIps.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {recentIps.map((ip, idx) => (
                <span key={idx} className="px-2 py-1 text-xs bg-green-100 text-green-700 rounded">{ip}</span>
              ))}
            </div>
          ) : (
            <div className="text-sm text-gray-500">No recent detections yet.</div>
          )}
        </div>
      </div>
    </div>
  );
};

const StatCard = ({ title, value, icon, color }) => (
  <div className="stat-card">
    <div className="flex items-center justify-between mb-2">
      <h4 className="text-sm font-medium text-gray-600">{title}</h4>
      <div className={color}>{icon}</div>
    </div>
    <div className="stat-value">{value}</div>
  </div>
);

export default DashboardPage;
