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
        <Link href="/sync-definitions/new" className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
          Create New
        </Link>
      </div>

      <div className="border rounded shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Mode</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Strategy</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {defs.map((def: any) => (
              <tr key={def.id}>
                <td className="px-6 py-4 whitespace-nowrap">{def.name}</td>
                <td className="px-6 py-4 whitespace-nowrap">{def.sync_mode}</td>
                <td className="px-6 py-4 whitespace-nowrap">{def.target_strategy}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  <Link href={`/sync-definitions/${def.id}`} className="text-blue-600 hover:text-blue-900 font-medium">View & Ops</Link>
                </td>
              </tr>
            ))}
            {defs.length === 0 && (
              <tr>
                <td colSpan={4} className="px-6 py-4 text-center text-gray-500">No definitions found.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      <div className="mt-4">
        <Link href="/" className="text-blue-600 hover:underline">&larr; Back to Dashboard</Link>
      </div>
    </div>
  );
}
