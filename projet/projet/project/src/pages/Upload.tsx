import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import { FileSpreadsheet, Upload as UploadIcon, X, CheckCircle, AlertCircle } from 'lucide-react';
import axios from 'axios';
import { API_URL } from '../utils/constants';

const Upload: React.FC = () => {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState('');

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      const selectedFile = acceptedFiles[0];
      if (selectedFile.type === 'text/csv' || selectedFile.name.endsWith('.csv')) {
        setFile(selectedFile);
        setUploadStatus('idle');
        setErrorMessage('');
      } else {
        setErrorMessage('Only CSV files are allowed');
      }
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv']
    },
    maxFiles: 1
  });

  const handleRemoveFile = () => {
    setFile(null);
    setUploadStatus('idle');
    setErrorMessage('');
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setUploadStatus('uploading');
    setUploadProgress(0);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API_URL}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / (progressEvent.total || 100)
          );
          setUploadProgress(percentCompleted);
        }
      });

      setUploadStatus('success');
      
      // Process the file immediately after upload
      const jobId = response.data.job_id;
      await axios.post(`${API_URL}/process/${jobId}`, {
        remove_duplicates: true,
        fill_nulls: true,
        null_value: 0,
        normalize: false
      });

      // Navigate to dashboard after successful processing
      navigate('/', { replace: true });
      
    } catch (error) {
      console.error('Upload error:', error);
      setUploadStatus('error');
      setErrorMessage(error.response?.data?.error || 'Failed to upload file');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold text-gray-900">Upload CSV File</h1>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">CSV File Upload</h2>
          <p className="mt-1 text-sm text-gray-500">
            Upload a CSV file to preprocess and prepare it for the main system
          </p>
        </div>

        <div className="p-6">
          {file && uploadStatus !== 'uploading' ? (
            <div className="mb-6">
              <div className="flex items-start justify-between p-4 border border-gray-200 rounded-lg bg-gray-50">
                <div className="flex items-center space-x-3">
                  <FileSpreadsheet className="h-8 w-8 text-blue-500" />
                  <div>
                    <p className="text-sm font-medium text-gray-900">{file.name}</p>
                    <p className="text-xs text-gray-500">
                      {(file.size / 1024).toFixed(2)} KB • CSV
                    </p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={handleRemoveFile}
                  className="text-gray-400 hover:text-gray-500"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
            </div>
          ) : null}

          {uploadStatus === 'uploading' ? (
            <div className="mb-6">
              <div className="flex items-start p-4 border border-gray-200 rounded-lg bg-gray-50">
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-3">
                      <FileSpreadsheet className="h-8 w-8 text-blue-500" />
                      <div>
                        <p className="text-sm font-medium text-gray-900">{file?.name}</p>
                        <p className="text-xs text-gray-500">Uploading...</p>
                      </div>
                    </div>
                    <span className="text-sm font-medium text-blue-600">{uploadProgress}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300 ease-in-out"
                      style={{ width: `${uploadProgress}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            </div>
          ) : null}

          {uploadStatus === 'success' ? (
            <div className="mb-6 flex items-center p-4 border border-green-200 rounded-lg bg-green-50 text-green-800">
              <CheckCircle className="h-5 w-5 mr-2 text-green-500" />
              <span>File uploaded successfully!</span>
            </div>
          ) : null}

          {uploadStatus === 'error' ? (
            <div className="mb-6 flex items-center p-4 border border-red-200 rounded-lg bg-red-50 text-red-800">
              <AlertCircle className="h-5 w-5 mr-2 text-red-500" />
              <span>{errorMessage || 'An error occurred during upload'}</span>
            </div>
          ) : null}

          {!file || uploadStatus === 'error' ? (
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-lg p-10 text-center cursor-pointer transition-colors ${
                isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50'
              }`}
            >
              <input {...getInputProps()} />
              <FileSpreadsheet className="h-12 w-12 text-gray-400 mx-auto mb-3" />
              <p className="text-lg font-medium text-gray-900 mb-1">
                {isDragActive ? 'Drop the CSV file here' : 'Drag & drop a CSV file here'}
              </p>
              <p className="text-sm text-gray-500 mb-4">or click to browse files</p>
              <button
                type="button"
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                onClick={(e) => {
                  e.stopPropagation();
                  document.getElementById('fileInput')?.click();
                }}
              >
                <UploadIcon className="mr-2 h-4 w-4" />
                Browse Files
              </button>
              <input
                id="fileInput"
                type="file"
                accept=".csv"
                className="hidden"
                onChange={(e) => {
                  if (e.target.files && e.target.files[0]) {
                    onDrop([e.target.files[0]]);
                  }
                }}
              />
            </div>
          ) : null}

          {file && uploadStatus !== 'uploading' && uploadStatus !== 'success' ? (
            <div className="mt-6 text-right">
              <button
                onClick={handleUpload}
                disabled={uploading}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                {uploading ? (
                  <>
                    <span className="animate-spin mr-2">
                      <UploadIcon className="h-4 w-4" />
                    </span>
                    Uploading...
                  </>
                ) : (
                  <>
                    <UploadIcon className="mr-2 h-4 w-4" />
                    Upload File
                  </>
                )}
              </button>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
};

export default Upload;