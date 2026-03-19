import React, { useState, useEffect, useCallback } from 'react';
import { getPublicationStatus, createPublication, dropPublication, getPublicationAvailableTables } from '../services/api';
import { RefreshCw, Plus, Trash2, CheckCircle, AlertTriangle, List as ListIcon } from 'lucide-react';

interface PublicationManagerProps {
  instanceId: string;
}

export const PublicationManager: React.FC<PublicationManagerProps> = ({ instanceId }) => {
  const [status, setStatus] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [processing, setProcessing] = useState(false);
  
  // Selection State
  const [mode, setMode] = useState<'ALL' | 'SELECT'>('ALL');
  const [availableTables, setAvailableTables] = useState<string[]>([]);
  const [selectedTables, setSelectedTables] = useState<string[]>([]);
  const [loadingTables, setLoadingTables] = useState(false);

  const loadStatus = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await getPublicationStatus(instanceId);
      setStatus(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load publication status');
    } finally {
      setLoading(false);
    }
  }, [instanceId]);

  useEffect(() => {
    loadStatus();
  }, [loadStatus]);

  const handleModeChange = (newMode: 'ALL' | 'SELECT') => {
      setMode(newMode);
      if (newMode === 'SELECT' && availableTables.length === 0) {
          loadTables();
      }
  };

  const loadTables = async () => {
      setLoadingTables(true);
      try {
          const tables = await getPublicationAvailableTables(instanceId);
          setAvailableTables(tables);
      } catch (e) {
          console.error(e);
          setError("Failed to load tables");
      } finally {
          setLoadingTables(false);
      }
  };

  const handleCreate = async () => {
    setProcessing(true);
    setError('');
    try {
      const isAll = mode === 'ALL';
      if (!isAll && selectedTables.length === 0) {
          setError("Please select at least one table.");
          setProcessing(false);
          return;
      }
      
      await createPublication(instanceId, "arcore_cdc_pub", isAll, selectedTables);
      await loadStatus();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create publication');
    } finally {
      setProcessing(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm("Are you sure you want to drop the publication? CDC will stop working.")) return;
    setProcessing(true);
    setError('');
    try {
      await dropPublication(instanceId);
      await loadStatus();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to drop publication');
    } finally {
      setProcessing(false);
    }
  };

  if (loading && !status) {
    return <div className="text-sm text-gray-500">Loading publication status...</div>;
  }

  return (
    <div className="space-y-4">
      {error && (
        <div className="bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400 p-3 rounded text-sm flex items-start">
          <AlertTriangle size={16} className="mr-2 mt-0.5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {status?.exists ? (
        <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-md p-4">
          <div className="flex justify-between items-start">
            <div className="flex items-center">
              <CheckCircle size={20} className="text-green-600 dark:text-green-400 mr-2" />
              <div>
                <h4 className="text-sm font-bold text-green-800 dark:text-green-300">Publication Active</h4>
                <p className="text-xs text-green-700 dark:text-green-400 mt-1">
                  Name: <span className="font-mono">arcore_cdc_pub</span>
                </p>
                <p className="text-xs text-green-700 dark:text-green-400">
                  Scope: {status.all_tables ? "FOR ALL TABLES" : `Selected Tables (${status.tables.length})`}
                </p>
                {!status.all_tables && (
                    <div className="mt-2 text-xs text-green-800 dark:text-green-200 font-mono">
                        {status.tables.join(', ')}
                    </div>
                )}
              </div>
            </div>
            <button
              onClick={handleDelete}
              disabled={processing}
              className="text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-300 text-xs flex items-center"
            >
              <Trash2 size={14} className="mr-1" />
              Drop
            </button>
          </div>
        </div>
      ) : (
        <div className="bg-white dark:bg-dark-surface border border-gray-200 dark:border-gray-700 rounded-md p-6">
          <h4 className="text-base font-medium text-light-text-primary dark:text-dark-text-primary mb-2 text-center">Publication Missing</h4>
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-6 text-center">
            The source database requires a publication named <code className="bg-gray-100 dark:bg-gray-800 px-1 py-0.5 rounded text-xs">arcore_cdc_pub</code> to stream changes.
          </p>
          
          <div className="space-y-4">
              <div className="flex justify-center space-x-4">
                  <button
                    onClick={() => handleModeChange('ALL')}
                    className={`px-4 py-2 rounded text-sm font-medium border ${mode === 'ALL' ? 'bg-blue-50 border-blue-200 text-blue-700 dark:bg-blue-900/30 dark:border-blue-700 dark:text-blue-300' : 'bg-white border-gray-200 text-gray-700 dark:bg-dark-surface dark:border-gray-600 dark:text-gray-300'}`}
                  >
                      All Tables (Recommended)
                  </button>
                  <button
                    onClick={() => handleModeChange('SELECT')}
                    className={`px-4 py-2 rounded text-sm font-medium border ${mode === 'SELECT' ? 'bg-blue-50 border-blue-200 text-blue-700 dark:bg-blue-900/30 dark:border-blue-700 dark:text-blue-300' : 'bg-white border-gray-200 text-gray-700 dark:bg-dark-surface dark:border-gray-600 dark:text-gray-300'}`}
                  >
                      Select Tables
                  </button>
              </div>

              {mode === 'SELECT' && (
                  <div className="border border-gray-200 dark:border-gray-700 rounded-md max-h-60 overflow-y-auto p-2 bg-gray-50 dark:bg-gray-800">
                      {loadingTables ? (
                          <div className="text-xs text-center p-4">Loading tables...</div>
                      ) : (
                          availableTables.map(t => (
                              <label key={t} className="flex items-center space-x-2 p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded cursor-pointer">
                                  <input 
                                    type="checkbox" 
                                    checked={selectedTables.includes(t)}
                                    onChange={(e) => {
                                        if (e.target.checked) setSelectedTables([...selectedTables, t]);
                                        else setSelectedTables(selectedTables.filter(x => x !== t));
                                    }}
                                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                  />
                                  <span className="text-sm font-mono text-gray-700 dark:text-gray-300">{t}</span>
                              </label>
                          ))
                      )}
                  </div>
              )}

              <div className="flex justify-center mt-4">
                <button
                    onClick={handleCreate}
                    disabled={processing || (mode === 'SELECT' && selectedTables.length === 0)}
                    className="inline-flex items-center px-4 py-2 bg-light-primary dark:bg-dark-primary text-white rounded hover:opacity-90 disabled:opacity-50 text-sm font-medium"
                >
                    {processing ? (
                    <RefreshCw size={16} className="animate-spin mr-2" />
                    ) : (
                    <Plus size={16} className="mr-2" />
                    )}
                    Create Publication
                </button>
              </div>
          </div>
        </div>
      )}
    </div>
  );
};
