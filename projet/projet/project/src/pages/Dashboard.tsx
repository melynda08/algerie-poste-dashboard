import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Upload, FileSpreadsheet, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import axios from 'axios';
import { API_URL } from '../utils/constants';

interface JobStats {
  total: number;
  processing: number;
  completed: number;
  failed: number;
}

const Dashboard: React.FC = () => {
  const [recentJobs, setRecentJobs] = useState([]);
  const [stats, setStats] = useState<JobStats>({
    total: 0,
    processing: 0,
    completed: 0,
    failed: 0
  });
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const response = await axios.get(`${API_URL}/jobs`);
      const jobs = response.data;
      
      setRecentJobs(jobs.slice(0, 5));
      
      // Calculate stats
      const total = jobs.length;
      const processing = jobs.filter(job => job.status === 'processing').length;
      const completed = jobs.filter(job => job.status === 'completed').length;
      const failed = jobs.filter(job => job.status === 'failed').length;
      
      setStats({ total, processing, completed, failed });
      setLoading(false);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    
    // Poll for updates every 5 seconds
    const interval = setInterval(fetchData, 5000);
    
    return () => clearInterval(interval);
  }, []);

  const statusIcon = (status) => {
    switch (status) {
      case 'uploaded':
        return <FileSpreadsheet className="h-5 w-5 text-gray-500" />;
      case 'processing':
        return <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />;
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'failed':
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      default:
        return <FileSpreadsheet className="h-5 w-5 text-gray-500" />;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-gray-900">Dashboard</h1>
        <Link
          to="/upload"
          className="flex items-center space-x-1 px-4 py-2 rounded-md bg-blue-600 text-white hover:bg-blue-700 transition-colors"
        >
          <Upload className="h-4 w-4" />
          <span>Upload New CSV</span>
        </Link>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
        <div className="bg-white p-5 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">Total Files</p>
              <p className="text-2xl font-semibold text-gray-900">{stats.total}</p>
            </div>
            <div className="h-10 w-10 bg-blue-100 rounded-full flex items-center justify-center">
              <FileSpreadsheet className="h-5 w-5 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="bg-white p-5 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">Processing</p>
              <p className="text-2xl font-semibold text-blue-600">{stats.processing}</p>
            </div>
            <div className="h-10 w-10 bg-blue-100 rounded-full flex items-center justify-center">
              <Loader2 className="h-5 w-5 text-blue-600 animate-spin" />
            </div>
          </div>
        </div>

        <div className="bg-white p-5 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">Completed</p>
              <p className="text-2xl font-semibold text-green-600">{stats.completed}</p>
            </div>
            <div className="h-10 w-10 bg-green-100 rounded-full flex items-center justify-center">
              <CheckCircle className="h-5 w-5 text-green-600" />
            </div>
          </div>
        </div>

        <div className="bg-white p-5 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-500">Failed</p>
              <p className="text-2xl font-semibold text-red-600">{stats.failed}</p>
            </div>
            <div className="h-10 w-10 bg-red-100 rounded-full flex items-center justify-center">
              <AlertCircle className="h-5 w-5 text-red-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Recent Jobs */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">Recent Files</h2>
        </div>
        {loading ? (
          <div className="flex items-center justify-center p-8">
            <Loader2 className="h-8 w-8 text-blue-500 animate-spin" />
          </div>
        ) : recentJobs.length > 0 ? (
          <div className="divide-y divide-gray-200">
            {recentJobs.map((job) => (
              <div 
                key={job.id}
                className="px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center space-x-3">
                  {statusIcon(job.status)}
                  <div>
                    <p className="text-sm font-medium text-gray-900">{job.original_filename}</p>
                    <p className="text-xs text-gray-500">
                      {new Date(job.created_at * 1000).toLocaleString()}
                    </p>
                  </div>
                </div>
                <div className="flex items-center">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium
                    ${job.status === 'completed' ? 'bg-green-100 text-green-800' : ''}
                    ${job.status === 'processing' ? 'bg-blue-100 text-blue-800' : ''}
                    ${job.status === 'failed' ? 'bg-red-100 text-red-800' : ''}
                    ${job.status === 'uploaded' ? 'bg-gray-100 text-gray-800' : ''}
                  `}>
                    {job.status.charAt(0).toUpperCase() + job.status.slice(1)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center p-8 text-center">
            <FileSpreadsheet className="h-12 w-12 text-gray-400 mb-3" />
            <h3 className="text-lg font-medium text-gray-900 mb-1">No files yet</h3>
            <p className="text-sm text-gray-500 mb-4">Upload your first CSV file to get started</p>
            <Link
              to="/upload"
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <Upload className="mr-2 h-4 w-4" />
              Upload CSV
            </Link>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;