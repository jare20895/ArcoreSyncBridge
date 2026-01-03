import React, { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import { getSyncRuns } from '../services/api';
import { Activity, CheckCircle, XCircle, Clock } from 'lucide-react';

export default function RunsPage() {
  const [runs, setRuns] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchRuns();
    const interval = setInterval(fetchRuns, 5000); // Auto refresh
    return () => clearInterval(interval);
  }, []);

  const fetchRuns = async () => {
    try {
      const data = await getSyncRuns();
      setRuns(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout>
      <div className="max-w-6xl mx-auto">
        <h1 className="text-2xl font-bold font-secondary text-gray-900 dark:text-white mb-6 flex items-center">
            <Activity className="mr-3 text-light-primary" />
            Run History & Ledger
        </h1>

        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead className="bg-gray-50 dark:bg-gray-900">
                    <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Run ID</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Sync Definition</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Start Time</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Duration</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Items</th>
                    </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                    {runs.map(run => {
                        const start = new Date(run.start_time);
                        const end = run.end_time ? new Date(run.end_time) : null;
                        const duration = end ? ((end.getTime() - start.getTime()) / 1000).toFixed(1) + 's' : '-';
                        
                        return (
                            <tr key={run.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
                                <td className="px-6 py-4 whitespace-nowrap text-xs font-mono text-gray-500">{run.id.substring(0, 8)}...</td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100 font-medium">{run.sync_def_id.substring(0, 8)}...</td>
                                <td className="px-6 py-4 whitespace-nowrap text-xs font-bold text-gray-600 dark:text-gray-400">{run.run_type}</td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                        run.status === 'COMPLETED' ? 'bg-green-100 text-green-800' :
                                        run.status === 'FAILED' ? 'bg-red-100 text-red-800' :
                                        'bg-blue-100 text-blue-800'
                                    }`}>
                                        {run.status === 'COMPLETED' && <CheckCircle size={12} className="mr-1"/>}
                                        {run.status === 'FAILED' && <XCircle size={12} className="mr-1"/>}
                                        {run.status === 'RUNNING' && <Clock size={12} className="mr-1 animate-pulse"/>}
                                        {run.status}
                                    </span>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{start.toLocaleString()}</td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{duration}</td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                                    {run.items_processed} <span className="text-gray-400 text-xs">processed</span>
                                    {run.items_failed > 0 && <span className="text-red-500 ml-2">({run.items_failed} failed)</span>}
                                </td>
                            </tr>
                        );
                    })}
                    {runs.length === 0 && !loading && (
                        <tr>
                            <td colSpan={7} className="px-6 py-12 text-center text-gray-500">No run history available.</td>
                        </tr>
                    )}
                </tbody>
            </table>
        </div>
      </div>
    </Layout>
  );
}
