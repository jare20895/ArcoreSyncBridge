import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { getDatabaseInstances, getConnections, getSyncDefinitions, getSystemCounts, getSyncRuns } from '../services/api';
import { Activity, Database, AlertTriangle, Layers, BarChart, GitBranch, Grid, Network, Settings, List, FileText } from 'lucide-react';
import MermaidDiagram from '../components/diagrams/MermaidDiagram';
import AllSyncsGridView from '../components/diagrams/AllSyncsGridView';
import InteractiveFlowDiagram from '../components/diagrams/InteractiveFlowDiagram';
import CdcHealthWidget from '../components/CdcHealthWidget';
import CdcManagement from '../components/CdcManagement';
import SystemSnapshot from '../components/SystemSnapshot';
import DriftMetricsWidget from '../components/DriftMetricsWidget';
import { generateAllSyncsMermaid } from '../lib/generateAllSyncsMermaid';

export default function Dashboard() {
  const router = useRouter();
  const [dbs, setDbs] = useState([]);
  const [conns, setConns] = useState([]);
  const [diagramView, setDiagramView] = useState<'single' | 'grid' | 'interactive'>('single');
  const [syncDefs, setSyncDefs] = useState([]);
  const [counts, setCounts] = useState<any>(null);
  const [activeSection, setActiveSection] = useState('overview');
  const [syncRuns, setSyncRuns] = useState<any[]>([]);

  // Get active section from URL hash (client-side only)
  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.slice(1) || 'overview';
      setActiveSection(hash);
    };

    // Set initial section
    handleHashChange();

    // Listen for hash changes
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  useEffect(() => {
    getDatabaseInstances().then(setDbs).catch(console.error);
    getConnections().then(setConns).catch(console.error);
    getSyncDefinitions().then(setSyncDefs).catch(console.error);
    getSystemCounts().then(setCounts).catch(console.error);
    getSyncRuns().then(setSyncRuns).catch(console.error);
  }, []);

  return (
    <div className="space-y-8">
      {/* Overview Section */}
      {activeSection === 'overview' && (
      <>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-secondary font-bold text-gray-900 dark:text-gray-100">Dashboard Overview</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">System status and key metrics</p>
        </div>
        <div className="flex items-center space-x-2 text-sm">
          <div className="px-3 py-1.5 rounded-full bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 font-medium">
            ● Live
          </div>
        </div>
      </div>
      <div className="space-y-8">

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* System Resources - Combined Card */}
        <div className="bg-white dark:bg-dark-surface p-6 rounded-lg border border-gray-200 dark:border-gray-800 shadow-sm">
            <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-4 uppercase tracking-wide">System Resources</h3>
            <div className="grid grid-cols-3 gap-4">
                <div className="text-center">
                    <div className="flex justify-center mb-2">
                        <div className="p-2 bg-blue-500/10 rounded-lg text-blue-600 dark:text-blue-400">
                            <Database size={20} />
                        </div>
                    </div>
                    <p className="text-2xl font-bold font-mono text-gray-900 dark:text-gray-100">{counts?.source_tables || 0}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Source Tables</p>
                </div>
                <div className="text-center">
                    <div className="flex justify-center mb-2">
                        <div className="p-2 bg-purple-500/10 rounded-lg text-purple-600 dark:text-purple-400">
                            <Layers size={20} />
                        </div>
                    </div>
                    <p className="text-2xl font-bold font-mono text-gray-900 dark:text-gray-100">{counts?.applications || 0}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Applications</p>
                </div>
                <div className="text-center">
                    <div className="flex justify-center mb-2">
                        <div className="p-2 bg-orange-500/10 rounded-lg text-orange-600 dark:text-orange-400">
                            <FileText size={20} />
                        </div>
                    </div>
                    <p className="text-2xl font-bold font-mono text-gray-900 dark:text-gray-100">{counts?.instances || 0}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">DB Instances</p>
                </div>
            </div>
        </div>

        {/* SharePoint Lists - Enhanced Card */}
        <div className="bg-white dark:bg-dark-surface p-6 rounded-lg border border-gray-200 dark:border-gray-800 shadow-sm">
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-3">
                    <div className="p-2 bg-green-500/10 rounded-lg text-green-600 dark:text-green-400">
                        <List size={20} />
                    </div>
                    <div>
                        <p className="text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wide">SharePoint Lists</p>
                        <p className="text-2xl font-bold font-mono text-gray-900 dark:text-gray-100">{counts?.sharepoint_lists?.inventory || 0}</p>
                    </div>
                </div>
            </div>
            <div className="grid grid-cols-2 gap-3 pt-3 border-t border-gray-100 dark:border-gray-700">
                <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 rounded-full bg-teal-500"></div>
                    <div className="flex-1">
                        <p className="text-xs text-gray-500 dark:text-gray-400">Provisioned</p>
                        <p className="text-lg font-bold font-mono text-gray-900 dark:text-gray-100">{counts?.sharepoint_lists?.provisioned || 0}</p>
                    </div>
                </div>
                <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 rounded-full bg-red-500"></div>
                    <div className="flex-1">
                        <p className="text-xs text-gray-500 dark:text-gray-400">Deleted</p>
                        <p className="text-lg font-bold font-mono text-gray-900 dark:text-gray-100">{counts?.sharepoint_lists?.deleted || 0}</p>
                    </div>
                </div>
            </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Column: System Snapshot & Runs */}
        <div className="lg:col-span-2 space-y-8">
            {/* System Snapshot */}
            <SystemSnapshot />

             <div className="bg-white dark:bg-dark-surface rounded-lg border border-gray-200 dark:border-gray-800 shadow-sm overflow-hidden">
                <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-800 flex justify-between items-center bg-gray-50 dark:bg-gray-900/50">
                    <h3 className="text-lg font-bold font-secondary text-gray-900 dark:text-gray-100">Recent Runs</h3>
                    <Link href="/runs" className="text-sm text-light-primary dark:text-dark-primary hover:underline font-medium">View All →</Link>
                </div>
                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                    <thead className="bg-gray-50 dark:bg-gray-900/50">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider">Sync Def</th>
                            <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider">Type</th>
                            <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider">Status</th>
                            <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider">Items</th>
                            <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider">Duration</th>
                            <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 dark:text-gray-300 uppercase tracking-wider">Time</th>
                        </tr>
                    </thead>
                    <tbody className="bg-white dark:bg-dark-surface divide-y divide-gray-200 dark:divide-gray-800">
                         {syncRuns.length === 0 ? (
                           <tr>
                             <td colSpan={6} className="px-6 py-8 text-center text-sm text-gray-500">No sync runs yet</td>
                           </tr>
                         ) : (
                           syncRuns.slice(0, 10).map((run: any) => {
                             const syncDef = syncDefs.find((def: any) => def.id === run.sync_def_id);
                             const duration = run.end_time
                               ? Math.round((new Date(run.end_time).getTime() - new Date(run.start_time).getTime()) / 1000)
                               : null;
                             const timeAgo = (() => {
                               const now = new Date();
                               const start = new Date(run.start_time);
                               const diffMs = now.getTime() - start.getTime();
                               const diffMins = Math.floor(diffMs / 60000);
                               const diffHours = Math.floor(diffMs / 3600000);
                               const diffDays = Math.floor(diffMs / 86400000);

                               if (diffMins < 1) return 'Just now';
                               if (diffMins < 60) return `${diffMins} min${diffMins > 1 ? 's' : ''} ago`;
                               if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
                               return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
                             })();

                             const statusColor = run.status === 'COMPLETED' ? 'light-success'
                               : run.status === 'FAILED' ? 'light-danger'
                               : run.status === 'RUNNING' ? 'light-warning'
                               : 'gray-500';

                             return (
                               <tr key={run.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
                                 <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-gray-100">
                                   {syncDef?.name || 'Unknown Sync'}
                                 </td>
                                 <td className="px-6 py-4 whitespace-nowrap text-xs text-gray-500 dark:text-gray-400">
                                   {run.run_type}
                                 </td>
                                 <td className="px-6 py-4 whitespace-nowrap">
                                   <span className={`px-2 py-1 rounded-full bg-${statusColor}/20 text-${statusColor} text-xs font-bold`}>
                                     {run.status}
                                   </span>
                                 </td>
                                 <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">
                                   {run.items_processed}{run.items_failed > 0 ? ` (${run.items_failed} failed)` : ''}
                                 </td>
                                 <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">
                                   {duration !== null ? `${duration}s` : '-'}
                                 </td>
                                 <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                                   {timeAgo}
                                 </td>
                               </tr>
                             );
                           })
                         )}
                    </tbody>
                </table>
            </div>
        </div>

        {/* Right Column: Status & Quick Actions */}
        <div className="space-y-8">
            {/* CDC Health Widget */}
            <CdcHealthWidget />

            {/* Drift Metrics Widget */}
            <DriftMetricsWidget />

             <div className="bg-white dark:bg-dark-surface rounded-lg border border-gray-200 dark:border-gray-800 shadow-sm p-6">
                <h3 className="text-lg font-bold font-secondary mb-4 text-gray-900 dark:text-gray-100">Quick Actions</h3>
                <div className="space-y-3">
                    <Link href="/database-instances/new" className="block w-full text-center py-2.5 px-4 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                        Register Database
                    </Link>
                    <Link href="/sharepoint-connections/new" className="block w-full text-center py-2.5 px-4 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                        Add Connection
                    </Link>
                    <Link href="/sync-definitions/new" className="block w-full text-center py-2.5 px-4 bg-light-primary dark:bg-dark-primary text-white rounded-md shadow-sm text-sm font-medium hover:bg-opacity-90 dark:hover:bg-opacity-90 transition-all transform hover:scale-[1.02]">
                        New Sync Definition
                    </Link>
                </div>
            </div>

            <div className="bg-white dark:bg-dark-surface rounded-lg border border-gray-200 dark:border-gray-800 shadow-sm p-6">
                <h3 className="text-lg font-bold font-secondary mb-2 text-gray-900 dark:text-gray-100">Recent Issues</h3>
                <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">Failed or problematic sync runs</p>
                <ul className="space-y-3">
                     {(() => {
                       const failedRuns = syncRuns.filter((run: any) => run.status === 'FAILED' || run.items_failed > 0).slice(0, 5);

                       if (failedRuns.length === 0) {
                         return (
                           <li className="text-sm text-gray-500 text-center py-4">
                             <span className="text-green-600 dark:text-green-400">✓ No issues found</span>
                           </li>
                         );
                       }

                       return failedRuns.map((run: any) => {
                         const syncDef = syncDefs.find((def: any) => def.id === run.sync_def_id);
                         const timeAgo = (() => {
                           const now = new Date();
                           const start = new Date(run.start_time);
                           const diffMs = now.getTime() - start.getTime();
                           const diffMins = Math.floor(diffMs / 60000);
                           const diffHours = Math.floor(diffMs / 3600000);

                           if (diffMins < 1) return 'Just now';
                           if (diffMins < 60) return `${diffMins} min${diffMins > 1 ? 's' : ''} ago`;
                           return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
                         })();

                         return (
                           <li key={run.id} className="flex flex-col text-sm border-b border-gray-100 dark:border-gray-700 pb-2">
                             <div className="flex justify-between items-start mb-1">
                               <span className="font-medium text-gray-700 dark:text-gray-300">{syncDef?.name || 'Unknown Sync'}</span>
                               <span className="text-light-danger font-bold text-xs">{run.status}</span>
                             </div>
                             <div className="flex justify-between items-center text-xs text-gray-500">
                               <span>{run.items_failed > 0 ? `${run.items_failed} items failed` : run.error_message?.substring(0, 40) || 'Error'}</span>
                               <span>{timeAgo}</span>
                             </div>
                           </li>
                         );
                       });
                     })()}
                </ul>
                <Link href="/runs" className="mt-4 block w-full text-center text-sm text-light-primary hover:underline">
                  View All Runs
                </Link>
            </div>
        </div>

      </div>
      </div>
      </>
      )}

      {/* Diagrams Section */}
      {activeSection === 'diagrams' && (
        <>
        <div>
          <h1 className="text-3xl font-secondary font-bold text-light-text-primary dark:text-dark-text-primary">Sync Diagrams</h1>
          <p className="text-light-text-secondary dark:text-dark-text-secondary mt-1">Visual data flow representations.</p>
        </div>
        <div className="space-y-6">
          {/* Debug Info */}
          {syncDefs.some((def: any) => (!def.source_table_name && !def.source_table_name_resolved) || !def.target_list_name) && (
            <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-700 rounded p-4">
              <h4 className="font-bold text-yellow-800 dark:text-yellow-200 mb-2">⚠️ Warning: Incomplete Sync Definitions</h4>
              <p className="text-sm text-yellow-700 dark:text-yellow-300 mb-2">
                Some sync definitions are missing source or target information:
              </p>
              <div className="text-xs font-mono space-y-1 max-h-40 overflow-y-auto">
                {syncDefs.filter((def: any) => (!def.source_table_name && !def.source_table_name_resolved) || !def.target_list_name).map((def: any) => (
                  <div key={def.id} className="text-yellow-700 dark:text-yellow-300">
                    • {def.name} (ID: {def.id.substring(0, 8)}...):
                    {!def.source_table_name && !def.source_table_name_resolved && <span className="ml-2 text-red-600 dark:text-red-400">Missing source table (source_table_id may be invalid)</span>}
                    {!def.target_list_name && <span className="ml-2 text-red-600 dark:text-red-400">Missing target_list_name (target_list_id may be null or invalid)</span>}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* View Selector */}
          <div className="bg-white dark:bg-dark-surface p-4 rounded border border-gray-200 dark:border-gray-700">
            <div className="flex items-center space-x-4">
              <span className="font-medium text-sm text-light-text-primary dark:text-dark-text-primary">
                View Mode:
              </span>
              <button
                onClick={() => setDiagramView('single')}
                className={`flex items-center space-x-2 px-4 py-2 rounded transition-colors ${
                  diagramView === 'single'
                    ? 'bg-light-primary dark:bg-dark-primary text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
              >
                <GitBranch size={16} />
                <span>Single Diagram</span>
              </button>
              <button
                onClick={() => setDiagramView('grid')}
                className={`flex items-center space-x-2 px-4 py-2 rounded transition-colors ${
                  diagramView === 'grid'
                    ? 'bg-light-primary dark:bg-dark-primary text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
              >
                <Grid size={16} />
                <span>Grid View</span>
              </button>
              <button
                onClick={() => setDiagramView('interactive')}
                className={`flex items-center space-x-2 px-4 py-2 rounded transition-colors ${
                  diagramView === 'interactive'
                    ? 'bg-light-primary dark:bg-dark-primary text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
              >
                <Network size={16} />
                <span>Interactive</span>
              </button>
            </div>
          </div>

          {/* Option A: Single Large Diagram */}
          {diagramView === 'single' && (
            <div className="bg-white dark:bg-dark-surface p-6 rounded border border-gray-200 dark:border-gray-700 shadow-sm">
              <h3 className="text-lg font-bold mb-4 text-light-text-primary dark:text-dark-text-primary">
                All Sync Definitions
              </h3>
              <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary mb-4">
                Top-to-bottom flow showing all sync definitions from source databases to target lists
              </p>
              <div className="overflow-x-auto">
                <MermaidDiagram
                  chart={generateAllSyncsMermaid(syncDefs)}
                  className="min-h-[500px]"
                />
              </div>
            </div>
          )}

          {/* Option B: Grid View */}
          {diagramView === 'grid' && (
            <div>
              <div className="mb-4">
                <h3 className="text-lg font-bold text-light-text-primary dark:text-dark-text-primary">
                  Grid View
                </h3>
                <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary">
                  Click any card to navigate to the sync definition detail page
                </p>
              </div>
              <AllSyncsGridView syncDefinitions={syncDefs} />
            </div>
          )}

          {/* Option C: Interactive React Flow */}
          {diagramView === 'interactive' && (
            <div>
              <div className="mb-4">
                <h3 className="text-lg font-bold text-light-text-primary dark:text-dark-text-primary">
                  Interactive Diagram
                </h3>
                <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary">
                  Interactive flow diagram with filtering, zoom, and pan capabilities
                </p>
              </div>
              <InteractiveFlowDiagram syncDefinitions={syncDefs} />
            </div>
          )}
        </div>
        </>
      )}

      {/* CDC Management Section */}
      {activeSection === 'cdc' && (
        <>
        <div>
          <h1 className="text-3xl font-secondary font-bold text-light-text-primary dark:text-dark-text-primary">CDC Management</h1>
          <p className="text-light-text-secondary dark:text-dark-text-secondary mt-1">Change Data Capture health and operations.</p>
        </div>
        <div className="space-y-6">
          <CdcManagement />
        </div>
        </>
      )}

      {/* System Metrics Section */}
      {activeSection === 'metrics' && (
        <>
        <div>
          <h1 className="text-3xl font-secondary font-bold text-light-text-primary dark:text-dark-text-primary">System Metrics</h1>
          <p className="text-light-text-secondary dark:text-dark-text-secondary mt-1">Performance analysis and resource monitoring.</p>
        </div>
        <div className="space-y-6">
          <SystemSnapshot />
        </div>
        </>
      )}
    </div>
  );
}