import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import {
    getSyncDefinition,
    generateDriftReport,
    triggerSync,
    updateSyncDefinition,
    getSharePointSites,
    getSharePointLists,
    getSourceTableDetails,
    bulkUpdateFieldMappings,
    getSharePointColumns,
    resetSyncCursors
} from '../../services/api';
import { AlertTriangle, CheckCircle, RefreshCw, ArrowRightLeft, ArrowRight, Play, Settings, Database, Layers, Activity, List as ListIcon, Edit2, X, Save, RotateCcw } from 'lucide-react';
import FieldMappingEditor from '../../components/FieldMappingEditor';

export default function SyncDefinitionDetail() {
  const router = useRouter();
  const { id } = router.query;
  const [def, setDef] = useState<any>(null);
  const [activeSection, setActiveSection] = useState('overview');
  const [report, setReport] = useState<any>(null);
  const [loadingReport, setLoadingReport] = useState(false);
  const [runningSync, setRunningSync] = useState(false);

  // Editing State
  const [isEditingTargets, setIsEditingTargets] = useState(false);
  const [sites, setSites] = useState<any[]>([]);
  const [targetLists, setTargetLists] = useState<any[]>([]);
  const [editSiteId, setEditSiteId] = useState('');
  const [editListId, setEditListId] = useState('');

  // Field Mapping State
  const [sourceColumns, setSourceColumns] = useState<any[]>([]);
  const [targetColumns, setTargetColumns] = useState<any[]>([]);

  useEffect(() => {
    if (!id) return;
    getSyncDefinition(id as string).then(setDef).catch(console.error);
  }, [id]);

  // Load Sites when entering Edit Mode
  useEffect(() => {
      if (isEditingTargets && sites.length === 0) {
          getSharePointSites().then(setSites).catch(console.error);
      }
  }, [isEditingTargets]);

  // Load Lists when Site Selected
  useEffect(() => {
      if (editSiteId) {
          getSharePointLists(editSiteId).then(setTargetLists).catch(console.error);
      }
  }, [editSiteId]);

  // Load Source and Target Columns for Field Mapping Editor
  useEffect(() => {
      if (def && def.source_table_id && activeSection === 'mappings') {
          // Load source database columns
          getSourceTableDetails(def.source_table_id)
              .then(details => {
                  if (details && details.columns) {
                      setSourceColumns(details.columns.map((col: any) => ({
                          id: col.id || col.column_name,
                          name: col.column_name,
                          data_type: col.data_type
                      })));
                  }
              })
              .catch(console.error);

          // Load target SharePoint columns if target_list_id is set
          if (def.target_list_id) {
              getSharePointColumns(def.target_list_id)
                  .then(columns => {
                      if (columns && columns.length > 0) {
                          setTargetColumns(columns.map((col: any) => ({
                              id: col.id || col.column_name,
                              name: col.column_name,
                              data_type: col.column_type,
                              is_readonly: col.is_readonly || false,
                              is_required: col.is_required || false
                          })));
                      }
                  })
                  .catch(err => {
                      console.error('Failed to load SharePoint columns:', err);
                      // Fallback: use existing mappings if API fails
                      if (def.field_mappings && def.field_mappings.length > 0) {
                          const uniqueTargets = Array.from(new Set(
                              def.field_mappings.map((m: any) => m.target_column_name)
                          )).map(name => ({
                              id: name,
                              name: name as string,
                              data_type: 'text'
                          }));
                          setTargetColumns(uniqueTargets);
                      }
                  });
          }
      }
  }, [def, activeSection]);

  const handleRunReport = async () => {
    setLoadingReport(true);
    try {
        const res = await generateDriftReport({
            sync_def_id: id as string,
            check_type: 'LEDGER_VALIDITY'
        });
        setReport(res);
    } catch (e) {
        console.error(e);
        alert("Failed to run report");
    } finally {
        setLoadingReport(false);
    }
  };
  
  const handleRunSync = async () => {
    if (!id) return;
    setRunningSync(true);
    try {
        const res = await triggerSync(id as string);
        alert("Sync Completed: " + JSON.stringify(res, null, 2));
    } catch (e) {
        console.error(e);
        alert("Failed to run sync: " + String(e));
    } finally {
        setRunningSync(false);
    }
  };

  const handleResetCursors = async () => {
    if (!id) return;
    if (!confirm("Are you sure you want to reset all sync cursors?\n\nThis will force the next sync to start from the beginning and process all rows.")) {
        return;
    }
    try {
        const res = await resetSyncCursors(id as string);
        alert(`Success: ${res.message}`);
    } catch (e) {
        console.error(e);
        alert("Failed to reset cursors: " + String(e));
    }
  };

  const handleModeToggle = async (newMode: string) => {
      if (!def || !id) return;
      try {
          const updated = await updateSyncDefinition(id as string, { sync_mode: newMode });
          setDef(updated);
      } catch (e) {
          console.error(e);
          alert("Failed to update sync mode");
      }
  };

  const handleSaveMappings = async (mappings: any[]) => {
      if (!id) return;
      try {
          // Use dedicated field mappings API endpoint for bulk update
          const updatedMappings = await bulkUpdateFieldMappings(id as string, mappings);
          // Refresh the sync definition to get the latest data
          const updated = await getSyncDefinition(id as string);
          setDef(updated);
          alert('Field mappings saved successfully!');
      } catch (e) {
          console.error(e);
          throw new Error('Failed to save field mappings');
      }
  };

  const handleSaveTarget = async () => {
      if (!id || !editListId) return;
      try {
          const updated = await updateSyncDefinition(id as string, { target_list_id: editListId });
          
          // Optimistic / Local Update of Display Name
          const selectedList = targetLists.find(l => l.id === editListId);
          if (selectedList) {
              updated.target_list_name = selectedList.display_name;
          }
          
          setDef(updated);
          setIsEditingTargets(false);
          setEditListId('');
      } catch (e) {
          console.error(e);
          alert("Failed to update target list");
      }
  };

  if (!def) return <div className="p-8 text-light-text-primary dark:text-dark-text-primary">Loading definition...</div>;

  const sections = [
      { id: 'overview', label: 'Overview', icon: Settings },
      { id: 'mappings', label: 'Field Mappings', icon: ListIcon },
      { id: 'targets', label: 'Targets & Routing', icon: Database },
      { id: 'sharding', label: 'Sharding Rules', icon: Layers },
      { id: 'ops', label: 'Operations & Drift', icon: Activity },
  ];

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
      {/* Local Sidebar */}
      <div className="w-64 bg-white dark:bg-dark-surface border-r border-gray-200 dark:border-gray-800 flex flex-col">
        <div className="p-6 border-b border-gray-200 dark:border-gray-800">
             <h1 className="text-lg font-bold font-secondary text-light-text-primary dark:text-dark-text-primary truncate" title={def.name}>{def.name}</h1>
             <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary font-mono mt-1 truncate">{def.id}</p>
        </div>
        <nav className="flex-1 p-4 space-y-1">
            {sections.map(item => (
                <button
                    key={item.id}
                    onClick={() => setActiveSection(item.id)}
                    className={`w-full flex items-center space-x-3 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                        activeSection === item.id 
                        ? 'bg-light-primary/10 text-light-primary dark:bg-dark-primary/20 dark:text-dark-primary' 
                        : 'text-light-text-secondary dark:text-dark-text-secondary hover:bg-gray-50 dark:hover:bg-gray-800 hover:text-light-text-primary dark:hover:text-dark-text-primary'
                    }`}
                >
                    <item.icon size={18} />
                    <span>{item.label}</span>
                </button>
            ))}
        </nav>
        <div className="p-4 border-t border-gray-200 dark:border-gray-800">
            <button
                onClick={() => router.push('/sync-definitions')}
                className="w-full text-xs text-center text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            >
                &larr; Back to Definitions
            </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-auto">
        <header className="bg-white dark:bg-dark-surface border-b border-gray-200 dark:border-gray-800 py-4 px-8 flex justify-between items-center sticky top-0 z-10">
            <h2 className="text-xl font-bold text-light-text-primary dark:text-dark-text-primary">
                {sections.find(s => s.id === activeSection)?.label}
            </h2>
            <div className="flex space-x-3">
                 <button
                    onClick={handleRunSync}
                    disabled={runningSync}
                    className="flex items-center space-x-2 px-4 py-2 bg-light-primary dark:bg-dark-primary text-white rounded shadow-sm text-sm font-medium hover:bg-opacity-90 disabled:opacity-50"
                 >
                    <Play size={16} className={runningSync ? "animate-spin" : ""} />
                    <span>{runningSync ? "Running..." : "Run Sync Now"}</span>
                 </button>
                 <button
                    onClick={handleResetCursors}
                    className="flex items-center space-x-2 px-4 py-2 bg-orange-500 dark:bg-orange-600 text-white rounded shadow-sm text-sm font-medium hover:bg-opacity-90"
                    title="Reset sync cursors to start from beginning"
                 >
                    <RotateCcw size={16} />
                    <span>Reset Cursor</span>
                 </button>
            </div>
        </header>

        <main className="p-8">
            {activeSection === 'overview' && (
                <div className="space-y-6 max-w-4xl">
                    <div className="bg-white dark:bg-dark-surface p-6 rounded border border-gray-200 dark:border-gray-700 shadow-sm">
                        <h3 className="text-lg font-bold text-light-text-primary dark:text-dark-text-primary mb-4">Sync Mode</h3>
                        <div className="flex space-x-4">
                            <button
                                onClick={() => handleModeToggle('ONE_WAY_PUSH')}
                                className={`flex-1 flex items-center justify-center space-x-2 px-4 py-3 rounded border ${def.sync_mode === 'ONE_WAY_PUSH' ? 'bg-blue-50 dark:bg-blue-900/30 border-blue-200 dark:border-blue-700 text-blue-700 dark:text-blue-300 ring-1 ring-blue-200 dark:ring-blue-700' : 'bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'}`}
                            >
                                <ArrowRight size={18} />
                                <span className="font-medium text-sm">One-Way Push</span>
                            </button>
                            <button
                                onClick={() => handleModeToggle('TWO_WAY')}
                                className={`flex-1 flex items-center justify-center space-x-2 px-4 py-3 rounded border ${def.sync_mode === 'TWO_WAY' ? 'bg-purple-50 dark:bg-purple-900/30 border-purple-200 dark:border-purple-700 text-purple-700 dark:text-purple-300 ring-1 ring-purple-200 dark:ring-purple-700' : 'bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'}`}
                            >
                                <ArrowRightLeft size={18} />
                                <span className="font-medium text-sm">Two-Way Sync</span>
                            </button>
                        </div>
                        <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary mt-2">
                            {def.sync_mode === 'ONE_WAY_PUSH'
                                ? "Changes in Database are pushed to SharePoint. SharePoint changes are ignored."
                                : "Changes are synchronized in both directions. Conflict policy applies."}
                        </p>
                    </div>

                    <div className="grid grid-cols-2 gap-6">
                        <div className="bg-white dark:bg-dark-surface p-6 rounded border border-gray-200 dark:border-gray-700 shadow-sm">
                            <h3 className="text-sm font-bold text-light-text-secondary dark:text-dark-text-secondary uppercase mb-2">Strategy</h3>
                            <dl className="space-y-2">
                                <div>
                                    <dt className="text-xs text-gray-500">Target Strategy</dt>
                                    <dd className="text-sm font-medium">{def.target_strategy}</dd>
                                </div>
                                <div>
                                    <dt className="text-xs text-gray-500">Conflict Policy</dt>
                                    <dd className="text-sm font-medium">{def.conflict_policy}</dd>
                                </div>
                                <div>
                                    <dt className="text-xs text-gray-500">Cursor Strategy</dt>
                                    <dd className="text-sm font-medium">{def.cursor_strategy}</dd>
                                </div>
                            </dl>
                        </div>
                         <div className="bg-white dark:bg-dark-surface p-6 rounded border border-gray-200 dark:border-gray-700 shadow-sm">
                            <h3 className="text-sm font-bold text-light-text-secondary dark:text-dark-text-secondary uppercase mb-2">IDs</h3>
                            <dl className="space-y-2">
                                <div>
                                    <dt className="text-xs text-gray-500">Source Table ID</dt>
                                    <dd className="text-xs font-mono">{def.source_table_id}</dd>
                                </div>
                                <div>
                                    <dt className="text-xs text-gray-500">Target List ID</dt>
                                    <dd className="text-xs font-mono">{def.target_list_id || 'Dynamic (Sharded)'}</dd>
                                </div>
                            </dl>
                        </div>
                    </div>
                </div>
            )}

            {activeSection === 'mappings' && (
                <FieldMappingEditor
                    mappings={def.field_mappings || []}
                    sourceColumns={sourceColumns}
                    targetColumns={targetColumns}
                    onSave={handleSaveMappings}
                    readonly={false}
                />
            )}

            {activeSection === 'targets' && (
                <div className="bg-white dark:bg-dark-surface p-6 rounded border border-gray-200 dark:border-gray-700 shadow-sm">
                    <div className="flex justify-between items-center mb-4">
                        <h3 className="text-lg font-bold text-light-text-primary dark:text-dark-text-primary">Default Target</h3>
                        {!isEditingTargets && (
                            <button 
                                onClick={() => setIsEditingTargets(true)}
                                className="flex items-center space-x-2 text-sm text-light-primary dark:text-dark-primary hover:underline"
                            >
                                <Edit2 size={14} />
                                <span>Change Target</span>
                            </button>
                        )}
                    </div>

                    {!isEditingTargets ? (
                        <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-700">
                            <div className="text-sm font-medium text-light-text-primary dark:text-dark-text-primary">
                                {def.target_list_name || 'No Default List Selected'}
                            </div>
                            <div className="text-xs text-gray-500 font-mono mt-1">
                                Internal ID: {def.target_list_id || 'N/A'}
                            </div>
                            {def.target_list_guid && (
                                <div className="text-xs text-gray-500 font-mono mt-1">
                                    SharePoint GUID: {def.target_list_guid}
                                </div>
                            )}
                        </div>
                    ) : (
                        <div className="space-y-4 p-4 bg-gray-50 dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-700">
                            <div>
                                <label className="block text-sm font-medium text-light-text-primary dark:text-dark-text-primary mb-1">SharePoint Site</label>
                                <select 
                                    value={editSiteId}
                                    onChange={(e) => setEditSiteId(e.target.value)}
                                    className="w-full border border-gray-300 dark:border-gray-600 rounded p-2 bg-white dark:bg-dark-surface text-sm"
                                >
                                    <option value="">Select Site...</option>
                                    {sites.map(s => (
                                        <option key={s.id} value={s.id}>{s.hostname} {s.site_path}</option>
                                    ))}
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-light-text-primary dark:text-dark-text-primary mb-1">Target List</label>
                                <select 
                                    value={editListId}
                                    onChange={(e) => setEditListId(e.target.value)}
                                    className="w-full border border-gray-300 dark:border-gray-600 rounded p-2 bg-white dark:bg-dark-surface text-sm"
                                    disabled={!editSiteId}
                                >
                                    <option value="">Select List...</option>
                                    {targetLists.map(l => (
                                        <option key={l.id} value={l.id}>{l.display_name}</option>
                                    ))}
                                </select>
                            </div>
                            <div className="flex justify-end space-x-2 pt-2">
                                <button 
                                    onClick={() => setIsEditingTargets(false)}
                                    className="px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-200 rounded"
                                >
                                    Cancel
                                </button>
                                <button 
                                    onClick={handleSaveTarget}
                                    disabled={!editListId}
                                    className="flex items-center space-x-1 px-3 py-1.5 bg-light-primary text-white text-sm rounded hover:opacity-90 disabled:opacity-50"
                                >
                                    <Save size={14} />
                                    <span>Save</span>
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            )}

            {activeSection === 'sharding' && (
                 <div className="space-y-4">
                    <div className="bg-white dark:bg-dark-surface p-6 rounded border border-gray-200 dark:border-gray-700 shadow-sm">
                         <h3 className="text-lg font-bold text-light-text-primary dark:text-dark-text-primary mb-2">Sharding Rules</h3>
                        <p className="text-sm text-gray-500 mb-4">Routing logic for conditional targets.</p>
                        <pre className="bg-gray-50 dark:bg-gray-800 p-4 rounded text-xs overflow-auto h-64 border border-gray-200 dark:border-gray-700 font-mono text-light-text-primary dark:text-dark-text-primary">
                            {JSON.stringify(def.sharding_policy, null, 2)}
                        </pre>
                    </div>
                </div>
            )}

            {activeSection === 'ops' && (
                <div className="space-y-8">
                <div className="bg-light-surface dark:bg-dark-surface p-6 rounded shadow-sm border border-gray-200 dark:border-gray-700">
                    <div className="flex justify-between items-start mb-4">
                        <div>
                            <h3 className="text-lg font-bold flex items-center text-light-text-primary dark:text-dark-text-primary">
                                <AlertTriangle className="mr-2 text-light-warning dark:text-dark-warning" size={20}/>
                                Drift Report
                            </h3>
                            <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary">Check for items in the Ledger that are missing from SharePoint.</p>
                        </div>
                        <button
                            onClick={handleRunReport}
                            disabled={loadingReport}
                            className="flex items-center space-x-2 px-3 py-2 bg-light-surface dark:bg-dark-surface border border-gray-300 dark:border-gray-600 rounded text-sm text-light-text-primary dark:text-dark-text-primary hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 transition-colors"
                        >
                            <RefreshCw size={16} className={loadingReport ? "animate-spin" : ""} />
                            <span>{loadingReport ? 'Running...' : 'Run Report'}</span>
                        </button>
                    </div>

                    {report && (
                        <div className="mt-4">
                            <div className="grid grid-cols-3 gap-4 mb-4">
                                <div className="bg-gray-50 dark:bg-gray-800 p-3 rounded text-center border border-gray-200 dark:border-gray-700">
                                    <span className="block text-xs text-light-text-secondary dark:text-dark-text-secondary uppercase">Timestamp</span>
                                    <span className="font-mono text-sm text-light-text-primary dark:text-dark-text-primary">{new Date(report.timestamp).toLocaleTimeString()}</span>
                                </div>
                                <div className="bg-gray-50 dark:bg-gray-800 p-3 rounded text-center border border-gray-200 dark:border-gray-700">
                                    <span className="block text-xs text-light-text-secondary dark:text-dark-text-secondary uppercase">Total Issues</span>
                                    <span className={`font-bold text-lg ${report.total_issues > 0 ? 'text-red-600 dark:text-red-400' : 'text-green-600 dark:text-green-400'}`}>
                                        {report.total_issues}
                                    </span>
                                </div>
                                <div className="bg-gray-50 dark:bg-gray-800 p-3 rounded text-center border border-gray-200 dark:border-gray-700">
                                    <span className="block text-xs text-light-text-secondary dark:text-dark-text-secondary uppercase">Status</span>
                                    <span className="font-bold text-sm text-light-text-primary dark:text-dark-text-primary">Completed</span>
                                </div>
                            </div>

                            {report.items.length > 0 ? (
                                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                                    <thead className="bg-gray-50 dark:bg-gray-800">
                                        <tr>
                                            <th className="px-4 py-2 text-left text-xs font-medium text-light-text-secondary dark:text-dark-text-secondary uppercase">Item ID</th>
                                            <th className="px-4 py-2 text-left text-xs font-medium text-light-text-secondary dark:text-dark-text-secondary uppercase">List ID</th>
                                            <th className="px-4 py-2 text-left text-xs font-medium text-light-text-secondary dark:text-dark-text-secondary uppercase">Issue</th>
                                            <th className="px-4 py-2 text-left text-xs font-medium text-light-text-secondary dark:text-dark-text-secondary uppercase">Details</th>
                                        </tr>
                                    </thead>
                                    <tbody className="bg-light-surface dark:bg-dark-surface divide-y divide-gray-200 dark:divide-gray-700">
                                        {report.items.map((item: any, idx: number) => (
                                            <tr key={idx}>
                                                <td className="px-4 py-2 text-sm font-mono text-light-text-primary dark:text-dark-text-primary">{item.item_id}</td>
                                                <td className="px-4 py-2 text-sm text-light-text-secondary dark:text-dark-text-secondary font-mono text-xs">{item.list_id}</td>
                                                <td className="px-4 py-2 text-sm">
                                                    <span className="px-2 py-0.5 rounded bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300 text-xs font-bold">
                                                        {item.issue}
                                                    </span>
                                                </td>
                                                <td className="px-4 py-2 text-sm text-light-text-secondary dark:text-dark-text-secondary">{item.details}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            ) : (
                                <div className="flex items-center justify-center p-8 bg-green-50 dark:bg-green-900/30 rounded border border-green-100 dark:border-green-700 text-green-700 dark:text-green-300">
                                    <CheckCircle className="mr-2" size={20} />
                                    <span className="font-medium">No drift detected. Ledger and SharePoint are in sync.</span>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
            )}
        </main>
      </div>
    </div>
  );
}
