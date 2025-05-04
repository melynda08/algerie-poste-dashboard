import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Upload, 
  Settings, 
  HelpCircle
} from 'lucide-react';

const Sidebar: React.FC = () => {
  const navItems = [
    { path: '/', icon: <LayoutDashboard size={20} />, label: 'Dashboard' },
    { path: '/upload', icon: <Upload size={20} />, label: 'Upload CSV' },
    { path: '/settings', icon: <Settings size={20} />, label: 'Settings' },
  ];

  return (
    <aside className="w-56 bg-white border-r border-gray-200 overflow-y-auto hidden md:block">
      <nav className="mt-6 px-3">
        <ul className="space-y-1">
          {navItems.map((item) => (
            <li key={item.path}>
              <NavLink
                to={item.path}
                className={({ isActive }) => 
                  `flex items-center px-3 py-2 rounded-md ${
                    isActive 
                      ? 'bg-blue-50 text-blue-700' 
                      : 'text-gray-700 hover:bg-gray-100'
                  } transition-colors`
                }
              >
                <span className="mr-3">{item.icon}</span>
                <span>{item.label}</span>
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      <div className="px-3 mt-10">
        <div className="p-4 bg-blue-50 rounded-lg">
          <h4 className="text-sm font-medium text-blue-700 mb-2">Need Help?</h4>
          <p className="text-xs text-blue-600 mb-3">
            View our documentation to learn more about CSV preprocessing.
          </p>
          <a 
            href="#" 
            className="flex items-center text-xs font-medium text-blue-700 hover:text-blue-800"
          >
            <HelpCircle size={14} className="mr-1" />
            View Documentation
          </a>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;