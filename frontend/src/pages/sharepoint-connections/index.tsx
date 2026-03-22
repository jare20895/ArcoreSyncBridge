import React, { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { Cloud, Plus } from 'lucide-react';
import { getConnectionsPage } from '../../services/api';
import { FilterToolbar } from '../../components/ui/FilterToolbar';
import { ListPagination } from '../../components/ui/ListPagination';
import { getErrorMessage } from '../../lib/errors';

const PAGE_SIZE = 20;

export default function SharePointConnectionsPage() {
  const [connections, setConnections] = useState<any[]>([]);
  const [meta, setMeta] = useState<{ total?: number; offset?: number }>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [page, setPage] = useState(0);

  const loadConnections = useCallback(async () => {
    setLoading(true);
    try {
      const response = await getConnectionsPage({
        q: search || undefined,
        status: statusFilter || undefined,
        offset: page * PAGE_SIZE,
        limit: PAGE_SIZE,
      });
      setConnections(response.data);
      setMeta(response.meta ?? {});
      setError('');
    } catch (err) {
      console.error(err);
      setError(getErrorMessage(err, 'Failed to load SharePoint connections'));
    } finally {
      setLoading(false);
    }
  }, [page, search, statusFilter]);

  useEffect(() => {
    void loadConnections();
  }, [loadConnections]);

  const hasPrevious = page > 0;
  const hasNext = (meta.offset ?? 0) + connections.length < (meta.total ?? connections.length);

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

      <FilterToolbar className="md:grid-cols-[minmax(0,1fr)_220px]">
        <input
          value={search}
          onChange={(event) => {
            setPage(0);
            setSearch(event.target.value);
          }}
          placeholder="Search tenant, hostname, or client ID"
          className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-light-text-primary dark:border-gray-700 dark:bg-gray-900 dark:text-dark-text-primary"
        />
        <select
          value={statusFilter}
          onChange={(event) => {
            setPage(0);
            setStatusFilter(event.target.value);
          }}
          className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-light-text-primary dark:border-gray-700 dark:bg-gray-900 dark:text-dark-text-primary"
        >
          <option value="">All statuses</option>
          <option value="ACTIVE">ACTIVE</option>
          <option value="DISABLED">DISABLED</option>
        </select>
      </FilterToolbar>

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
        <ListPagination
          offset={meta.offset}
          total={meta.total}
          count={connections.length}
          hasPrevious={hasPrevious}
          hasNext={hasNext}
          onPrevious={() => setPage((current) => Math.max(0, current - 1))}
          onNext={() => setPage((current) => current + 1)}
          className="border-t border-gray-200 dark:border-gray-800"
        />
      </div>
    </div>
  );
}
