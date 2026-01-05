import React, { useState, useEffect } from 'react';
import { getPublicationStatus, createPublication, dropPublication } from '../services/api';
import { RefreshCw, Plus, Trash2, CheckCircle, AlertTriangle } from 'lucide-react';

interface PublicationManagerProps {
  instanceId: string;
}

export const PublicationManager: React.FC<PublicationManagerProps> = ({ instanceId }) => {
  const [status, setStatus] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [processing, setProcessing] = useState(false);

  useEffect(() => {
    loadStatus();
  }, [instanceId]);

  const loadStatus = async () => {
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
  };

  const handleCreate = async () => {
    setProcessing(true);
    setError('');
    try {
      await createPublication(instanceId);
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
        <div className="bg-white dark:bg-dark-surface border border-gray-200 dark:border-gray-700 rounded-md p-6 text-center">
          <h4 className="text-base font-medium text-light-text-primary dark:text-dark-text-primary mb-2">Publication Missing</h4>
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
            The source database requires a publication named <code className="bg-gray-100 dark:bg-gray-800 px-1 py-0.5 rounded text-xs">arcore_cdc_pub</code> to stream changes.
          </p>
          <button
            onClick={handleCreate}
            disabled={processing}
            className="inline-flex items-center px-4 py-2 bg-light-primary dark:bg-dark-primary text-white rounded hover:opacity-90 disabled:opacity-50 text-sm font-medium"
          >
            {processing ? (
              <RefreshCw size={16} className="animate-spin mr-2" />
            ) : (
              <Plus size={16} className="mr-2" />
            )}
            Create Publication (FOR ALL TABLES)
          </button>
        </div>
      )}
    </div>
  );
};
