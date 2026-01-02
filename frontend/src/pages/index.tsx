import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { getDatabaseInstances, getConnections } from '../services/api';
import { Activity, Database, AlertTriangle, Layers } from 'lucide-react';

export default function Dashboard() {
  const [dbs, setDbs] = useState([]);
  const [conns, setConns] = useState([]);

  useEffect(() => {
    getDatabaseInstances().then(setDbs).catch(console.error);
    getConnections().then(setConns).catch(console.error);
  }, []);

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-secondary font-bold text-light-text-primary dark:text-dark-text-primary">Overview</h1>
        <p className="text-light-text-secondary dark:text-dark-text-secondary mt-1">System status and key performance indicators.</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white dark:bg-dark-surface p-6 rounded-lg border border-gray-200 dark:border-gray-800 shadow-sm flex items-center space-x-4">
            <div className="p-3 bg-light-primary/10 rounded-full text-light-primary">
                <Activity size={24} />
            </div>
            <div>
                <p className="text-sm text-light-text-secondary font-medium">Throughput (1h)</p>
                <p className="text-2xl font-bold font-mono">1,240</p>
            </div>
        </div>
        <div className="bg-white dark:bg-dark-surface p-6 rounded-lg border border-gray-200 dark:border-gray-800 shadow-sm flex items-center space-x-4">
            <div className="p-3 bg-light-success/10 rounded-full text-light-success">
                <Database size={24} />
            </div>
            <div>
                <p className="text-sm text-light-text-secondary font-medium">Active DBs</p>
                <p className="text-2xl font-bold font-mono">{dbs.length}</p>
            </div>
        </div>
        <div className="bg-white dark:bg-dark-surface p-6 rounded-lg border border-gray-200 dark:border-gray-800 shadow-sm flex items-center space-x-4">
            <div className="p-3 bg-light-warning/10 rounded-full text-light-warning">
                <AlertTriangle size={24} />
            </div>
            <div>
                <p className="text-sm text-light-text-secondary font-medium">Drift Alerts</p>
                <p className="text-2xl font-bold font-mono">3</p>
            </div>
        </div>
        <div className="bg-white dark:bg-dark-surface p-6 rounded-lg border border-gray-200 dark:border-gray-800 shadow-sm flex items-center space-x-4">
            <div className="p-3 bg-gray-100 rounded-full text-gray-600">
                <Layers size={24} />
            </div>
            <div>
                <p className="text-sm text-light-text-secondary font-medium">Queue Depth</p>
                <p className="text-2xl font-bold font-mono">12</p>
            </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Column: Throughput & Runs */}
        <div className="lg:col-span-2 space-y-8">
            <div className="bg-white dark:bg-dark-surface rounded-lg border border-gray-200 dark:border-gray-800 shadow-sm p-6">
                <h3 className="text-lg font-bold font-secondary mb-4">Throughput Trend</h3>
                <div className="h-64 bg-gray-50 dark:bg-gray-900 rounded flex items-center justify-center text-gray-400">
                    [Chart Placeholder: Time Series]
                </div>
            </div>

             <div className="bg-white dark:bg-dark-surface rounded-lg border border-gray-200 dark:border-gray-800 shadow-sm overflow-hidden">
                <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-800 flex justify-between items-center">
                    <h3 className="text-lg font-bold font-secondary">Recent Runs</h3>
                    <Link href="/runs" className="text-sm text-light-primary hover:underline">View All</Link>
                </div>
                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-800">
                    <thead className="bg-gray-50 dark:bg-gray-900">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Sync Def</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Duration</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Time</th>
                        </tr>
                    </thead>
                    <tbody className="bg-white dark:bg-dark-surface divide-y divide-gray-200 dark:divide-gray-800">
                         <tr>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">Main Inventory Sync</td>
                            <td className="px-6 py-4 whitespace-nowrap"><span className="px-2 py-1 rounded-full bg-light-success/20 text-light-success text-xs font-bold">SUCCESS</span></td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">12s</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">2 mins ago</td>
                         </tr>
                         <tr>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">Employee Roster</td>
                            <td className="px-6 py-4 whitespace-nowrap"><span className="px-2 py-1 rounded-full bg-light-warning/20 text-light-warning text-xs font-bold">WARNING</span></td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">45s</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">1 hour ago</td>
                         </tr>
                    </tbody>
                </table>
            </div>
        </div>

        {/* Right Column: Status & Quick Actions */}
        <div className="space-y-8">
             <div className="bg-white dark:bg-dark-surface rounded-lg border border-gray-200 dark:border-gray-800 shadow-sm p-6">
                <h3 className="text-lg font-bold font-secondary mb-4">Quick Actions</h3>
                <div className="space-y-3">
                    <Link href="/database-instances/new" className="block w-full text-center py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50">
                        Register Database
                    </Link>
                    <Link href="/sharepoint-connections/new" className="block w-full text-center py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50">
                        Add Connection
                    </Link>
                    <Link href="/sync-definitions/new" className="block w-full text-center py-2 px-4 bg-light-primary text-white rounded-md shadow-sm text-sm font-medium hover:bg-opacity-90">
                        New Sync Definition
                    </Link>
                </div>
            </div>

            <div className="bg-white dark:bg-dark-surface rounded-lg border border-gray-200 dark:border-gray-800 shadow-sm p-6">
                <h3 className="text-lg font-bold font-secondary mb-4">Drift Summary</h3>
                <p className="text-sm text-gray-500 mb-4">Items found in Ledger but missing in SharePoint.</p>
                <ul className="space-y-3">
                     <li className="flex justify-between items-center text-sm border-b pb-2">
                        <span className="font-mono text-gray-600">ID: 48102</span>
                        <span className="text-light-danger font-bold">Missing</span>
                     </li>
                     <li className="flex justify-between items-center text-sm border-b pb-2">
                        <span className="font-mono text-gray-600">ID: 99123</span>
                        <span className="text-light-danger font-bold">Missing</span>
                     </li>
                </ul>
                <button className="mt-4 w-full text-sm text-light-primary hover:underline">View Full Report</button>
            </div>
        </div>

      </div>
    </div>
  );
}