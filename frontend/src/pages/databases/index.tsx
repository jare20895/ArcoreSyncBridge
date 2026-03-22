import React, { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { Plus, Edit, Trash2 } from 'lucide-react';
import { getDatabasesPage, deleteDatabase, getApplications } from '../../services/api';
import { useToast } from '../../components/ui/ToastProvider';
import { useConfirmDialog } from '../../components/ui/ConfirmDialogProvider';
import { getErrorMessage } from '../../lib/errors';

const PAGE_SIZE = 20;

export default function DatabasesPage() {
  const { showToast } = useToast();
  const { confirm } = useConfirmDialog();
  const [databases, setDatabases] = useState<any[]>([]);
  const [meta, setMeta] = useState<{ total?: number; offset?: number }>({});
  const [applications, setApplications] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [environmentFilter, setEnvironmentFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [page, setPage] = useState(0);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [dbResponse, appData] = await Promise.all([
        getDatabasesPage({
          q: search || undefined,
          environment: environmentFilter || undefined,
          status: statusFilter || undefined,
          offset: page * PAGE_SIZE,
          limit: PAGE_SIZE,
        }),
        getApplications()
      ]);
      setDatabases(dbResponse.data);
      setMeta(dbResponse.meta ?? {});
      setError('');

      // Create a map of applications by ID for easy lookup
      const appMap = appData.reduce((acc: Record<string, any>, app: any) => {
        acc[app.id] = app;
        return acc;
      }, {});
      setApplications(appMap);
    } catch (err) {
      console.error(err);
      setError('Failed to load databases');
    } finally {
      setLoading(false);
    }
  }, [environmentFilter, page, search, statusFilter]);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  const handleDelete = async (id: string, name: string) => {
    const confirmed = await confirm({
      title: 'Delete database?',
      description: `Delete "${name}" and all associated database instances.`,
      confirmLabel: 'Delete database',
      tone: 'danger'
    });
    if (!confirmed) {
      return;
    }

    try {
      await deleteDatabase(id);
      showToast({
        title: 'Database deleted',
        description: `${name} was removed successfully.`,
        variant: 'success'
      });
      void loadData();
    } catch (err: any) {
      showToast({
        title: 'Delete failed',
        description: getErrorMessage(err, 'Failed to delete database'),
        variant: 'error'
      });
    }
  };

  if (loading) {
    return (
      <div className="p-8">
        <div className="text-light-text-primary dark:text-dark-text-primary">Loading...</div>
      </div>
    );
  }

  const hasPrevious = page > 0;
  const hasNext = (meta.offset ?? 0) + databases.length < (meta.total ?? databases.length);

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-light-text-primary dark:text-dark-text-primary">Databases</h1>
          <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary mt-1">
            Manage logical database definitions
          </p>
        </div>
        <Link
          href="/databases/new"
          className="flex items-center space-x-2 px-4 py-2 bg-light-primary dark:bg-dark-primary text-white rounded hover:opacity-90 transition-opacity"
        >
          <Plus size={20} />
          <span>New Database</span>
        </Link>
      </div>

      {error && <div className="bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 p-3 rounded mb-4">{error}</div>}

      <div className="mb-4 grid gap-3 lg:grid-cols-[minmax(0,1fr)_180px_180px]">
        <input
          value={search}
          onChange={(event) => {
            setPage(0);
            setSearch(event.target.value);
          }}
          placeholder="Search name or database name"
          className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-light-text-primary dark:border-gray-700 dark:bg-gray-900 dark:text-dark-text-primary"
        />
        <select
          value={environmentFilter}
          onChange={(event) => {
            setPage(0);
            setEnvironmentFilter(event.target.value);
          }}
          className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-light-text-primary dark:border-gray-700 dark:bg-gray-900 dark:text-dark-text-primary"
        >
          <option value="">All environments</option>
          <option value="DEV">DEV</option>
          <option value="STAGING">STAGING</option>
          <option value="PROD">PROD</option>
        </select>
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
      </div>

      <div className="bg-light-surface dark:bg-dark-surface border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50 dark:bg-gray-800">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Name</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Application</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Type</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Environment</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Database Name</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Status</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {databases.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-6 py-8 text-center text-light-text-secondary dark:text-dark-text-secondary">
                  No databases found. Create your first database to get started.
                </td>
              </tr>
            ) : (
              databases.map((db) => (
                <tr key={db.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                  <td className="px-6 py-4">
                    <Link href={`/databases/${db.id}`} className="text-light-primary dark:text-dark-primary hover:underline font-medium">
                      {db.name}
                    </Link>
                  </td>
                  <td className="px-6 py-4 text-sm text-light-text-primary dark:text-dark-text-primary">
                    {applications[db.application_id]?.name || '-'}
                  </td>
                  <td className="px-6 py-4 text-sm text-light-text-primary dark:text-dark-text-primary">
                    {db.db_type}
                  </td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      db.environment === 'PROD'
                        ? 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300'
                        : db.environment === 'STAGING'
                        ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300'
                        : 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300'
                    }`}>
                      {db.environment}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-light-text-primary dark:text-dark-text-primary font-mono">
                    {db.database_name}
                  </td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      db.status === 'ACTIVE'
                        ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300'
                        : 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300'
                    }`}>
                      {db.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right text-sm">
                    <div className="flex items-center justify-end space-x-3">
                      <Link href={`/databases/${db.id}/edit`} className="text-light-primary dark:text-dark-primary hover:underline flex items-center space-x-1">
                        <Edit size={14} />
                        <span>Edit</span>
                      </Link>
                      <button
                        onClick={() => handleDelete(db.id, db.name)}
                        className="text-red-600 dark:text-red-400 hover:underline flex items-center space-x-1"
                      >
                        <Trash2 size={14} />
                        <span>Delete</span>
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
        <div className="flex items-center justify-between border-t border-gray-200 px-6 py-4 text-sm dark:border-gray-700">
          <div className="text-light-text-secondary dark:text-dark-text-secondary">
            Showing {(meta.offset ?? 0) + (databases.length > 0 ? 1 : 0)}-{(meta.offset ?? 0) + databases.length} of{' '}
            {meta.total ?? databases.length}
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setPage((current) => Math.max(0, current - 1))}
              disabled={!hasPrevious}
              className="rounded-lg border border-gray-300 px-3 py-2 text-sm text-light-text-primary transition hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-700 dark:text-dark-text-primary dark:hover:bg-gray-900"
            >
              Previous
            </button>
            <button
              onClick={() => setPage((current) => current + 1)}
              disabled={!hasNext}
              className="rounded-lg border border-gray-300 px-3 py-2 text-sm text-light-text-primary transition hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-700 dark:text-dark-text-primary dark:hover:bg-gray-900"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
