import React, { useEffect, useState } from 'react';
import { getCdcHealth } from '../services/api';
import { Activity, AlertTriangle, CheckCircle, XCircle, Database, HardDrive, Users } from 'lucide-react';

interface SlotData {
  slot_name: string;
  slot_type: string;
  database: string;
  instance_id?: string;
  instance_label?: string;
  active: boolean;
  restart_lsn: string | null;
  confirmed_flush_lsn: string | null;
  lag_bytes: number | null;
  lag_mb: number | null;
  flush_lag_bytes: number | null;
  flush_lag_mb: number | null;
}

interface CdcHealthData {
  status: 'healthy' | 'warning' | 'critical';
  issues: string[];
  timestamp: string;
  wal: {
    current_lsn: string;
    position_bytes: number;
    position_mb: number;
    directory_size: string;
    directory_size_bytes: number;
  };
  slots: SlotData[];
  connections: {
    total: number;
    active: number;
    idle: number;
    waiting: number;
  };
}

export default function CdcHealthWidget() {
  const [health, setHealth] = useState<CdcHealthData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHealth = async () => {
    try {
      setLoading(true);
      const data = await getCdcHealth();
      setHealth(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch CDC health');
      console.error('Error fetching CDC health:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    // Refresh every 30 seconds
    const interval = setInterval(fetchHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading && !health) {
    return (
      <div className="bg-white dark:bg-dark-surface rounded-lg border border-gray-200 dark:border-gray-800 shadow-sm p-6">
        <div className="flex items-center space-x-2">
          <Activity className="animate-spin" size={20} />
          <span className="text-sm text-gray-500">Loading CDC health...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white dark:bg-dark-surface rounded-lg border border-red-200 dark:border-red-800 shadow-sm p-6">
        <div className="flex items-center space-x-2 text-red-600 dark:text-red-400">
          <XCircle size={20} />
          <span className="text-sm font-medium">Error: {error}</span>
        </div>
      </div>
    );
  }

  if (!health) return null;

  const statusConfig = {
    healthy: {
      icon: CheckCircle,
      color: 'text-green-600 dark:text-green-400',
      bgColor: 'bg-green-100 dark:bg-green-900/20',
      borderColor: 'border-green-200 dark:border-green-700',
      label: 'Healthy'
    },
    warning: {
      icon: AlertTriangle,
      color: 'text-yellow-600 dark:text-yellow-400',
      bgColor: 'bg-yellow-100 dark:bg-yellow-900/20',
      borderColor: 'border-yellow-200 dark:border-yellow-700',
      label: 'Warning'
    },
    critical: {
      icon: XCircle,
      color: 'text-red-600 dark:text-red-400',
      bgColor: 'bg-red-100 dark:bg-red-900/20',
      borderColor: 'border-red-200 dark:border-red-700',
      label: 'Critical'
    }
  };

  const status = statusConfig[health.status];
  const StatusIcon = status.icon;

  return (
    <div className={`bg-white dark:bg-dark-surface rounded-lg border ${status.borderColor} shadow-sm p-6`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className={`p-2 ${status.bgColor} rounded-lg`}>
            <StatusIcon className={status.color} size={24} />
          </div>
          <div>
            <h3 className="text-lg font-bold font-secondary text-light-text-primary dark:text-dark-text-primary">
              CDC Health
            </h3>
            <p className="text-xs text-gray-500">
              Last updated: {new Date(health.timestamp).toLocaleTimeString()}
            </p>
          </div>
        </div>
        <div className={`px-3 py-1 rounded-full ${status.bgColor} ${status.color} text-sm font-bold`}>
          {status.label}
        </div>
      </div>

      {/* Issues Section */}
      {health.issues.length > 0 && (
        <div className={`mb-4 p-3 ${status.bgColor} rounded border ${status.borderColor}`}>
          <h4 className={`font-semibold text-sm ${status.color} mb-2`}>Active Issues:</h4>
          <ul className="space-y-1">
            {health.issues.map((issue, idx) => (
              <li key={idx} className={`text-xs ${status.color} flex items-start`}>
                <span className="mr-2">•</span>
                <span>{issue}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        {/* WAL Size */}
        <div className="space-y-1">
          <div className="flex items-center space-x-2 text-gray-500">
            <HardDrive size={14} />
            <span className="text-xs font-medium">WAL Directory</span>
          </div>
          <p className="text-lg font-bold font-mono text-light-text-primary dark:text-dark-text-primary">
            {health.wal.directory_size}
          </p>
          <p className="text-xs text-gray-400">Position: {health.wal.position_mb.toFixed(2)} MB</p>
        </div>

        {/* Connections */}
        <div className="space-y-1">
          <div className="flex items-center space-x-2 text-gray-500">
            <Users size={14} />
            <span className="text-xs font-medium">Connections</span>
          </div>
          <p className="text-lg font-bold font-mono text-light-text-primary dark:text-dark-text-primary">
            {health.connections.active} / {health.connections.total}
          </p>
          <p className="text-xs text-gray-400">Active / Total</p>
        </div>
      </div>

      {/* Replication Slots */}
      {health.slots.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-semibold text-light-text-primary dark:text-dark-text-primary flex items-center space-x-2">
            <Database size={14} />
            <span>Replication Slots ({health.slots.length})</span>
          </h4>
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {health.slots.map((slot, idx) => {
              const isInactive = !slot.active;
              const hasHighLag = slot.lag_mb !== null && slot.lag_mb > 100;
              const slotStatus = isInactive ? 'critical' : hasHighLag ? 'warning' : 'healthy';
              const slotStatusConfig = statusConfig[slotStatus];

              return (
                <div
                  key={idx}
                  className={`p-3 rounded border ${slotStatusConfig.borderColor} ${slotStatusConfig.bgColor}`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-mono font-semibold text-light-text-primary dark:text-dark-text-primary">
                      {slot.slot_name}
                    </span>
                    <span
                      className={`text-xs px-2 py-0.5 rounded ${
                        slot.active
                          ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
                          : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'
                      }`}
                    >
                      {slot.active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div>
                      <span className="text-gray-500">Type:</span>
                      <span className="ml-1 text-light-text-primary dark:text-dark-text-primary font-mono">
                        {slot.slot_type}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500">Instance:</span>
                      <span className="ml-1 text-light-text-primary dark:text-dark-text-primary font-mono truncate block" title={slot.instance_label || slot.database}>
                        {slot.instance_label || slot.database}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500">Lag:</span>
                      <span
                        className={`ml-1 font-mono font-semibold ${
                          slot.lag_mb === null
                            ? 'text-gray-400'
                            : slot.lag_mb > 100
                            ? 'text-red-600 dark:text-red-400'
                            : slot.lag_mb > 50
                            ? 'text-yellow-600 dark:text-yellow-400'
                            : 'text-green-600 dark:text-green-400'
                        }`}
                      >
                        {slot.lag_mb !== null ? `${slot.lag_mb.toFixed(2)} MB` : 'N/A'}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500">Flush Lag:</span>
                      <span className="ml-1 text-light-text-primary dark:text-dark-text-primary font-mono">
                        {slot.flush_lag_mb !== null ? `${slot.flush_lag_mb.toFixed(2)} MB` : 'N/A'}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* No Slots Message */}
      {health.slots.length === 0 && (
        <div className="text-center py-4 text-sm text-gray-500">
          <Database className="mx-auto mb-2" size={32} />
          <p>No replication slots configured</p>
        </div>
      )}

      {/* Refresh Button */}
      <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
        <button
          onClick={fetchHealth}
          disabled={loading}
          className="w-full py-2 px-4 bg-light-primary dark:bg-dark-primary text-white rounded hover:opacity-90 transition-opacity disabled:opacity-50 text-sm font-medium"
        >
          {loading ? 'Refreshing...' : 'Refresh Health Status'}
        </button>
      </div>
    </div>
  );
}
