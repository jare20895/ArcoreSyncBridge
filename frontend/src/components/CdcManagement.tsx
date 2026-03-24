import React, { useCallback, useEffect, useState } from 'react';
import { dropHealthReplicationSlot, getCdcHealth, getDatabaseStats, vacuumHealthTable } from '../services/api';
import { Trash2, RefreshCw, Database, HardDrive, AlertTriangle, CheckCircle, Play, Settings } from 'lucide-react';
import { useToast } from './ui/ToastProvider';
import { useConfirmDialog } from './ui/ConfirmDialogProvider';

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

interface TableData {
  schema: string;
  table: string;
  size: string;
  size_bytes: number;
  modifications: number;
  live_tuples: number;
}

export default function CdcManagement() {
  const { showToast } = useToast();
  const { confirm } = useConfirmDialog();
  const [health, setHealth] = useState<any>(null);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [selectedSlots, setSelectedSlots] = useState<Set<string>>(new Set());
  const [selectedTables, setSelectedTables] = useState<Set<string>>(new Set());

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [healthData, statsData] = await Promise.all([
        getCdcHealth(),
        getDatabaseStats()
      ]);
      setHealth(healthData);
      setStats(statsData);
    } catch (err) {
      console.error('Error fetching CDC data:', err);
      showToast({
        title: 'CDC data load failed',
        description: 'Failed to fetch CDC health and database statistics.',
        variant: 'error',
      });
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    void fetchData();
  }, [fetchData]);

  const handleDropSlot = async (slotName: string, force: boolean = false) => {
    const slot = health?.slots?.find((s: SlotData) => s.slot_name === slotName);
    const isActive = slot?.active;
    const instanceId = slot?.instance_id;

    let message = `Are you sure you want to drop replication slot '${slotName}'?`;
    if (isActive && !force) {
      message += '\n\nWARNING: This slot is currently ACTIVE. Dropping it will terminate the connection and may cause data loss.';
    }
    message += '\n\nThis action cannot be undone.';

    const confirmed = await confirm({
      title: force ? `Force drop slot ${slotName}?` : `Drop slot ${slotName}?`,
      description: message,
      confirmLabel: force ? 'Force drop' : 'Drop slot',
      tone: 'danger',
    });
    if (!confirmed) {
      return;
    }

    setActionLoading(`drop-slot-${slotName}`);
    try {
      await dropHealthReplicationSlot({
        slot_name: slotName,
        force,
        instance_id: instanceId || undefined,
      });
      showToast({
        title: 'Slot dropped',
        description: `Successfully dropped slot: ${slotName}`,
        variant: 'success',
      });
      await fetchData();
    } catch (err: any) {
      if (err?.response?.status === 409) {
        // Slot is active, ask if user wants to force
        const error = err.response.data;
        const forceConfirmed = await confirm({
          title: 'Force drop active slot?',
          description: `${error.detail}\n\nDo you want to force-drop this slot by terminating the connection?`,
          confirmLabel: 'Force drop',
          tone: 'danger',
        });
        if (forceConfirmed) {
          await handleDropSlot(slotName, true);
        }
      } else {
        showToast({
          title: 'Slot drop failed',
          description: err?.response?.data?.detail || err?.message || 'Unknown error',
          variant: 'error',
        });
      }
    } finally {
      setActionLoading(null);
    }
  };

  const handleDropSelectedSlots = async () => {
    if (selectedSlots.size === 0) {
      showToast({
        title: 'No slots selected',
        description: 'Please select at least one slot to drop.',
        variant: 'info',
      });
      return;
    }

    const activeSlots = Array.from(selectedSlots).filter(slotName => {
      const slot = health?.slots?.find((s: SlotData) => s.slot_name === slotName);
      return slot?.active;
    });

    let message = `Are you sure you want to drop ${selectedSlots.size} replication slot(s)?`;
    if (activeSlots.length > 0) {
      message += `\n\nWARNING: ${activeSlots.length} of these slots are ACTIVE. Dropping them will terminate connections and may cause data loss.`;
    }
    message += '\n\nThis action cannot be undone.';

    const confirmed = await confirm({
      title: `Drop ${selectedSlots.size} slot(s)?`,
      description: message,
      confirmLabel: 'Drop selected',
      tone: 'danger',
    });
    if (!confirmed) {
      return;
    }

    setActionLoading('drop-selected-slots');
    let successCount = 0;
    let failCount = 0;

    try {
      for (const slotName of Array.from(selectedSlots)) {
        const slot = health?.slots?.find((s: SlotData) => s.slot_name === slotName);
        const isActive = slot?.active;
        const instanceId = slot?.instance_id;

        try {
          await dropHealthReplicationSlot({ slot_name: slotName, force: isActive, instance_id: instanceId || undefined });
          successCount++;
        } catch {
          failCount++;
        }
      }

      showToast({
        title: 'Slot cleanup complete',
        description: `Dropped ${successCount} slot(s) successfully${failCount > 0 ? `, ${failCount} failed` : ''}`,
        variant: failCount > 0 ? 'info' : 'success',
      });
      setSelectedSlots(new Set());
      await fetchData();
    } catch (err: any) {
      showToast({
        title: 'Bulk slot drop failed',
        description: err.message,
        variant: 'error',
      });
    } finally {
      setActionLoading(null);
    }
  };

  const handleVacuumTable = async (schema: string, table: string, full: boolean = false) => {
    const vacuumType = full ? 'VACUUM FULL' : 'VACUUM';
    const confirmed = await confirm({
      title: `Run ${vacuumType}?`,
      description: `Are you sure you want to run ${vacuumType} on ${schema}.${table}? ${full ? 'This will lock the table and may take a while.' : ''}`,
      confirmLabel: vacuumType,
      tone: 'danger',
    });
    if (!confirmed) {
      return;
    }

    setActionLoading(`vacuum-${schema}-${table}`);
    try {
      await vacuumHealthTable({ schema, table, full });
      showToast({
        title: `${vacuumType} completed`,
        description: `Successfully ran ${vacuumType} on ${schema}.${table}`,
        variant: 'success',
      });
      await fetchData();
    } catch (err: any) {
      showToast({
        title: `${vacuumType} failed`,
        description: err?.response?.data?.detail || err?.message,
        variant: 'error',
      });
    } finally {
      setActionLoading(null);
    }
  };

  const handleVacuumSelectedTables = async (full: boolean = false) => {
    if (selectedTables.size === 0) {
      showToast({
        title: 'No tables selected',
        description: 'Please select at least one table to vacuum.',
        variant: 'info',
      });
      return;
    }

    const vacuumType = full ? 'VACUUM FULL' : 'VACUUM';
    const confirmed = await confirm({
      title: `Run ${vacuumType} on ${selectedTables.size} table(s)?`,
      description: `Are you sure you want to run ${vacuumType} on ${selectedTables.size} table(s)? ${full ? 'This will lock the tables and may take a while.' : ''}`,
      confirmLabel: vacuumType,
      tone: 'danger',
    });
    if (!confirmed) {
      return;
    }

    setActionLoading('vacuum-selected-tables');
    try {
      for (const tableKey of Array.from(selectedTables)) {
        const [schema, table] = tableKey.split('.');
        await vacuumHealthTable({ schema, table, full });
      }
      showToast({
        title: `${vacuumType} completed`,
        description: `Successfully vacuumed ${selectedTables.size} table(s)`,
        variant: 'success',
      });
      setSelectedTables(new Set());
      await fetchData();
    } catch (err: any) {
      showToast({
        title: `Bulk ${vacuumType} failed`,
        description: err.message,
        variant: 'error',
      });
    } finally {
      setActionLoading(null);
    }
  };

  const toggleSlotSelection = (slotName: string) => {
    const newSelection = new Set(selectedSlots);
    if (newSelection.has(slotName)) {
      newSelection.delete(slotName);
    } else {
      newSelection.add(slotName);
    }
    setSelectedSlots(newSelection);
  };

  const toggleTableSelection = (schema: string, table: string) => {
    const tableKey = `${schema}.${table}`;
    const newSelection = new Set(selectedTables);
    if (newSelection.has(tableKey)) {
      newSelection.delete(tableKey);
    } else {
      newSelection.add(tableKey);
    }
    setSelectedTables(newSelection);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <RefreshCw className="animate-spin mr-2" size={24} />
        <span>Loading CDC management data...</span>
      </div>
    );
  }

  const inactiveSlots = health?.slots?.filter((s: SlotData) => !s.active) || [];
  const highLagSlots = health?.slots?.filter((s: SlotData) => s.lag_mb && s.lag_mb > 100) || [];
  const bloatedTables = stats?.tables?.filter((t: TableData) => t.size_bytes > 50 * 1024 * 1024) || []; // >50MB

  return (
    <div className="space-y-8">
      {/* Quick Actions Summary */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-gray-800 dark:to-gray-900 p-6 rounded-lg border border-blue-200 dark:border-gray-700">
        <h2 className="text-xl font-bold mb-4 flex items-center">
          <Settings className="mr-2" size={24} />
          CDC Management & Optimization
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white dark:bg-dark-surface p-4 rounded shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Inactive Slots</p>
                <p className="text-2xl font-bold text-red-600 dark:text-red-400">{inactiveSlots.length}</p>
              </div>
              <AlertTriangle className="text-red-600 dark:text-red-400" size={32} />
            </div>
            <p className="text-xs text-gray-500 mt-2">Preventing WAL cleanup</p>
          </div>
          <div className="bg-white dark:bg-dark-surface p-4 rounded shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">High Lag Slots</p>
                <p className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">{highLagSlots.length}</p>
              </div>
              <AlertTriangle className="text-yellow-600 dark:text-yellow-400" size={32} />
            </div>
            <p className="text-xs text-gray-500 mt-2">&gt;100MB behind</p>
          </div>
          <div className="bg-white dark:bg-dark-surface p-4 rounded shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Large Tables</p>
                <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">{bloatedTables.length}</p>
              </div>
              <Database className="text-blue-600 dark:text-blue-400" size={32} />
            </div>
            <p className="text-xs text-gray-500 mt-2">&gt;50MB size</p>
          </div>
        </div>
      </div>

      {/* Replication Slots Management */}
      <div className="bg-white dark:bg-dark-surface rounded-lg border border-gray-200 dark:border-gray-800 shadow-sm">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-800 flex justify-between items-center">
          <h3 className="text-lg font-bold flex items-center">
            <Database className="mr-2" size={20} />
            Replication Slots ({health?.slots?.length || 0})
          </h3>
          <div className="flex gap-2">
            {selectedSlots.size > 0 && (
              <button
                onClick={handleDropSelectedSlots}
                disabled={actionLoading !== null}
                className="px-3 py-1.5 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50 text-sm flex items-center"
              >
                <Trash2 size={14} className="mr-1" />
                Drop Selected ({selectedSlots.size})
              </button>
            )}
            <button
              onClick={fetchData}
              disabled={loading}
              className="px-3 py-1.5 bg-gray-600 text-white rounded hover:bg-gray-700 disabled:opacity-50 text-sm flex items-center"
            >
              <RefreshCw size={14} className="mr-1" />
              Refresh
            </button>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-800">
            <thead className="bg-gray-50 dark:bg-gray-900">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  <input
                    type="checkbox"
                    checked={selectedSlots.size === health?.slots?.length && health?.slots?.length > 0}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedSlots(new Set(health.slots.map((s: SlotData) => s.slot_name)));
                      } else {
                        setSelectedSlots(new Set());
                      }
                    }}
                  />
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Slot Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Instance</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Lag</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-dark-surface divide-y divide-gray-200 dark:divide-gray-800">
              {health?.slots?.map((slot: SlotData) => (
                <tr key={slot.slot_name} className={selectedSlots.has(slot.slot_name) ? 'bg-blue-50 dark:bg-blue-900/20' : ''}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <input
                      type="checkbox"
                      checked={selectedSlots.has(slot.slot_name)}
                      onChange={() => toggleSlotSelection(slot.slot_name)}
                    />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-mono">{slot.slot_name}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 rounded-full text-xs font-bold ${
                      slot.active
                        ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
                        : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'
                    }`}>
                      {slot.active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">{slot.slot_type}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-mono">
                    {slot.instance_label || slot.database}
                    {slot.instance_label && slot.database && slot.instance_label !== slot.database && (
                      <span className="text-gray-400 block text-xs">{slot.database}</span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <span className={`font-mono font-semibold ${
                      slot.lag_mb === null ? 'text-gray-400' :
                      slot.lag_mb > 100 ? 'text-red-600 dark:text-red-400' :
                      slot.lag_mb > 50 ? 'text-yellow-600 dark:text-yellow-400' :
                      'text-green-600 dark:text-green-400'
                    }`}>
                      {slot.lag_mb !== null ? `${slot.lag_mb.toFixed(2)} MB` : 'N/A'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <button
                      onClick={() => handleDropSlot(slot.slot_name)}
                      disabled={actionLoading !== null}
                      className="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300 disabled:opacity-50 flex items-center"
                    >
                      <Trash2 size={14} className="mr-1" />
                      Drop
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {(!health?.slots || health.slots.length === 0) && (
            <div className="text-center py-8 text-gray-500">
              <Database className="mx-auto mb-2" size={48} />
              <p>No replication slots found</p>
            </div>
          )}
        </div>
      </div>

      {/* Table Management */}
      <div className="bg-white dark:bg-dark-surface rounded-lg border border-gray-200 dark:border-gray-800 shadow-sm">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-800 flex justify-between items-center">
          <h3 className="text-lg font-bold flex items-center">
            <HardDrive className="mr-2" size={20} />
            Tables - Top 10 by Size
          </h3>
          <div className="flex gap-2">
            {selectedTables.size > 0 && (
              <>
                <button
                  onClick={() => handleVacuumSelectedTables(false)}
                  disabled={actionLoading !== null}
                  className="px-3 py-1.5 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 text-sm flex items-center"
                >
                  <Play size={14} className="mr-1" />
                  Vacuum Selected ({selectedTables.size})
                </button>
                <button
                  onClick={() => handleVacuumSelectedTables(true)}
                  disabled={actionLoading !== null}
                  className="px-3 py-1.5 bg-purple-600 text-white rounded hover:bg-purple-700 disabled:opacity-50 text-sm flex items-center"
                >
                  <Play size={14} className="mr-1" />
                  Vacuum Full Selected
                </button>
              </>
            )}
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-800">
            <thead className="bg-gray-50 dark:bg-gray-900">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  <input
                    type="checkbox"
                    checked={selectedTables.size === stats?.tables?.length && stats?.tables?.length > 0}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedTables(new Set(stats.tables.map((t: TableData) => `${t.schema}.${t.table}`)));
                      } else {
                        setSelectedTables(new Set());
                      }
                    }}
                  />
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Schema</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Table</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Size</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Modifications</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Live Tuples</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-dark-surface divide-y divide-gray-200 dark:divide-gray-800">
              {stats?.tables?.map((table: TableData) => {
                const tableKey = `${table.schema}.${table.table}`;
                return (
                  <tr key={tableKey} className={selectedTables.has(tableKey) ? 'bg-blue-50 dark:bg-blue-900/20' : ''}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <input
                        type="checkbox"
                        checked={selectedTables.has(tableKey)}
                        onChange={() => toggleTableSelection(table.schema, table.table)}
                      />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-mono">{table.schema}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-mono">{table.table}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-mono font-semibold">
                      {table.size}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-mono">
                      {table.modifications.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-mono">
                      {table.live_tuples.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleVacuumTable(table.schema, table.table, false)}
                          disabled={actionLoading !== null}
                          className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 disabled:opacity-50"
                        >
                          Vacuum
                        </button>
                        <button
                          onClick={() => handleVacuumTable(table.schema, table.table, true)}
                          disabled={actionLoading !== null}
                          className="text-purple-600 hover:text-purple-800 dark:text-purple-400 dark:hover:text-purple-300 disabled:opacity-50"
                        >
                          Full
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Cache Statistics */}
      {stats && (
        <div className="bg-white dark:bg-dark-surface rounded-lg border border-gray-200 dark:border-gray-800 shadow-sm p-6">
          <h3 className="text-lg font-bold mb-4 flex items-center">
            <CheckCircle className="mr-2" size={20} />
            Database Cache Performance
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <p className="text-sm text-gray-500">Cache Hit Ratio</p>
              <p className={`text-3xl font-bold font-mono ${
                stats.cache_hit_ratio >= 90 ? 'text-green-600' :
                stats.cache_hit_ratio >= 75 ? 'text-yellow-600' :
                'text-red-600'
              }`}>
                {stats.cache_hit_ratio.toFixed(1)}%
              </p>
              <p className="text-xs text-gray-500 mt-1">Target: &gt;90%</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Heap Blocks Hit</p>
              <p className="text-2xl font-bold font-mono text-green-600">
                {(stats.heap_blocks_hit / 1000000000).toFixed(2)}B
              </p>
              <p className="text-xs text-gray-500 mt-1">From cache</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Heap Blocks Read</p>
              <p className="text-2xl font-bold font-mono text-red-600">
                {(stats.heap_blocks_read / 1000000000).toFixed(2)}B
              </p>
              <p className="text-xs text-gray-500 mt-1">From disk</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
