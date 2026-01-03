import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { getSyncDefinitions, deleteSyncDefinition } from '../../services/api';
import { Trash } from 'lucide-react';

export default function SyncDefinitionsList() {
  const [defs, setDefs] = useState([]);

  const loadDefinitions = () => {
      getSyncDefinitions().then(setDefs).catch(console.error);
  };

  useEffect(() => {
    loadDefinitions();
  }, []);

  const handleDelete = async (id: string) => {
      if (confirm('Are you sure you want to delete this sync definition? This action cannot be undone.')) {
          try {
              await deleteSyncDefinition(id);
              loadDefinitions();
          } catch (e) {
              console.error(e);
              alert('Failed to delete definition');
          }
      }
  };

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
              <th className="px-6 py-3 text-left text-xs font-medium text-light-text-secondary dark:text-dark-text-secondary uppercase tracking-wider">Source</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-light-text-secondary dark:text-dark-text-secondary uppercase tracking-wider">Target</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-light-text-secondary dark:text-dark-text-secondary uppercase tracking-wider">Mode</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-light-text-secondary dark:text-dark-text-secondary uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody className="bg-light-surface dark:bg-dark-surface divide-y divide-gray-200 dark:divide-gray-800">
            {defs.map((def: any) => (
              <tr key={def.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/60 transition-colors">
                <td className="px-6 py-4 whitespace-nowrap text-light-text-primary dark:text-dark-text-primary font-medium">{def.name}</td>
                <td className="px-6 py-4 whitespace-nowrap text-light-text-secondary dark:text-dark-text-secondary text-sm">
                    {def.source_table_name_resolved || def.source_table_name || 'Unknown Source'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-light-text-secondary dark:text-dark-text-secondary text-sm">
                    {def.target_list_name || 'Unknown Target'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-light-text-secondary dark:text-dark-text-secondary text-sm">
                    <span className={`px-2 py-1 rounded text-xs ${def.sync_mode === 'TWO_WAY' ? 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300' : 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300'}`}>
                        {def.sync_mode === 'TWO_WAY' ? 'Two-Way' : 'Push'}
                    </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm flex items-center space-x-4">
                  <Link href={`/sync-definitions/${def.id}`} className="text-light-primary dark:text-dark-primary hover:opacity-80 font-medium">Manage</Link>
                  <button onClick={() => handleDelete(def.id)} className="text-red-600 dark:text-red-400 hover:opacity-80">
                      <Trash size={16} />
                  </button>
                </td>
              </tr>
            ))}
            {defs.length === 0 && (
              <tr>
                <td colSpan={5} className="px-6 py-4 text-center text-light-text-secondary dark:text-dark-text-secondary">No definitions found.</td>
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
