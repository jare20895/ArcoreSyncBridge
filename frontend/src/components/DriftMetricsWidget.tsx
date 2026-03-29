import React, { useEffect, useState } from 'react';
import { getDriftSummary, getDriftMetrics, triggerDriftReconciliation } from '../services/api';
import { RefreshCw, AlertTriangle, CheckCircle, HelpCircle, TrendingUp } from 'lucide-react';
import { useToast } from '@/components/ui/ToastProvider';

export default function DriftMetricsWidget() {
  const [summary, setSummary] = useState<any>(null);
  const [metrics, setMetrics] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [reconciling, setReconciling] = useState(false);
  const { showToast } = useToast();

  useEffect(() => {
    fetchDriftData();
    // Refresh every 15 minutes
    const interval = setInterval(fetchDriftData, 900000);
    return () => clearInterval(interval);
  }, []);

  const fetchDriftData = async () => {
    try {
      const [summaryData, metricsData] = await Promise.all([
        getDriftSummary(),
        getDriftMetrics()
      ]);
      setSummary(summaryData);
      setMetrics(metricsData);
    } catch (error) {
      console.error('Failed to fetch drift metrics:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleReconcile = async () => {
    setReconciling(true);
    try {
      await triggerDriftReconciliation();
      await fetchDriftData();
      showToast({
        title: 'Drift metrics refreshed',
        description: 'Reconciliation completed and the dashboard has been updated.',
        variant: 'success',
      });
    } catch (error) {
      console.error('Failed to reconcile drift:', error);
      showToast({
        title: 'Failed to reconcile drift metrics',
        description: 'The reconciliation request did not complete. Check the backend logs and try again.',
        variant: 'error',
      });
    } finally {
      setReconciling(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-white dark:bg-dark-surface rounded-lg border border-gray-200 dark:border-gray-800 shadow-sm p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mb-4"></div>
          <div className="h-20 bg-gray-200 dark:bg-gray-700 rounded"></div>
        </div>
      </div>
    );
  }

  const hasDrift = summary && summary.mismatched > 0;
  const totalDrift = summary?.total_drift_items || 0;

  return (
    <div className="bg-white dark:bg-dark-surface rounded-lg border border-gray-200 dark:border-gray-800 shadow-sm p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <TrendingUp className="text-purple-600 dark:text-purple-400" size={20} />
          <h3 className="text-lg font-bold font-secondary text-gray-900 dark:text-gray-100">
            Drift Metrics
          </h3>
        </div>
        <button
          onClick={handleReconcile}
          disabled={reconciling}
          className="flex items-center space-x-1 text-xs text-gray-600 dark:text-gray-400 hover:text-purple-600 dark:hover:text-purple-400 transition-colors disabled:opacity-50"
          title="Reconcile drift metrics"
        >
          <RefreshCw size={14} className={reconciling ? 'animate-spin' : ''} />
          <span>{reconciling ? 'Reconciling...' : 'Refresh'}</span>
        </button>
      </div>

      {/* Summary Stats */}
      {summary ? (
        <div className="space-y-4">
          {/* Status Overview */}
          <div className="grid grid-cols-3 gap-3">
            <div className="text-center p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
              <div className="flex justify-center mb-1">
                <CheckCircle className="text-green-600 dark:text-green-400" size={16} />
              </div>
              <p className="text-xl font-bold text-green-700 dark:text-green-300">
                {summary.matched}
              </p>
              <p className="text-xs text-green-600 dark:text-green-400">Matched</p>
            </div>

            <div className="text-center p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
              <div className="flex justify-center mb-1">
                <AlertTriangle className="text-red-600 dark:text-red-400" size={16} />
              </div>
              <p className="text-xl font-bold text-red-700 dark:text-red-300">
                {summary.mismatched}
              </p>
              <p className="text-xs text-red-600 dark:text-red-400">Drifted</p>
            </div>

            <div className="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <div className="flex justify-center mb-1">
                <HelpCircle className="text-gray-600 dark:text-gray-400" size={16} />
              </div>
              <p className="text-xl font-bold text-gray-700 dark:text-gray-300">
                {summary.unknown}
              </p>
              <p className="text-xs text-gray-600 dark:text-gray-400">Unknown</p>
            </div>
          </div>

          {/* Total Drift */}
          {hasDrift && (
            <div className="p-3 bg-orange-50 dark:bg-orange-900/20 rounded-lg border border-orange-200 dark:border-orange-700">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-orange-700 dark:text-orange-300">
                  Total Drift Items
                </span>
                <span className="text-lg font-bold font-mono text-orange-700 dark:text-orange-300">
                  {totalDrift.toLocaleString()}
                </span>
              </div>
            </div>
          )}

          {/* Top Drifted Syncs */}
          {metrics.length > 0 && (
            <div className="pt-3 border-t border-gray-200 dark:border-gray-700">
              <p className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase mb-2">
                Syncs with Drift
              </p>
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {metrics
                  .filter(m => m.reconcile_status === 'MISMATCH')
                  .slice(0, 5)
                  .map(metric => (
                    <div
                      key={metric.id}
                      className="flex items-center justify-between text-xs py-1.5 px-2 rounded bg-gray-50 dark:bg-gray-800"
                    >
                      <span className="font-medium text-gray-700 dark:text-gray-300 truncate flex-1">
                        {metric.sync_def_name}
                      </span>
                      <span className="text-red-600 dark:text-red-400 font-mono font-bold ml-2">
                        ±{metric.reconcile_delta}
                      </span>
                    </div>
                  ))}
                {metrics.filter(m => m.reconcile_status === 'MISMATCH').length === 0 && (
                  <p className="text-xs text-center text-green-600 dark:text-green-400 py-2">
                    ✓ All syncs in sync!
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Last Updated */}
          {summary.last_updated && (
            <p className="text-xs text-gray-500 dark:text-gray-400 text-center mt-2">
              Last updated:{' '}
              {new Date(summary.last_updated).toLocaleString('en-US', {
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
              })}
            </p>
          )}
        </div>
      ) : (
        <div className="text-center py-8">
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-3">
            No drift metrics available yet
          </p>
          <button
            onClick={handleReconcile}
            disabled={reconciling}
            className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white text-sm rounded-md transition-colors disabled:opacity-50"
          >
            {reconciling ? 'Calculating...' : 'Calculate Drift'}
          </button>
        </div>
      )}
    </div>
  );
}
