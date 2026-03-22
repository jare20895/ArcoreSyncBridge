import React, { useCallback, useEffect, useState } from 'react';
import { getSyncRunsPage, getSyncDefinitions } from '../../services/api';
import { Clock, CheckCircle, XCircle, AlertCircle, Play, ArrowRight, RefreshCw } from 'lucide-react';
import Link from 'next/link';

const PAGE_SIZE = 20;

export default function RunsPage() {
  const [runs, setRuns] = useState<any[]>([]);
  const [meta, setMeta] = useState<{ total?: number; offset?: number }>({});
  const [syncDefs, setSyncDefs] = useState<{ [key: string]: any }>({});
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all'); // all, completed, failed, running
  const [runTypeFilter, setRunTypeFilter] = useState<string>('all');
  const [page, setPage] = useState(0);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [runsResponse, defsData] = await Promise.all([
        getSyncRunsPage({
          offset: page * PAGE_SIZE,
          limit: PAGE_SIZE,
          status: filter === 'all' ? undefined : filter.toUpperCase(),
          run_type: runTypeFilter === 'all' ? undefined : runTypeFilter,
        }),
        getSyncDefinitions()
      ]);

      setRuns(runsResponse.data);
      setMeta(runsResponse.meta ?? {});

      // Map sync definitions by ID for quick lookup
      const defsMap: { [key: string]: any } = {};
      defsData.forEach((def: any) => {
        defsMap[def.id] = def;
      });
      setSyncDefs(defsMap);
    } catch (err) {
      console.error('Failed to load runs:', err);
    } finally {
      setLoading(false);
    }
  }, [filter, page, runTypeFilter]);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return <CheckCircle size={20} className="text-green-500" />;
      case 'FAILED':
        return <XCircle size={20} className="text-red-500" />;
      case 'RUNNING':
        return <RefreshCw size={20} className="text-blue-500 animate-spin" />;
      default:
        return <AlertCircle size={20} className="text-gray-500" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const baseClasses = "px-2 py-1 text-xs font-medium rounded";
    switch (status) {
      case 'COMPLETED':
        return <span className={`${baseClasses} bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300`}>Completed</span>;
      case 'FAILED':
        return <span className={`${baseClasses} bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300`}>Failed</span>;
      case 'RUNNING':
        return <span className={`${baseClasses} bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300`}>Running</span>;
      default:
        return <span className={`${baseClasses} bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300`}>Unknown</span>;
    }
  };

  const getRunTypeIcon = (runType: string) => {
    switch (runType) {
      case 'PUSH':
        return <ArrowRight size={16} className="text-blue-500" />;
      case 'INGRESS':
        return <ArrowRight size={16} className="text-purple-500 rotate-180" />;
      case 'CDC':
        return <RefreshCw size={16} className="text-green-500" />;
      default:
        return <Play size={16} className="text-gray-500" />;
    }
  };

  const formatDuration = (start: string, end: string | null) => {
    if (!end) return 'In progress...';
    const startTime = new Date(start).getTime();
    const endTime = new Date(end).getTime();
    const durationMs = endTime - startTime;

    if (durationMs < 1000) return `${durationMs}ms`;
    if (durationMs < 60000) return `${(durationMs / 1000).toFixed(1)}s`;
    return `${Math.floor(durationMs / 60000)}m ${Math.floor((durationMs % 60000) / 1000)}s`;
  };

  const formatDateTime = (dateStr: string) => {
    const date = new Date(dateStr);
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    }).format(date);
  };

  const hasPrevious = page > 0;
  const hasNext = (meta.offset ?? 0) + runs.length < (meta.total ?? runs.length);

  return (
    <div className="min-h-screen bg-light-background dark:bg-dark-background">
      <header className="bg-white dark:bg-dark-surface border-b border-gray-200 dark:border-gray-800 py-6 px-8">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-light-text-primary dark:text-dark-text-primary">
              Sync Run History
            </h1>
            <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary mt-1">
              View all sync executions and their results
            </p>
          </div>
          <button
            onClick={() => void loadData()}
            className="flex items-center space-x-2 px-4 py-2 bg-light-primary dark:bg-dark-primary text-white rounded shadow-sm hover:bg-opacity-90"
          >
            <RefreshCw size={16} />
            <span>Refresh</span>
          </button>
        </div>

        {/* Filter Tabs */}
        <div className="mt-4 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex flex-wrap gap-4">
            {['all', 'completed', 'failed', 'running'].map((f) => (
              <button
                key={f}
                onClick={() => {
                  setPage(0);
                  setFilter(f);
                }}
                className={`px-4 py-2 text-sm font-medium rounded transition ${
                  filter === f
                    ? 'bg-light-primary dark:bg-dark-primary text-white'
                    : 'text-light-text-secondary dark:text-dark-text-secondary hover:bg-gray-100 dark:hover:bg-gray-800'
                }`}
              >
                {f.charAt(0).toUpperCase() + f.slice(1)}
              </button>
            ))}
          </div>
          <select
            value={runTypeFilter}
            onChange={(event) => {
              setPage(0);
              setRunTypeFilter(event.target.value);
            }}
            className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-light-text-primary dark:border-gray-700 dark:bg-gray-900 dark:text-dark-text-primary"
          >
            <option value="all">All run types</option>
            <option value="PUSH">PUSH</option>
            <option value="INGRESS">INGRESS</option>
            <option value="CDC">CDC</option>
          </select>
        </div>
      </header>

      <main className="p-8">
        {loading ? (
          <div className="text-center py-12">
            <RefreshCw size={32} className="animate-spin mx-auto text-light-primary dark:text-dark-primary" />
            <p className="mt-4 text-light-text-secondary dark:text-dark-text-secondary">Loading run history...</p>
          </div>
        ) : runs.length === 0 ? (
          <div className="bg-white dark:bg-dark-surface rounded border border-gray-200 dark:border-gray-700 p-12 text-center">
            <Clock size={48} className="mx-auto text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-light-text-primary dark:text-dark-text-primary mb-2">
              No runs found
            </h3>
            <p className="text-light-text-secondary dark:text-dark-text-secondary">
              {filter === 'all' ? 'No sync runs have been executed yet.' : `No ${filter} runs found.`}
            </p>
          </div>
        ) : (
          <div className="bg-white dark:bg-dark-surface rounded border border-gray-200 dark:border-gray-700 overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-900">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Sync Definition
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Start Time
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Duration
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Items
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Error
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {runs.map((run) => {
                  const syncDef = syncDefs[run.sync_def_id];
                  return (
                    <tr key={run.id} className="hover:bg-gray-50 dark:hover:bg-gray-800 transition">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center space-x-2">
                          {getStatusIcon(run.status)}
                          {getStatusBadge(run.status)}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        {syncDef ? (
                          <Link
                            href={`/sync-definitions/${run.sync_def_id}`}
                            className="text-light-primary dark:text-dark-primary hover:underline font-medium"
                          >
                            {syncDef.name}
                          </Link>
                        ) : (
                          <span className="text-gray-500">{run.sync_def_id}</span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div
                          className="flex items-center space-x-2"
                          title={
                            run.run_type === 'PUSH'
                              ? 'Push (DB to SharePoint)'
                              : run.run_type === 'INGRESS'
                              ? 'Pull (SharePoint to DB)'
                              : run.run_type === 'CDC'
                              ? 'CDC (Real-time)'
                              : run.run_type
                          }
                        >
                          {getRunTypeIcon(run.run_type)}
                          <span className="text-sm text-light-text-primary dark:text-dark-text-primary">
                            {run.run_type}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-light-text-secondary dark:text-dark-text-secondary">
                        {formatDateTime(run.start_time)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-light-text-secondary dark:text-dark-text-secondary">
                        {formatDuration(run.start_time, run.end_time)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm">
                          <span className="text-green-600 dark:text-green-400 font-medium">
                            {run.items_processed - run.items_failed}
                          </span>
                          <span className="text-gray-500 mx-1">/</span>
                          <span className="text-gray-600 dark:text-gray-400">
                            {run.items_processed}
                          </span>
                          {run.items_failed > 0 && (
                            <>
                              <span className="text-gray-500 mx-1">·</span>
                              <span className="text-red-600 dark:text-red-400 font-medium">
                                {run.items_failed} failed
                              </span>
                            </>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        {run.error_message ? (
                          <span className="text-xs text-red-600 dark:text-red-400 font-mono">
                            {run.error_message.length > 50
                              ? run.error_message.substring(0, 50) + '...'
                              : run.error_message}
                          </span>
                        ) : (
                          <span className="text-xs text-gray-400">-</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            <div className="flex items-center justify-between border-t border-gray-200 px-6 py-4 text-sm dark:border-gray-700">
              <div className="text-light-text-secondary dark:text-dark-text-secondary">
                Showing {(meta.offset ?? 0) + (runs.length > 0 ? 1 : 0)}-{(meta.offset ?? 0) + runs.length} of {meta.total ?? runs.length}
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage((current) => Math.max(0, current - 1))}
                  disabled={!hasPrevious}
                  className="rounded-lg border border-gray-300 px-3 py-2 text-sm text-light-text-primary transition hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-700 dark:text-dark-text-primary dark:hover:bg-gray-900"
                >
                  Previous
                </button>
                <button
                  onClick={() => setPage((current) => current + 1)}
                  disabled={!hasNext}
                  className="rounded-lg border border-gray-300 px-3 py-2 text-sm text-light-text-primary transition hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-700 dark:text-dark-text-primary dark:hover:bg-gray-900"
                >
                  Next
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
