import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  FileSpreadsheet, 
  Download, 
  Clock, 
  CheckCircle, 
  AlertCircle, 
  Loader2, 
  Play,
  Eye,
  Settings
} from 'lucide-react';
import axios from 'axios';
import { API_URL } from '../utils/constants';

interface FileDetails {
  id: string;
  original_filename: string;
  status: string;
  created_at: number;
  completed_at?: number;
  message: string;
}

interface PreviewData {
  columns: string[];
  data: Record<string, any>[];
}

const FileDetails: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [details, setDetails] = useState<FileDetails | null>(null);
  const [preview, setPreview] = useState<PreviewData | null>(null);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [processingOptions, setProcessingOptions] = useState({
    remove_duplicates: true,
    fill_nulls: true,
    null_value: 0,
    normalize: false
  });

  useEffect(() => {
    const fetchData = async () => {
      try {
        const detailsResponse = await axios.get(`${API_URL}/jobs/${id}`);
        setDetails(detailsResponse.data);
        
        if (detailsResponse.data.status === 'uploaded' || detailsResponse.data.status === 'completed') {
          try {
            const previewResponse = await axios.get(`${API_URL}/preview/${id}`);
            setPreview(previewResponse.data);
          } catch (error) {
            console.error('Error fetching file preview:', error);
          }
        }
        
      } catch (error) {
        console.error('Error fetching file details:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    
    // Poll for updates if status is processing
    let interval: number | null = null;
    if (details?.status === 'processing') {
      interval = window.setInterval(async () => {
        try {
          const response = await axios.get(`${API_URL}/jobs/${id}`);
          setDetails(response.data);
          if (response.data.status !== 'processing') {
            if (interval) clearInterval(interval);
            if (response.data.status === 'completed') {
              const previewResponse = await axios.get(`${API_URL}/preview/${id}`);
              setPreview(previewResponse.data);
            }
          }
        } catch (error) {
          console.error('Error polling job status:', error);
          if (interval) clearInterval(interval);
        }
      }, 2000);
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [id, details?.status]);

  const handleProcessFile = async () => {
    if (!id) return;
    
    setProcessing(true);
    
    try {
      const response = await axios.post(`${API_URL}/process/${id}`, processingOptions);
      setDetails(prevDetails => {
        if (!prevDetails) return null;
        return { ...prevDetails, status: 'processing', message: 'Processing in progress' };
      });
    } catch (error) {
      console.error('Error processing file:', error);
    } finally {
      setProcessing(false);
    }
  };

  const handleDownloadProcessed = () => {
    if (details?.status === 'completed') {
      window.open(`${API_URL}/download/${id}`, '_blank');
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'uploaded':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
            <Clock className="h-3 w-3 mr-1" />
            Uploaded
          </span>
        );
      case 'processing':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
            <Loader2 className="h-3 w-3 mr-1 animate-spin" />
            Processing
          </span>
        );
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

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 text-blue-500 animate-spin" />
      </div>
    );
  }

  if (!details) {
    return (
      <div className="max-w-3xl mx-auto text-center p-8">
        <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-3" />
        <h2 className="text-lg font-medium text-gray-900 mb-1">File not found</h2>
        <p className="text-sm text-gray-500 mb-4">The requested file could not be found</p>
        <Link
          to="/dashboard"
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          Return to Dashboard
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">{details.original_filename}</h1>
          <div className="flex items-center space-x-2 mt-1">
            {getStatusBadge(details.status)}
            <span className="text-sm text-gray-500">
              Uploaded {new Date(details.created_at * 1000).toLocaleString()}
            </span>
          </div>
        </div>
        
        <div className="flex space-x-3">
          {details.status === 'completed' && (
            <button
              onClick={handleDownloadProcessed}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
            >
              <Download className="mr-2 h-4 w-4" />
              Download Processed
            </button>
          )}
          
          {details.status === 'uploaded' && (
            <button
              onClick={handleProcessFile}
              disabled={processing}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              {processing ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <Play className="mr-2 h-4 w-4" />
                  Process File
                </>
              )}
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-2 space-y-6">
          {/* File Preview */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <h2 className="text-lg font-medium text-gray-900">Data Preview</h2>
              <div className="flex items-center">
                <Eye className="h-4 w-4 text-gray-500 mr-1" />
                <span className="text-sm text-gray-500">
                  {preview ? 'First 5 rows' : 'Preview unavailable'}
                </span>
              </div>
            </div>
            
            <div className="p-0">
              {preview ? (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        {preview.columns.map((column, index) => (
                          <th
                            key={index}
                            scope="col"
                            className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                          >
                            {column}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {preview.data.map((row, rowIndex) => (
                        <tr key={rowIndex} className={rowIndex % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                          {preview.columns.map((column, colIndex) => (
                            <td key={colIndex} className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {row[column] !== null && row[column] !== undefined ? String(row[column]) : '-'}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center p-8 text-center">
                  <FileSpreadsheet className="h-12 w-12 text-gray-400 mb-3" />
                  <h3 className="text-lg font-medium text-gray-900 mb-1">No preview available</h3>
                  <p className="text-sm text-gray-500">
                    {details.status === 'processing' 
                      ? 'Preview will be available once processing completes' 
                      : 'Unable to generate preview for this file'}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Processing Status */}
          {details.status === 'processing' && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
              <div className="p-6">
                <div className="flex items-center space-x-3 mb-4">
                  <div className="h-8 w-8 bg-blue-100 rounded-full flex items-center justify-center">
                    <Loader2 className="h-5 w-5 text-blue-600 animate-spin" />
                  </div>
                  <div>
                    <h3 className="text-lg font-medium text-gray-900">Processing in Progress</h3>
                    <p className="text-sm text-gray-500">Your file is being processed...</p>
                  </div>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2.5">
                  <div className="bg-blue-600 h-2.5 rounded-full animate-pulse w-3/4"></div>
                </div>
              </div>
            </div>
          )}

          {/* Processing Results */}
          {details.status === 'completed' && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-lg font-medium text-gray-900">Processing Results</h2>
              </div>
              <div className="p-6">
                <div className="flex items-center space-x-3 mb-4">
                  <div className="h-8 w-8 bg-green-100 rounded-full flex items-center justify-center">
                    <CheckCircle className="h-5 w-5 text-green-600" />
                  </div>
                  <div>
                    <h3 className="text-lg font-medium text-gray-900">Processing Complete</h3>
                    <p className="text-sm text-gray-500">
                      Completed at {new Date(details.completed_at! * 1000).toLocaleString()}
                    </p>
                  </div>
                </div>
                <div className="mt-4 bg-green-50 border border-green-100 rounded-md p-4">
                  <p className="text-sm text-green-800">{details.message}</p>
                </div>
                <div className="mt-4">
                  <button
                    onClick={handleDownloadProcessed}
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                  >
                    <Download className="mr-2 h-4 w-4" />
                    Download Processed File
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Processing Error */}
          {details.status === 'failed' && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-lg font-medium text-gray-900">Processing Error</h2>
              </div>
              <div className="p-6">
                <div className="flex items-center space-x-3 mb-4">
                  <div className="h-8 w-8 bg-red-100 rounded-full flex items-center justify-center">
                    <AlertCircle className="h-5 w-5 text-red-600" />
                  </div>
                  <div>
                    <h3 className="text-lg font-medium text-gray-900">Processing Failed</h3>
                    <p className="text-sm text-gray-500">
                      An error occurred during processing
                    </p>
                  </div>
                </div>
                <div className="mt-4 bg-red-50 border border-red-100 rounded-md p-4">
                  <p className="text-sm text-red-800">{details.message}</p>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="space-y-6">
          {/* File Info */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-medium text-gray-900">File Information</h2>
            </div>
            <div className="p-6">
              <div className="space-y-4">
                <div>
                  <h3 className="text-sm font-medium text-gray-500">File Name</h3>
                  <p className="mt-1 text-sm text-gray-900">{details.original_filename}</p>
                </div>
                <div>
                  <h3 className="text-sm font-medium text-gray-500">Upload Date</h3>
                  <p className="mt-1 text-sm text-gray-900">
                    {new Date(details.created_at * 1000).toLocaleString()}
                  </p>
                </div>
                <div>
                  <h3 className="text-sm font-medium text-gray-500">Status</h3>
                  <p className="mt-1">{getStatusBadge(details.status)}</p>
                </div>
                {details.completed_at && (
                  <div>
                    <h3 className="text-sm font-medium text-gray-500">Completed At</h3>
                    <p className="mt-1 text-sm text-gray-900">
                      {new Date(details.completed_at * 1000).toLocaleString()}
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Processing Options */}
          {details.status === 'uploaded' && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
                <h2 className="text-lg font-medium text-gray-900">Processing Options</h2>
                <Settings className="h-4 w-4 text-gray-500" />
              </div>
              <div className="p-6">
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-sm font-medium text-gray-900">Remove Duplicates</h3>
                      <p className="text-xs text-gray-500">
                        Remove duplicate rows from the dataset
                      </p>
                    </div>
                    <div className="relative inline-block w-10 align-middle select-none">
                      <input
                        type="checkbox"
                        id="remove-duplicates"
                        checked={processingOptions.remove_duplicates}
                        onChange={() => setProcessingOptions(prev => ({
                          ...prev,
                          remove_duplicates: !prev.remove_duplicates
                        }))}
                        className="sr-only peer"
                      />
                      <label
                        htmlFor="remove-duplicates"
                        className="block overflow-hidden h-6 rounded-full bg-gray-200 cursor-pointer peer-checked:bg-blue-600"
                      >
                        <span className="absolute inset-y-0 left-0 w-6 h-6 bg-white rounded-full shadow transform transition-transform duration-300 ease-in-out peer-checked:translate-x-4"></span>
                      </label>
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-sm font-medium text-gray-900">Fill Null Values</h3>
                      <p className="text-xs text-gray-500">
                        Replace null values with a default value
                      </p>
                    </div>
                    <div className="relative inline-block w-10 align-middle select-none">
                      <input
                        type="checkbox"
                        id="fill-nulls"
                        checked={processingOptions.fill_nulls}
                        onChange={() => setProcessingOptions(prev => ({
                          ...prev,
                          fill_nulls: !prev.fill_nulls
                        }))}
                        className="sr-only peer"
                      />
                      <label
                        htmlFor="fill-nulls"
                        className="block overflow-hidden h-6 rounded-full bg-gray-200 cursor-pointer peer-checked:bg-blue-600"
                      >
                        <span className="absolute inset-y-0 left-0 w-6 h-6 bg-white rounded-full shadow transform transition-transform duration-300 ease-in-out peer-checked:translate-x-4"></span>
                      </label>
                    </div>
                  </div>

                  {processingOptions.fill_nulls && (
                    <div>
                      <h3 className="text-sm font-medium text-gray-900 mb-1">Default Value for Nulls</h3>
                      <input
                        type="number"
                        value={processingOptions.null_value}
                        onChange={(e) => setProcessingOptions(prev => ({
                          ...prev,
                          null_value: Number(e.target.value)
                        }))}
                        className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                      />
                    </div>
                  )}

                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-sm font-medium text-gray-900">Normalize Data</h3>
                      <p className="text-xs text-gray-500">
                        Scale numeric columns to a 0-1 range
                      </p>
                    </div>
                    <div className="relative inline-block w-10 align-middle select-none">
                      <input
                        type="checkbox"
                        id="normalize"
                        checked={processingOptions.normalize}
                        onChange={() => setProcessingOptions(prev => ({
                          ...prev,
                          normalize: !prev.normalize
                        }))}
                        className="sr-only peer"
                      />
                      <label
                        htmlFor="normalize"
                        className="block overflow-hidden h-6 rounded-full bg-gray-200 cursor-pointer peer-checked:bg-blue-600"
                      >
                        <span className="absolute inset-y-0 left-0 w-6 h-6 bg-white rounded-full shadow transform transition-transform duration-300 ease-in-out peer-checked:translate-x-4"></span>
                      </label>
                    </div>
                  </div>

                  <div className="pt-4">
                    <button
                      onClick={handleProcessFile}
                      disabled={processing}
                      className="w-full inline-flex justify-center items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                      {processing ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Processing...
                        </>
                      ) : (
                        <>
                          <Play className="mr-2 h-4 w-4" />
                          Process File
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default FileDetails;