import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { 
    createSyncDefinition, 
    getDatabases, 
    getSourceTables, 
    getSharePointListsBySourceTable,
    getSharePointSites,
    getSharePointLists
} from '../../services/api';
import Link from 'next/link';

export default function NewSyncDefinition() {
  const router = useRouter();
  
  // Catalogs
  const [databases, setDatabases] = useState<any[]>([]);
  const [tables, setTables] = useState<any[]>([]);
  const [sites, setSites] = useState<any[]>([]);
  const [targetLists, setTargetLists] = useState<any[]>([]);

  // Selection State
  const [selectedDatabaseId, setSelectedDatabaseId] = useState('');
  const [selectedSiteId, setSelectedSiteId] = useState('');

  const [formData, setFormData] = useState({
    name: '',
    source_table_id: '',
    target_list_id: '',
    sync_mode: 'ONE_WAY_PUSH',
    conflict_policy: 'SOURCE_WINS',
    key_strategy: 'PRIMARY_KEY',
    target_strategy: 'SINGLE',
    cursor_strategy: 'UPDATED_AT',
    sharding_policy: JSON.stringify({
        rules: [
            { "if": "status == 'Archived'", "target_list_id": "uuid-here" }
        ],
        "default_target_list_id": "uuid-here"
    }, null, 2),
    sources: [],
    targets: [],
    key_columns: [],
    field_mappings: []
  });
  const [error, setError] = useState('');

  // 1. Load Databases & Sites on Mount
  useEffect(() => {
    getDatabases().then(setDatabases).catch(console.error);
    getSharePointSites().then(setSites).catch(console.error);
  }, []);

  // 2. Load Tables when Database selected
  useEffect(() => {
      if (!selectedDatabaseId) {
          setTables([]);
          return;
      }
      getSourceTables(selectedDatabaseId).then(setTables).catch(console.error);
  }, [selectedDatabaseId]);

  // 3. Load Target Lists when Site selected
  useEffect(() => {
      if (!selectedSiteId) {
          setTargetLists([]);
          return;
      }
      getSharePointLists(selectedSiteId).then(setTargetLists).catch(console.error);
  }, [selectedSiteId]);

  // 4. Auto-detect Target List when Source Table changes
  useEffect(() => {
      if (!formData.source_table_id) return;
      
      // Try to find linked lists
      getSharePointListsBySourceTable(formData.source_table_id).then(lists => {
          if (lists && lists.length > 0) {
              // Found a linked list!
              const linkedList = lists[0];
              // Pre-select it
              setFormData(prev => ({ ...prev, target_list_id: linkedList.id }));
              // Also try to set the site context if we can
              if (linkedList.site_id) {
                  setSelectedSiteId(linkedList.site_id);
              }
          }
      }).catch(console.error);
      
      // Auto-name sync definition if empty
      const table = tables.find(t => t.id === formData.source_table_id);
      if (table && !formData.name) {
          setFormData(prev => ({ ...prev, name: `Sync ${table.table_name}` }));
      }
  }, [formData.source_table_id]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
        const payload = {
            ...formData,
            sharding_policy: JSON.parse(formData.sharding_policy)
        };
      await createSyncDefinition(payload);
      router.push('/sync-definitions');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create definition');
    }
  };

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6 text-light-text-primary dark:text-dark-text-primary">New Sync Definition</h1>
      {error && <div className="bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 p-3 rounded mb-4">{error}</div>}
      
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid grid-cols-2 gap-6">
            <div>
            <label className="block text-sm font-medium text-light-text-primary dark:text-dark-text-primary">Name</label>
            <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                required
                className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm p-2 bg-white dark:bg-dark-surface text-light-text-primary dark:text-dark-text-primary"
            />
            </div>

            <div>
            <label className="block text-sm font-medium text-light-text-primary dark:text-dark-text-primary">Sync Mode</label>
            <select
                name="sync_mode"
                value={formData.sync_mode}
                onChange={handleChange}
                className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm p-2 bg-white dark:bg-dark-surface text-light-text-primary dark:text-dark-text-primary"
            >
                <option value="ONE_WAY_PUSH">One-Way Push</option>
                <option value="TWO_WAY">Two-Way</option>
            </select>
            </div>
        </div>

        {/* Source Selection Section */}
        <div className="bg-white dark:bg-dark-surface p-4 rounded border border-gray-200 dark:border-gray-700">
            <h3 className="text-sm font-semibold mb-4 text-light-text-primary dark:text-dark-text-primary">Source Configuration</h3>
            <div className="grid grid-cols-2 gap-6">
                <div>
                    <label className="block text-sm font-medium text-light-text-primary dark:text-dark-text-primary">Database</label>
                    <select
                        value={selectedDatabaseId}
                        onChange={(e) => setSelectedDatabaseId(e.target.value)}
                        className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm p-2 bg-white dark:bg-dark-surface"
                    >
                        <option value="">Select Database</option>
                        {databases.map(db => (
                            <option key={db.id} value={db.id}>{db.name}</option>
                        ))}
                    </select>
                </div>
                <div>
                    <label className="block text-sm font-medium text-light-text-primary dark:text-dark-text-primary">Source Table</label>
                    <select
                        name="source_table_id"
                        value={formData.source_table_id}
                        onChange={handleChange}
                        required
                        className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm p-2 bg-white dark:bg-dark-surface"
                        disabled={!selectedDatabaseId}
                    >
                        <option value="">Select Table</option>
                        {tables.map(t => (
                            <option key={t.id} value={t.id}>{t.schema_name}.{t.table_name}</option>
                        ))}
                    </select>
                </div>
            </div>
        </div>

        {/* Target Selection Section */}
        <div className="bg-white dark:bg-dark-surface p-4 rounded border border-gray-200 dark:border-gray-700">
            <h3 className="text-sm font-semibold mb-4 text-light-text-primary dark:text-dark-text-primary">Target Configuration</h3>
            <div className="grid grid-cols-2 gap-6">
                <div>
                    <label className="block text-sm font-medium text-light-text-primary dark:text-dark-text-primary">SharePoint Site</label>
                    <select
                        value={selectedSiteId}
                        onChange={(e) => setSelectedSiteId(e.target.value)}
                        className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm p-2 bg-white dark:bg-dark-surface"
                    >
                        <option value="">Select Site</option>
                        {sites.map(s => (
                            <option key={s.id} value={s.id}>{s.hostname} {s.site_path}</option>
                        ))}
                    </select>
                </div>
                <div>
                    <label className="block text-sm font-medium text-light-text-primary dark:text-dark-text-primary">Target List</label>
                    <select
                        name="target_list_id"
                        value={formData.target_list_id}
                        onChange={handleChange}
                        className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm p-2 bg-white dark:bg-dark-surface"
                        disabled={!selectedSiteId}
                    >
                        <option value="">Select List (or use Sharding)</option>
                        {targetLists.map(l => (
                            <option key={l.id} value={l.id}>{l.display_name} {l.is_provisioned ? '(Linked)' : ''}</option>
                        ))}
                    </select>
                    {formData.source_table_id && !formData.target_list_id && (
                        <p className="text-xs text-orange-500 mt-1">No linked list found. Please select manually.</p>
                    )}
                </div>
            </div>
        </div>
        
        <div className="grid grid-cols-2 gap-6">
            <div>
            <label className="block text-sm font-medium text-light-text-primary dark:text-dark-text-primary">Target Strategy</label>
            <select
                name="target_strategy"
                value={formData.target_strategy}
                onChange={handleChange}
                className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm p-2 bg-white dark:bg-dark-surface text-light-text-primary dark:text-dark-text-primary"
            >
                <option value="SINGLE">Single Target</option>
                <option value="CONDITIONAL">Conditional (Sharding)</option>
            </select>
            </div>

            <div>
            <label className="block text-sm font-medium text-light-text-primary dark:text-dark-text-primary">Cursor Strategy</label>
            <select
                name="cursor_strategy"
                value={formData.cursor_strategy}
                onChange={handleChange}
                className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm p-2 bg-white dark:bg-dark-surface text-light-text-primary dark:text-dark-text-primary"
            >
                <option value="UPDATED_AT">Updated At Timestamp</option>
                <option value="INCREMENTAL_ID">Incremental ID</option>
            </select>
            </div>
        </div>

        {formData.target_strategy === 'CONDITIONAL' && (
            <div>
                <label className="block text-sm font-medium text-light-text-primary dark:text-dark-text-primary">Sharding Policy (JSON)</label>
                <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary mb-2">Define rules for routing items to different lists.</p>
                <textarea
                    name="sharding_policy"
                    value={formData.sharding_policy}
                    onChange={handleChange}
                    rows={8}
                    className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm p-2 font-mono text-sm bg-white dark:bg-dark-surface text-light-text-primary dark:text-dark-text-primary"
                />
            </div>
        )}

        <div className="bg-gray-50 dark:bg-gray-800/40 p-4 rounded border border-gray-200 dark:border-gray-700">
             <h3 className="text-sm font-semibold mb-2 text-light-text-primary dark:text-dark-text-primary">Advanced Configuration</h3>
             <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary">For Phase 2, please configure Field Mappings and Sources via API or future UI updates. This form creates the base definition.</p>
        </div>

        <div className="flex justify-between">
            <Link href="/sync-definitions" className="bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-200 px-4 py-2 rounded hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors">
                Cancel
            </Link>
            <button
            type="submit"
            className="bg-light-primary dark:bg-dark-primary text-white px-6 py-2 rounded hover:opacity-90 transition-opacity"
            >
            Create Definition
            </button>
        </div>
      </form>
    </div>
  );
}
