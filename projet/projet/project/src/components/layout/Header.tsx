import React from 'react';
import { Link } from 'react-router-dom';
import { Database, FileSpreadsheet, Settings, HelpCircle } from 'lucide-react';

const Header: React.FC = () => {
  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
      <div className="flex items-center justify-between h-16 px-6">
        <div className="flex items-center space-x-2">
          <Link to="/" className="flex items-center space-x-2">
            <Database className="h-6 w-6 text-blue-600" />
            <span className="text-xl font-semibold text-gray-900">GoodData</span>
          </Link>
        </div>
        
        <div className="flex items-center space-x-4">
          <Link 
            to="/upload" 
            className="flex items-center space-x-1 px-4 py-2 rounded-md bg-blue-600 text-white hover:bg-blue-700 transition-colors"
          >
            <FileSpreadsheet className="h-4 w-4" />
            <span>Upload CSV</span>
          </Link>
          
          <Link to="/settings" className="text-gray-600 hover:text-gray-900 transition-colors">
            <Settings className="h-5 w-5" />
          </Link>
          
          <Link to="/help" className="text-gray-600 hover:text-gray-900 transition-colors">
            <HelpCircle className="h-5 w-5" />
          </Link>
        </div>
      </div>
    </header>
  );
};

export default Header;