import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  FileSpreadsheet, 
  Download, 
  CheckCircle, 
  AlertCircle, 
  Loader2, 
  Search,
  RefreshCw,
  ArrowDownAZ,
  ArrowUpZA,
  Calendar
} from 'lucide-react';
import axios from 'axios';
import { API_URL } from '../utils/constants';

interface Job {
  id: string;
  original_filename: string;
  status: string;
  created_at: number;
  completed_at?: number;
  message: string;
}

const ProcessedFiles: React.FC = () => {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [refreshing, setRefreshing] = useState(false);
  const [sortField, setSortField] = useState<'original_filename' | 'created_at'>('created_at');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');

  const fetchJobs = async () => {
    try {
      const response = await axios.get(`${API_URL}/jobs`);
      const allJobs = response.data;
      
      // Filter to show only completed and failed jobs
      const processedJobs = allJobs.filter(
        job => job.status === 'completed' || job.status === 'failed'
      );
      
      setJobs(processedJobs);
    } catch (error) {
      console.error('Error fetching jobs:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchJobs();
  };

  const handleSort = (field: 'original_filename' | 'created_at') => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const handleDownload = (id: string) => {
    window.open(`${API_URL}/download/${id}`, '_blank');
  };

  const filteredJobs = jobs
    .filter(job => 
      job.original_filename.toLowerCase().includes(searchTerm.toLowerCase())
    )
    .sort((a, b) => {
      if (sortField === 'original_filename') {
        return sortDirection === 'asc'
          ? a.original_filename.localeCompare(b.original_filename)
          : b.original_filename.localeCompare(a.original_filename);
      } else {
        return sortDirection === 'asc'
          ? a.created_at - b.created_at
          : b.created_at - a.created_at;
      }
    });

  const statusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
            <CheckCircle className="h-3 w-3 mr-1" />
            Completed
          </span>
        );
      case 'failed':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
            <AlertCircle className="h-3 w-3 mr-1" />
            Failed
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
            {status}
          </span>
        );
    }
  };
  
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-gray-900">Processed Files</h1>
        
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin text-blue-500' : 'text-gray-500'}`} />
          Refresh
        </button>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center">
            <div className="relative flex-grow">
              <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
                <Search className="h-5 w-5 text-gray-400" />
              </div>
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search files..."
                className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              />
            </div>
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center p-8">
            <Loader2 className="h-8 w-8 text-blue-500 animate-spin" />
          </div>
        ) : filteredJobs.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    <button 
                      className="flex items-center space-x-1 focus:outline-none"
                      onClick={() => handleSort('original_filename')}
                    >
                      <span>File</span>
                      {sortField === 'original_filename' && (
                        sortDirection === 'asc'
                          ? <ArrowDownAZ className="h-4 w-4 text-gray-400" />
                          : <ArrowUpZA className="h-4 w-4 text-gray-400" />
                      )}
                    </button>
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    <button 
                      className="flex items-center space-x-1 focus:outline-none"
                      onClick={() => handleSort('created_at')}
                    >
                      <span>Date</span>
                      {sortField === 'created_at' && (
                        sortDirection === 'asc'
                          ? <Calendar className="h-4 w-4 text-gray-400" />
                          : <Calendar className="h-4 w-4 text-gray-400" />
                      )}
                    </button>
                  </th>
                  <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredJobs.map((job) => (
                  <tr key={job.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Link to={`/files/${job.id}`} className="flex items-center">
                        <FileSpreadsheet className="h-5 w-5 text-gray-400 mr-3" />
                        <div className="text-sm font-medium text-blue-600 hover:text-blue-800">
                          {job.original_filename}
                        </div>
                      </Link>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {statusBadge(job.status)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(job.created_at * 1000).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      {job.status === 'completed' && (
                        <button
                          onClick={() => handleDownload(job.id)}
                          className="inline-flex items-center px-3 py-1 border border-transparent text-xs font-medium rounded text-white bg-green-600 hover:bg-green-700"
                        >
                          <Download className="h-3 w-3 mr-1" />
                          Download
                        </button>
                      )}
                      <Link
                        to={`/files/${job.id}`}
                        className="ml-2 text-blue-600 hover:text-blue-900"
                      >
                        Details
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center p-8 text-center">
            <FileSpreadsheet className="h-12 w-12 text-gray-400 mb-3" />
            <h3 className="text-lg font-medium text-gray-900 mb-1">No processed files</h3>
            <p className="text-sm text-gray-500 mb-4">
              {searchTerm 
                ? 'No results match your search' 
                : 'Upload and process your first CSV file'}
            </p>
            <Link
              to="/upload"
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Upload New CSV
            </Link>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProcessedFiles;