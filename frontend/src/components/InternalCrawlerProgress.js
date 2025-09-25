import React, { useState, useEffect } from 'react';
import { RefreshCw, Activity, Globe, FileText, AlertCircle, CheckCircle, Clock } from 'lucide-react';
import { crawlerAPI } from '../services/api';

const InternalCrawlerProgress = () => {
  const [progress, setProgress] = useState(null);
  const [events, setEvents] = useState([]);
  const [isRunning, setIsRunning] = useState(false);
  const [loading, setLoading] = useState(false);

  const fetchProgress = async () => {
    try {
      const [progressData, eventsData] = await Promise.all([
        crawlerAPI.getInternalCrawlProgress(),
        crawlerAPI.getInternalCrawlEvents(20)
      ]);
      
      setProgress(progressData.progress);
      setIsRunning(progressData.is_running);
      setEvents(eventsData.events || []);
    } catch (error) {
      console.error('Failed to fetch progress:', error);
    }
  };

  useEffect(() => {
    fetchProgress();
    
    // Poll for updates every 2 seconds when running
    const interval = setInterval(() => {
      if (isRunning) {
        fetchProgress();
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [isRunning]);

  const formatTime = (timestamp) => {
    if (!timestamp) return 'N/A';
    return new Date(timestamp).toLocaleTimeString();
  };

  const formatElapsed = (seconds) => {
    if (!seconds) return 'N/A';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}m ${secs}s`;
  };

  const getEventIcon = (eventType) => {
    switch (eventType) {
      case 'crawl_start':
      case 'host_start':
        return <Activity className="w-4 h-4 text-blue-500" />;
      case 'page_success':
      case 'host_success':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'page_error':
      case 'host_error':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      case 'page_crawl':
        return <Globe className="w-4 h-4 text-blue-400" />;
      case 'crawl_complete':
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      default:
        return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  const getEventColor = (eventType) => {
    switch (eventType) {
      case 'crawl_start':
      case 'host_start':
        return 'bg-blue-50 border-blue-200';
      case 'page_success':
      case 'host_success':
        return 'bg-green-50 border-green-200';
      case 'page_error':
      case 'host_error':
        return 'bg-red-50 border-red-200';
      case 'page_crawl':
        return 'bg-blue-50 border-blue-200';
      case 'crawl_complete':
        return 'bg-green-50 border-green-200';
      default:
        return 'bg-gray-50 border-gray-200';
    }
  };

  if (!progress) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex items-center justify-center">
          <RefreshCw className="w-6 h-6 animate-spin text-gray-400" />
          <span className="ml-2 text-gray-600">Loading progress...</span>
        </div>
      </div>
    );
  }

  const progressPercentage = progress.total_hosts > 0 
    ? (progress.hosts_processed / progress.total_hosts) * 100 
    : 0;

  return (
    <div className="space-y-6">
      {/* Progress Overview */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">
            Internal Crawler Progress
          </h3>
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${isRunning ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`}></div>
            <span className="text-sm text-gray-600">
              {isRunning ? 'Running' : 'Stopped'}
            </span>
            <button
              onClick={fetchProgress}
              disabled={loading}
              className="p-1 text-gray-400 hover:text-gray-600"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mb-4">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>Overall Progress</span>
            <span>{progress.hosts_processed} / {progress.total_hosts} hosts</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progressPercentage}%` }}
            ></div>
          </div>
          <div className="text-xs text-gray-500 mt-1">
            {progressPercentage.toFixed(1)}% complete
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{progress.total_hosts}</div>
            <div className="text-sm text-gray-600">Total Hosts</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{progress.hosts_processed}</div>
            <div className="text-sm text-gray-600">Processed</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">{progress.total_pages_discovered}</div>
            <div className="text-sm text-gray-600">Pages Found</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-600">{progress.errors?.length || 0}</div>
            <div className="text-sm text-gray-600">Errors</div>
          </div>
        </div>

        {/* Current Activity */}
        {isRunning && (
          <div className="bg-blue-50 rounded-lg p-4">
            <h4 className="font-medium text-blue-900 mb-2">Current Activity</h4>
            <div className="text-sm text-blue-800">
              {progress.current_host && (
                <div className="mb-1">
                  <strong>Host:</strong> {progress.current_host}
                </div>
              )}
              {progress.current_host_pages > 0 && (
                <div className="mb-1">
                  <strong>Pages found:</strong> {progress.current_host_pages}
                </div>
              )}
              {progress.elapsed_seconds && (
                <div>
                  <strong>Elapsed:</strong> {formatElapsed(progress.elapsed_seconds)}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Recent URLs */}
        {progress.current_host_urls && progress.current_host_urls.length > 0 && (
          <div className="mt-4">
            <h4 className="font-medium text-gray-900 mb-2">Recent URLs Found</h4>
            <div className="max-h-32 overflow-y-auto space-y-1">
              {progress.current_host_urls.slice(-5).map((url, index) => (
                <div key={index} className="text-xs text-gray-600 bg-gray-50 px-2 py-1 rounded">
                  {url}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Recent Events */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Events</h3>
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {events.length === 0 ? (
            <div className="text-center text-gray-500 py-4">No events yet</div>
          ) : (
            events.map((event, index) => (
              <div 
                key={index} 
                className={`flex items-start space-x-3 p-3 rounded-lg border ${getEventColor(event.type)}`}
              >
                <div className="flex-shrink-0 mt-0.5">
                  {getEventIcon(event.type)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-gray-900">
                    {event.message}
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    {formatTime(event.timestamp)}
                  </div>
                  {event.data && Object.keys(event.data).length > 0 && (
                    <div className="text-xs text-gray-600 mt-1">
                      {Object.entries(event.data).map(([key, value]) => (
                        <span key={key} className="mr-3">
                          <strong>{key}:</strong> {String(value)}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default InternalCrawlerProgress;


