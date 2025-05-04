import React, { useState } from 'react';
import { Save, RefreshCw, Settings as SettingsIcon } from 'lucide-react';

interface ProcessingSettings {
  defaultRemoveDuplicates: boolean;
  defaultFillNulls: boolean;
  defaultNullValue: number;
  defaultNormalize: boolean;
}

const Settings: React.FC = () => {
  const [processingSettings, setProcessingSettings] = useState<ProcessingSettings>({
    defaultRemoveDuplicates: true,
    defaultFillNulls: true,
    defaultNullValue: 0,
    defaultNormalize: false
  });

  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const handleSaveSettings = () => {
    setSaving(true);
    
    // Simulate saving settings
    setTimeout(() => {
      setSaving(false);
      setSaved(true);
      
      // Hide success message after 3 seconds
      setTimeout(() => {
        setSaved(false);
      }, 3000);
    }, 1000);
  };

  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold text-gray-900">Settings</h1>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden mb-6">
        <div className="px-6 py-4 border-b border-gray-200 flex items-center">
          <SettingsIcon className="h-5 w-5 text-gray-500 mr-2" />
          <h2 className="text-lg font-medium text-gray-900">Default Processing Settings</h2>
        </div>

        <div className="p-6 space-y-6">
          <div>
            <h3 className="text-sm font-medium text-gray-900 mb-4">Default CSV Processing Options</h3>
            
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-medium text-gray-700">Remove Duplicates</h4>
                  <p className="text-xs text-gray-500">
                    Automatically remove duplicate rows
                  </p>
                </div>
                <div className="relative inline-block w-10 align-middle select-none">
                  <input
                    type="checkbox"
                    id="default-remove-duplicates"
                    checked={processingSettings.defaultRemoveDuplicates}
                    onChange={() => setProcessingSettings(prev => ({
                      ...prev,
                      defaultRemoveDuplicates: !prev.defaultRemoveDuplicates
                    }))}
                    className="sr-only peer"
                  />
                  <label
                    htmlFor="default-remove-duplicates"
                    className="block overflow-hidden h-6 rounded-full bg-gray-200 cursor-pointer peer-checked:bg-blue-600"
                  >
                    <span className="absolute inset-y-0 left-0 w-6 h-6 bg-white rounded-full shadow transform transition-transform duration-300 ease-in-out peer-checked:translate-x-4"></span>
                  </label>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-medium text-gray-700">Fill Null Values</h4>
                  <p className="text-xs text-gray-500">
                    Replace null values with a default value
                  </p>
                </div>
                <div className="relative inline-block w-10 align-middle select-none">
                  <input
                    type="checkbox"
                    id="default-fill-nulls"
                    checked={processingSettings.defaultFillNulls}
                    onChange={() => setProcessingSettings(prev => ({
                      ...prev,
                      defaultFillNulls: !prev.defaultFillNulls
                    }))}
                    className="sr-only peer"
                  />
                  <label
                    htmlFor="default-fill-nulls"
                    className="block overflow-hidden h-6 rounded-full bg-gray-200 cursor-pointer peer-checked:bg-blue-600"
                  >
                    <span className="absolute inset-y-0 left-0 w-6 h-6 bg-white rounded-full shadow transform transition-transform duration-300 ease-in-out peer-checked:translate-x-4"></span>
                  </label>
                </div>
              </div>

              {processingSettings.defaultFillNulls && (
                <div className="pl-6 border-l-2 border-gray-100">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Default Value for Nulls</h4>
                  <input
                    type="number"
                    value={processingSettings.defaultNullValue}
                    onChange={(e) => setProcessingSettings(prev => ({
                      ...prev,
                      defaultNullValue: Number(e.target.value)
                    }))}
                    className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  />
                </div>
              )}

              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-medium text-gray-700">Normalize Data</h4>
                  <p className="text-xs text-gray-500">
                    Scale numeric columns to a 0-1 range
                  </p>
                </div>
                <div className="relative inline-block w-10 align-middle select-none">
                  <input
                    type="checkbox"
                    id="default-normalize"
                    checked={processingSettings.defaultNormalize}
                    onChange={() => setProcessingSettings(prev => ({
                      ...prev,
                      defaultNormalize: !prev.defaultNormalize
                    }))}
                    className="sr-only peer"
                  />
                  <label
                    htmlFor="default-normalize"
                    className="block overflow-hidden h-6 rounded-full bg-gray-200 cursor-pointer peer-checked:bg-blue-600"
                  >
                    <span className="absolute inset-y-0 left-0 w-6 h-6 bg-white rounded-full shadow transform transition-transform duration-300 ease-in-out peer-checked:translate-x-4"></span>
                  </label>
                </div>
              </div>
            </div>
          </div>
          
          {saved && (
            <div className="p-3 bg-green-50 rounded-md text-green-800 text-sm flex items-center">
              <CheckCircle className="h-4 w-4 mr-2" />
              Settings saved successfully
            </div>
          )}

          <div className="flex justify-end">
            <button
              onClick={handleSaveSettings}
              disabled={saving}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              {saving ? (
                <>
                  <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="mr-2 h-4 w-4" />
                  Save Settings
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">About Data Preprocessing</h2>
        </div>
        <div className="p-6 space-y-4">
          <div>
            <h3 className="text-sm font-medium text-gray-900">Preprocessing Methods</h3>
            <p className="mt-1 text-sm text-gray-500">
              Our system supports various preprocessing methods to prepare your data for analysis and machine learning tasks.
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 gap-4">
            <div className="p-4 bg-blue-50 rounded-lg">
              <h4 className="text-sm font-semibold text-blue-700 mb-2">Remove Duplicates</h4>
              <p className="text-xs text-blue-600">
                Identifies and removes duplicate rows based on exact matches across all columns. 
                This helps in creating a clean dataset without redundant information.
              </p>
            </div>
            
            <div className="p-4 bg-blue-50 rounded-lg">
              <h4 className="text-sm font-semibold text-blue-700 mb-2">Fill Null Values</h4>
              <p className="text-xs text-blue-600">
                Replaces missing values (NaN, NULL, empty cells) with a specified default value. 
                This prevents errors in analysis and model training due to missing data.
              </p>
            </div>
            
            <div className="p-4 bg-blue-50 rounded-lg">
              <h4 className="text-sm font-semibold text-blue-700 mb-2">Normalize Data</h4>
              <p className="text-xs text-blue-600">
                Scales numeric columns to a range between 0 and 1. This is useful for 
                machine learning algorithms that are sensitive to the scale of input features.
              </p>
            </div>
            
            <div className="p-4 bg-blue-50 rounded-lg">
              <h4 className="text-sm font-semibold text-blue-700 mb-2">Custom Processing</h4>
              <p className="text-xs text-blue-600">
                For advanced needs, we can implement custom preprocessing steps. 
                Contact us to discuss your specific requirements.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;