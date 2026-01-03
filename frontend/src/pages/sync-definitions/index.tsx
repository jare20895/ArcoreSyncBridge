import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { getSyncDefinitions } from '../../services/api';

export default function SyncDefinitionsList() {
  const [defs, setDefs] = useState([]);

  useEffect(() => {
    getSyncDefinitions().then(setDefs).catch(console.error);
  }, []);

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Sync Definitions</h1>
        <Link
          href="/sync-definitions/new"
          className="bg-light-primary dark:bg-dark-primary text-white px-4 py-2 rounded hover:opacity-90 transition-colors"
        >
          Create New
        </Link>
      </div>

      <div className="border border-gray-200 dark:border-gray-800 rounded shadow-sm overflow-hidden bg-light-surface dark:bg-dark-surface">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-800">
          <thead className="bg-gray-50 dark:bg-gray-900/40">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-light-text-secondary dark:text-dark-text-secondary uppercase tracking-wider">Name</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-light-text-secondary dark:text-dark-text-secondary uppercase tracking-wider">Mode</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-light-text-secondary dark:text-dark-text-secondary uppercase tracking-wider">Strategy</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-light-text-secondary dark:text-dark-text-secondary uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody className="bg-light-surface dark:bg-dark-surface divide-y divide-gray-200 dark:divide-gray-800">
            {defs.map((def: any) => (
              <tr key={def.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/60 transition-colors">
                <td className="px-6 py-4 whitespace-nowrap text-light-text-primary dark:text-dark-text-primary">{def.name}</td>
                <td className="px-6 py-4 whitespace-nowrap text-light-text-secondary dark:text-dark-text-secondary">{def.sync_mode}</td>
                <td className="px-6 py-4 whitespace-nowrap text-light-text-secondary dark:text-dark-text-secondary">{def.target_strategy}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  <Link href={`/sync-definitions/${def.id}`} className="text-light-primary dark:text-dark-primary hover:opacity-80 font-medium">View & Ops</Link>
                </td>
              </tr>
            ))}
            {defs.length === 0 && (
              <tr>
                <td colSpan={4} className="px-6 py-4 text-center text-light-text-secondary dark:text-dark-text-secondary">No definitions found.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      <div className="mt-4">
        <Link href="/" className="text-light-primary dark:text-dark-primary hover:underline">&larr; Back to Dashboard</Link>
      </div>
    </div>
  );
}
