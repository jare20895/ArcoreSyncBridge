import React, { useState, useEffect, useCallback } from 'react';
import { getReplicationSlots, createReplicationSlot, dropReplicationSlot } from '../services/api';
import { useConfirmDialog } from '@/components/ui/ConfirmDialogProvider';
import { useToast } from '@/components/ui/ToastProvider';

interface ReplicationSlot {
  slot_name: string;
  plugin: string;
  slot_type: string;
  active: boolean;
  restart_lsn: string | null;
  confirmed_flush_lsn: string | null;
}

interface ReplicationSlotManagerProps {
  instanceId: string;
}

export const ReplicationSlotManager: React.FC<ReplicationSlotManagerProps> = ({ instanceId }) => {
  const [slots, setSlots] = useState<ReplicationSlot[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [newSlotName, setNewSlotName] = useState('');
  const [creating, setCreating] = useState(false);
  const { confirm } = useConfirmDialog();
  const { showToast } = useToast();

  const loadSlots = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await getReplicationSlots(instanceId);
      setSlots(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load slots');
    } finally {
      setLoading(false);
    }
  }, [instanceId]);

  useEffect(() => {
    loadSlots();
  }, [loadSlots]);

  const handleCreate = async () => {
    if (!newSlotName) return;
    setCreating(true);
    setError('');
    try {
      await createReplicationSlot(instanceId, newSlotName);
      showToast({
        title: 'Replication slot created',
        description: `${newSlotName} is now available for CDC configuration.`,
        variant: 'success',
      });
      setNewSlotName('');
      await loadSlots();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create slot');
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (slotName: string) => {
    const confirmed = await confirm({
      title: 'Drop replication slot?',
      description: `Dropping "${slotName}" can interrupt CDC processing for this source instance.`,
      confirmLabel: 'Drop Slot',
      cancelLabel: 'Keep Slot',
      tone: 'danger',
    });
    if (!confirmed) return;

    setError('');
    try {
      await dropReplicationSlot(instanceId, slotName);
      showToast({
        title: 'Replication slot dropped',
        description: `${slotName} has been removed from the source instance.`,
        variant: 'success',
      });
      await loadSlots();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to drop slot');
    }
  };

  if (loading && slots.length === 0) {
    return <div className="text-sm text-gray-500">Loading replication slots...</div>;
  }

  return (
    <div className="mt-8 border-t border-gray-200 dark:border-gray-700 pt-6">
      <h3 className="text-lg font-medium text-light-text-primary dark:text-dark-text-primary mb-4">Replication Slots</h3>
      
      {error && <div className="bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400 p-3 rounded mb-4 text-sm">{error}</div>}

      <div className="mb-4 flex gap-2">
        <input
          type="text"
          value={newSlotName}
          onChange={(e) => setNewSlotName(e.target.value)}
          placeholder="New slot name (e.g. arcore_cdc_slot)"
          className="flex-1 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm p-2 bg-white dark:bg-dark-surface text-light-text-primary dark:text-dark-text-primary text-sm"
        />
        <button
          onClick={handleCreate}
          disabled={!newSlotName || creating}
          className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:opacity-50 text-sm"
        >
          {creating ? 'Creating...' : 'Create Slot'}
        </button>
      </div>

      <div className="bg-white dark:bg-dark-surface border border-gray-200 dark:border-gray-700 rounded-md overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50 dark:bg-gray-800">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Slot Name</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Plugin</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Active</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody className="bg-white dark:bg-dark-surface divide-y divide-gray-200 dark:divide-gray-700">
            {slots.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-6 py-4 text-center text-sm text-gray-500 dark:text-gray-400">
                  No replication slots found.
                </td>
              </tr>
            ) : (
              slots.map((slot) => (
                <tr key={slot.slot_name}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-light-text-primary dark:text-dark-text-primary">{slot.slot_name}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">{slot.plugin}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                      slot.active ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                    }`}>
                      {slot.active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button
                      onClick={() => handleDelete(slot.slot_name)}
                      className="text-red-600 hover:text-red-900 dark:text-red-400 dark:hover:text-red-300"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
        Replication slots are required for CDC. Assign a slot name in the instance configuration above after creating it here.
      </p>
    </div>
  );
};
