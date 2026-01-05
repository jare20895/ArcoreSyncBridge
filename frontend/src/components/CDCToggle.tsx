import React, { useState } from 'react';
import { Zap, ZapOff } from 'lucide-react';
import { enableCDC, disableCDC } from '../services/api';

interface CDCToggleProps {
    syncDefId: string;
    cdcEnabled?: boolean;
    onToggle?: () => void;
}

export default function CDCToggle({ syncDefId, cdcEnabled = false, onToggle }: CDCToggleProps) {
    const [loading, setLoading] = useState(false);

    const handleToggle = async () => {
        setLoading(true);
        try {
            if (cdcEnabled) {
                await disableCDC(syncDefId);
                alert('CDC disabled successfully!');
            } else {
                await enableCDC(syncDefId);
                alert('CDC enabled successfully!\n\nChanges to the database will now be pushed to SharePoint in real-time.');
            }
            if (onToggle) onToggle();
        } catch (e: any) {
            console.error(e);
            // CDC endpoints may not exist yet (Epic 5)
            const errorMsg = e.response?.status === 404
                ? 'CDC feature is not yet available (coming in Epic 5)'
                : (e.response?.data?.detail || e.message);
            alert('Failed to toggle CDC: ' + errorMsg);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="bg-white dark:bg-dark-surface p-6 rounded border border-gray-200 dark:border-gray-700 shadow-sm">
            <div className="flex justify-between items-start">
                <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                        <Zap size={20} className="text-purple-600 dark:text-purple-400" />
                        <h3 className="text-lg font-bold text-light-text-primary dark:text-dark-text-primary">
                            Change Data Capture (CDC)
                        </h3>
                    </div>
                    <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary mb-4">
                        Enable real-time push sync from database to SharePoint. Changes are detected automatically
                        and pushed immediately without waiting for scheduled syncs.
                    </p>

                    {cdcEnabled && (
                        <div className="p-3 bg-purple-50 dark:bg-purple-900/20 rounded border border-purple-200 dark:border-purple-800 mb-4">
                            <div className="flex items-center space-x-2">
                                <div className="w-2 h-2 bg-purple-600 dark:bg-purple-400 rounded-full animate-pulse"></div>
                                <span className="text-sm font-medium text-purple-700 dark:text-purple-300">
                                    Real-time sync active
                                </span>
                            </div>
                            <p className="text-xs text-purple-600 dark:text-purple-400 mt-1">
                                Database changes are being monitored and pushed to SharePoint automatically
                            </p>
                        </div>
                    )}

                    <div className="space-y-2 text-sm text-light-text-secondary dark:text-dark-text-secondary">
                        <div className="flex items-center space-x-2">
                            <div className={`w-2 h-2 rounded-full ${cdcEnabled ? 'bg-green-500' : 'bg-gray-300 dark:bg-gray-600'}`}></div>
                            <span>Push database changes in real-time</span>
                        </div>
                        <div className="flex items-center space-x-2">
                            <div className={`w-2 h-2 rounded-full ${cdcEnabled ? 'bg-green-500' : 'bg-gray-300 dark:bg-gray-600'}`}></div>
                            <span>Low latency (typically &lt; 1 second)</span>
                        </div>
                        <div className="flex items-center space-x-2">
                            <div className={`w-2 h-2 rounded-full ${cdcEnabled ? 'bg-green-500' : 'bg-gray-300 dark:bg-gray-600'}`}></div>
                            <span>Uses PostgreSQL logical replication</span>
                        </div>
                    </div>
                </div>

                <div className="ml-6">
                    <button
                        onClick={handleToggle}
                        disabled={loading}
                        className={`relative inline-flex h-10 w-20 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 disabled:opacity-50 ${
                            cdcEnabled
                                ? 'bg-purple-600 dark:bg-purple-700'
                                : 'bg-gray-200 dark:bg-gray-700'
                        }`}
                        title={cdcEnabled ? 'Disable CDC' : 'Enable CDC'}
                    >
                        <span className="sr-only">Toggle CDC</span>
                        <span
                            className={`inline-block h-8 w-8 transform rounded-full bg-white shadow-lg transition-transform ${
                                cdcEnabled ? 'translate-x-11' : 'translate-x-1'
                            }`}
                        >
                            {cdcEnabled ? (
                                <Zap size={16} className="text-purple-600 m-auto mt-1.5" />
                            ) : (
                                <ZapOff size={16} className="text-gray-400 m-auto mt-1.5" />
                            )}
                        </span>
                    </button>
                    <div className="text-center mt-2">
                        <span className={`text-xs font-medium ${
                            cdcEnabled
                                ? 'text-purple-600 dark:text-purple-400'
                                : 'text-gray-500 dark:text-gray-400'
                        }`}>
                            {cdcEnabled ? 'Enabled' : 'Disabled'}
                        </span>
                    </div>
                </div>
            </div>

            {!cdcEnabled && (
                <div className="mt-4 p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded border border-yellow-200 dark:border-yellow-800">
                    <p className="text-xs text-yellow-800 dark:text-yellow-300">
                        <strong>Note:</strong> CDC requires a replication slot to be configured on the database instance.
                        Enabling CDC will start monitoring database changes immediately.
                    </p>
                </div>
            )}
        </div>
    );
}
