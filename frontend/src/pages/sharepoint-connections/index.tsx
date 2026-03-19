import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { Cloud, Plus } from 'lucide-react';
import { getConnections } from '../../services/api';
import { getErrorMessage } from '../../lib/errors';

export default function SharePointConnectionsPage() {
  const [connections, setConnections] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    async function loadConnections() {
      try {
        const data = await getConnections();
        setConnections(data);
      } catch (err) {
        console.error(err);
        setError(getErrorMessage(err, 'Failed to load SharePoint connections'));
      } finally {
        setLoading(false);
      }
    }

    loadConnections();
  }, []);

  if (loading) {
    return <div className="p-8 text-light-text-primary dark:text-dark-text-primary">Loading SharePoint connections...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold font-secondary text-light-text-primary dark:text-dark-text-primary">
            SharePoint Connections
          </h1>
          <p className="mt-1 text-sm text-light-text-secondary dark:text-dark-text-secondary">
            Review registered Microsoft 365 tenants and create additional Graph connections.
          </p>
        </div>
        <Link
          href="/sharepoint-connections/new"
          className="inline-flex items-center gap-2 rounded-lg bg-light-primary px-4 py-2 text-white transition hover:opacity-90 dark:bg-dark-primary"
        >
          <Plus size={18} />
          <span>New Connection</span>
        </Link>
      </div>

      {error ? (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-900/60 dark:bg-red-950/40 dark:text-red-300">
          {error}
        </div>
      ) : null}

      <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-800 dark:bg-dark-surface">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-800">
          <thead className="bg-gray-50 dark:bg-gray-900/60">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">Tenant</th>
              <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">Client ID</th>
              <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-800">
            {connections.length === 0 ? (
              <tr>
                <td
                  colSpan={3}
                  className="px-6 py-12 text-center text-sm text-light-text-secondary dark:text-dark-text-secondary"
                >
                  No SharePoint connections have been registered yet.
                </td>
              </tr>
            ) : (
              connections.map((connection) => (
                <tr key={connection.id} className="hover:bg-gray-50 dark:hover:bg-gray-900/30">
                  <td className="px-6 py-4 text-sm font-medium text-light-text-primary dark:text-dark-text-primary">
                    <div className="flex items-center gap-3">
                      <div className="rounded-full bg-blue-100 p-2 text-blue-700 dark:bg-blue-950/60 dark:text-blue-300">
                        <Cloud size={16} />
                      </div>
                      <span>{connection.tenant_id}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm font-mono text-light-text-secondary dark:text-dark-text-secondary">
                    {connection.client_id}
                  </td>
                  <td className="px-6 py-4 text-sm">
                    <span
                      className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium ${
                        connection.status === 'ACTIVE'
                          ? 'bg-green-100 text-green-800 dark:bg-green-950/50 dark:text-green-300'
                          : 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300'
                      }`}
                    >
                      {connection.status}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
