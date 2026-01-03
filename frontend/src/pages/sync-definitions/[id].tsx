import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { getSyncDefinitions, generateDriftReport, triggerSync, updateSyncDefinition } from '../../services/api'; // In real app, getSyncDefinition(id)
import { AlertTriangle, CheckCircle, RefreshCw, ArrowRightLeft, ArrowRight, Play } from 'lucide-react';

export default function SyncDefinitionDetail() {
  const router = useRouter();
  const { id } = router.query;
  const [def, setDef] = useState<any>(null);
  const [activeTab, setActiveTab] = useState('configuration');
  const [report, setReport] = useState<any>(null);
  const [loadingReport, setLoadingReport] = useState(false);
  const [runningSync, setRunningSync] = useState(false);

  useEffect(() => {
    if (!id) return;
    // Mock: filtering from list because get_sync_definition endpoint exists but we can just re-use the list call for now or update service
    // Actually the service has getSyncDefinitions (plural).
    // Let's assume we can fetch it. 
    // Updating service to add getSyncDefinition(id) is better but for speed I'll filter.
    getSyncDefinitions().then(defs => {
        const found = defs.find((d: any) => d.id === id);
        setDef(found);
    }).catch(console.error);
  }, [id]);

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

  if (!def) return <div className="p-8 text-light-text-primary dark:text-dark-text-primary">Loading definition...</div>;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center border-b border-gray-200 dark:border-gray-700 pb-4">
        <div>
            <h1 className="text-2xl font-bold font-secondary text-light-text-primary dark:text-dark-text-primary">{def.name}</h1>
            <div className="flex items-center space-x-2 text-sm text-light-text-secondary dark:text-dark-text-secondary mt-1">
                <span className="font-mono">{def.id}</span>
            </div>
        </div>
        <div className="flex space-x-3">
             <button className="px-4 py-2 bg-light-surface dark:bg-dark-surface border border-gray-300 dark:border-gray-600 rounded shadow-sm text-sm font-medium text-light-text-primary dark:text-dark-text-primary hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                Edit Configuration
             </button>
             <button
                onClick={handleRunSync}
                disabled={runningSync}
                className="flex items-center space-x-2 px-4 py-2 bg-light-primary dark:bg-dark-primary text-white rounded shadow-sm text-sm font-medium hover:bg-opacity-90 disabled:opacity-50"
             >
                <Play size={16} className={runningSync ? "animate-spin" : ""} />
                <span>{runningSync ? "Running..." : "Run Sync Now"}</span>
             </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        <nav className="-mb-px flex space-x-8">
            <button
                onClick={() => setActiveTab('configuration')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${activeTab === 'configuration' ? 'border-light-accent dark:border-dark-accent text-light-primary dark:text-dark-primary' : 'border-transparent text-light-text-secondary dark:text-dark-text-secondary hover:text-light-text-primary dark:hover:text-dark-text-primary hover:border-gray-300 dark:hover:border-gray-600'}`}
            >
                Configuration
            </button>
            <button
                onClick={() => setActiveTab('ops')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${activeTab === 'ops' ? 'border-light-accent dark:border-dark-accent text-light-primary dark:text-dark-primary' : 'border-transparent text-light-text-secondary dark:text-dark-text-secondary hover:text-light-text-primary dark:hover:text-dark-text-primary hover:border-gray-300 dark:hover:border-gray-600'}`}
            >
                Operations & Drift
            </button>
        </nav>
      </div>

      {/* Content */}
      <div className="mt-6">
        {activeTab === 'configuration' && (
            <div className="grid grid-cols-2 gap-8">
                <div className="space-y-4">
                    <h3 className="text-lg font-bold text-light-text-primary dark:text-dark-text-primary">General</h3>

                    <div className="bg-light-surface dark:bg-dark-surface p-4 rounded border border-gray-200 dark:border-gray-700 shadow-sm">
                        <label className="block text-sm font-medium text-light-text-primary dark:text-dark-text-primary mb-2">Sync Mode</label>
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

                    <dl className="grid grid-cols-1 gap-x-4 gap-y-4 sm:grid-cols-2 mt-4">
                        <div className="sm:col-span-1">
                            <dt className="text-sm font-medium text-light-text-secondary dark:text-dark-text-secondary">Target Strategy</dt>
                            <dd className="mt-1 text-sm text-light-text-primary dark:text-dark-text-primary">{def.target_strategy}</dd>
                        </div>
                        <div className="sm:col-span-1">
                            <dt className="text-sm font-medium text-light-text-secondary dark:text-dark-text-secondary">Conflict Policy</dt>
                            <dd className="mt-1 text-sm text-light-text-primary dark:text-dark-text-primary">{def.conflict_policy}</dd>
                        </div>
                    </dl>
                </div>
                 <div className="space-y-4">
                    <h3 className="text-lg font-bold text-light-text-primary dark:text-dark-text-primary">Sharding Policy</h3>
                    <pre className="bg-gray-50 dark:bg-gray-800 p-4 rounded text-xs overflow-auto h-48 border border-gray-200 dark:border-gray-700 text-light-text-primary dark:text-dark-text-primary">
                        {JSON.stringify(def.sharding_policy, null, 2)}
                    </pre>
                </div>
            </div>
        )}

        {activeTab === 'ops' && (
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
      </div>
    </div>
  );
}
