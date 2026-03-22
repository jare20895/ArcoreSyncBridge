import React, { useState } from 'react';
import { getSystemSnapshot } from '../services/api';
import { Activity, Server, HardDrive, Cpu, TrendingUp } from 'lucide-react';
import { useToast } from './ui/ToastProvider';

interface ContainerMetric {
  name: string;
  avg_cpu_percent: number;
  avg_memory_percent: number;
  avg_memory_mb: number;
}

interface SnapshotData {
  duration_seconds: number;
  samples_collected: number;
  timestamp: string;
  system: {
    cpu_percent: number;
    memory_percent: number;
    memory_total_gb: number;
    memory_available_gb: number;
    cpu_count: number;
  };
  syncbridge_containers: ContainerMetric[];
  all_containers_count: number;
}

export default function SystemSnapshot() {
  const { showToast } = useToast();
  const [loading, setLoading] = useState(false);
  const [snapshot, setSnapshot] = useState<SnapshotData | null>(null);
  const [duration, setDuration] = useState(15);
  const [progress, setProgress] = useState(0);

  const handleSnapshot = async () => {
    setLoading(true);
    setProgress(0);
    setSnapshot(null);

    // Start progress animation
    const progressInterval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          clearInterval(progressInterval);
          return 100;
        }
        return prev + (100 / duration);
      });
    }, 1000);

    try {
      const data = await getSystemSnapshot(duration);
      setSnapshot(data);
    } catch (err) {
      console.error('Error collecting snapshot:', err);
      showToast({
        title: 'Snapshot failed',
        description: 'Failed to collect system snapshot',
        variant: 'error',
      });
    } finally {
      clearInterval(progressInterval);
      setLoading(false);
      setProgress(0);
    }
  };

  return (
    <div className="bg-white dark:bg-dark-surface rounded-lg border border-gray-200 dark:border-gray-800 shadow-sm">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-800">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-bold font-secondary text-light-text-primary dark:text-dark-text-primary flex items-center">
              <Activity className="mr-2" size={20} />
              System Performance Snapshot
            </h3>
            <p className="text-xs text-gray-500 mt-1">
              Analyze CPU and memory usage over time
            </p>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <label className="text-sm text-gray-600 dark:text-gray-400">Duration:</label>
              <select
                value={duration}
                onChange={(e) => setDuration(Number(e.target.value))}
                disabled={loading}
                className="px-3 py-1.5 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-sm disabled:opacity-50"
              >
                <option value={3}>3s</option>
                <option value={5}>5s</option>
                <option value={10}>10s</option>
                <option value={15}>15s</option>
                <option value={30}>30s</option>
                <option value={60}>60s</option>
              </select>
            </div>
            <button
              onClick={handleSnapshot}
              disabled={loading}
              className="px-4 py-2 bg-light-primary dark:bg-dark-primary text-white rounded hover:opacity-90 disabled:opacity-50 text-sm font-medium flex items-center"
            >
              {loading ? (
                <>
                  <Activity className="animate-spin mr-2" size={16} />
                  Analyzing... {Math.round(progress)}%
                </>
              ) : (
                <>
                  <TrendingUp className="mr-2" size={16} />
                  Run Snapshot
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      {loading && (
        <div className="px-6 py-3 bg-blue-50 dark:bg-blue-900/20 border-b border-blue-200 dark:border-blue-800">
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-1000"
              style={{ width: `${progress}%` }}
            />
          </div>
          <p className="text-xs text-gray-600 dark:text-gray-400 mt-1 text-center">
            Collecting {duration} samples...
          </p>
        </div>
      )}

      {/* Results */}
      {snapshot && (
        <div className="p-6 space-y-6">
          {/* System Metrics */}
          <div>
            <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center">
              <Server className="mr-2" size={16} />
              System Metrics
            </h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded border border-gray-200 dark:border-gray-700">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-gray-500">Average CPU</span>
                  <Cpu size={14} className="text-blue-600" />
                </div>
                <p className={`text-2xl font-bold font-mono ${
                  snapshot.system.cpu_percent > 80 ? 'text-red-600' :
                  snapshot.system.cpu_percent > 50 ? 'text-yellow-600' :
                  'text-green-600'
                }`}>
                  {snapshot.system.cpu_percent.toFixed(1)}%
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  {snapshot.system.cpu_count} cores
                </p>
              </div>

              <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded border border-gray-200 dark:border-gray-700">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-gray-500">Average Memory</span>
                  <HardDrive size={14} className="text-purple-600" />
                </div>
                <p className={`text-2xl font-bold font-mono ${
                  snapshot.system.memory_percent > 80 ? 'text-red-600' :
                  snapshot.system.memory_percent > 50 ? 'text-yellow-600' :
                  'text-green-600'
                }`}>
                  {snapshot.system.memory_percent.toFixed(1)}%
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  {snapshot.system.memory_total_gb.toFixed(1)} GB total
                </p>
              </div>

              <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded border border-gray-200 dark:border-gray-700">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-gray-500">Available Memory</span>
                  <HardDrive size={14} className="text-green-600" />
                </div>
                <p className="text-2xl font-bold font-mono text-light-text-primary dark:text-dark-text-primary">
                  {snapshot.system.memory_available_gb.toFixed(1)} GB
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  {((snapshot.system.memory_available_gb / snapshot.system.memory_total_gb) * 100).toFixed(0)}% free
                </p>
              </div>

              <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded border border-gray-200 dark:border-gray-700">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-gray-500">Samples</span>
                  <Activity size={14} className="text-gray-600" />
                </div>
                <p className="text-2xl font-bold font-mono text-light-text-primary dark:text-dark-text-primary">
                  {snapshot.samples_collected}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  over {snapshot.duration_seconds}s
                </p>
              </div>
            </div>
          </div>

          {/* Container Metrics */}
          {snapshot.syncbridge_containers.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center justify-between">
                <span className="flex items-center">
                  <Server className="mr-2" size={16} />
                  SyncBridge Containers ({snapshot.syncbridge_containers.length})
                </span>
                <span className="text-xs font-normal text-gray-500">
                  {snapshot.all_containers_count} total containers running
                </span>
              </h4>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-800">
                  <thead className="bg-gray-50 dark:bg-gray-900">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Container</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Avg CPU</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Avg Memory</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Memory Usage</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white dark:bg-dark-surface divide-y divide-gray-200 dark:divide-gray-800">
                    {snapshot.syncbridge_containers.map((container, idx) => (
                      <tr key={idx}>
                        <td className="px-4 py-3 whitespace-nowrap text-sm font-mono">
                          {container.name
                            .replace('arcoresyncbridge-', '')
                            .replace('arcore-', '')
                            .replace(/^src-/, '')
                            .replace(/-1$/, '')}
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap">
                          <span className={`text-sm font-mono font-semibold ${
                            container.avg_cpu_percent > 80 ? 'text-red-600 dark:text-red-400' :
                            container.avg_cpu_percent > 50 ? 'text-yellow-600 dark:text-yellow-400' :
                            'text-green-600 dark:text-green-400'
                          }`}>
                            {container.avg_cpu_percent.toFixed(2)}%
                          </span>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap">
                          <span className={`text-sm font-mono font-semibold ${
                            container.avg_memory_percent > 80 ? 'text-red-600 dark:text-red-400' :
                            container.avg_memory_percent > 50 ? 'text-yellow-600 dark:text-yellow-400' :
                            'text-green-600 dark:text-green-400'
                          }`}>
                            {container.avg_memory_percent.toFixed(2)}%
                          </span>
                        </td>
                        <td className="px-4 py-3 whitespace-nowrap text-sm font-mono text-gray-600 dark:text-gray-400">
                          {container.avg_memory_mb.toFixed(1)} MB
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Timestamp */}
          <div className="text-xs text-gray-500 text-right">
            Snapshot taken at: {new Date(snapshot.timestamp).toLocaleString()}
          </div>
        </div>
      )}

      {/* Empty State */}
      {!snapshot && !loading && (
        <div className="p-12 text-center text-gray-500">
          <Activity size={48} className="mx-auto mb-3 opacity-50" />
          <p className="text-sm">Click &quot;Run Snapshot&quot; to analyze system performance</p>
        </div>
      )}
    </div>
  );
}
