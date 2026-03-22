import React, { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { getDatabaseInstancesPage, triggerFailover, deleteDatabaseInstance, getDatabases } from '../../services/api';
import { Database, ShieldAlert, ArrowRight, Edit, Trash2 } from 'lucide-react';
import { useToast } from '../../components/ui/ToastProvider';
import { useConfirmDialog } from '../../components/ui/ConfirmDialogProvider';
import { getErrorMessage } from '../../lib/errors';

const PAGE_SIZE = 20;

export default function DatabaseInstancesList() {
  const { showToast } = useToast();
  const { confirm } = useConfirmDialog();
  const [dbs, setDbs] = useState<any[]>([]);
  const [meta, setMeta] = useState<{ total?: number; offset?: number }>({});
  const [databases, setDatabases] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(false);
  const [failoverTarget, setFailoverTarget] = useState<any>(null); // Instance being promoted
  const [primaryToFail, setPrimaryToFail] = useState<string>('');
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [page, setPage] = useState(0);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [instancesResponse, databasesData] = await Promise.all([
        getDatabaseInstancesPage({
          q: search || undefined,
          role: roleFilter || undefined,
          status: statusFilter || undefined,
          offset: page * PAGE_SIZE,
          limit: PAGE_SIZE,
        }),
        getDatabases()
      ]);
      setDbs(instancesResponse.data);
      setMeta(instancesResponse.meta ?? {});

      // Create a map of databases by ID for easy lookup
      const dbMap = databasesData.reduce((acc: Record<string, any>, db: any) => {
        acc[db.id] = db;
        return acc;
      }, {});
      setDatabases(dbMap);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [page, roleFilter, search, statusFilter]);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  const loadDbs = () => {
    void loadData();
  };

  const handleFailover = async () => {
    if (!failoverTarget) return;
    setLoading(true);
    try {
        await triggerFailover({
            new_primary_instance_id: failoverTarget.id,
            old_primary_instance_id: primaryToFail || undefined
        });
        showToast({
          title: 'Replica promoted',
          description: `${failoverTarget.instance_label} is now the primary instance.`,
          variant: 'success'
        });
        setFailoverTarget(null);
        setPrimaryToFail('');
        loadDbs();
    } catch (e: any) {
        showToast({
          title: 'Failover failed',
          description: getErrorMessage(e, 'The database failover could not be completed'),
          variant: 'error'
        });
    } finally {
        setLoading(false);
    }
  };

  const handleDelete = async (id: string, label: string) => {
    const confirmed = await confirm({
      title: 'Delete database instance?',
      description: `Delete "${label}" from the connection inventory.`,
      confirmLabel: 'Delete instance',
      tone: 'danger'
    });
    if (!confirmed) return;
    try {
        await deleteDatabaseInstance(id);
        showToast({
          title: 'Instance deleted',
          description: `${label} was removed from the inventory.`,
          variant: 'success'
        });
        loadDbs();
    } catch (e: any) {
        showToast({
          title: 'Delete failed',
          description: getErrorMessage(e, 'The database instance could not be deleted'),
          variant: 'error'
        });
    }
  };

  // Find current primary for default selection in modal
  const currentPrimary = dbs.find(d => d.role === 'PRIMARY');
  const hasPrevious = page > 0;
  const hasNext = (meta.offset ?? 0) + dbs.length < (meta.total ?? dbs.length);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
             <h1 className="text-2xl font-bold font-secondary text-light-text-primary dark:text-dark-text-primary">Database Instances</h1>
             <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary">Manage registered database nodes and replication topology.</p>
        </div>
        <Link href="/database-instances/new" className="bg-light-primary dark:bg-dark-primary text-white px-4 py-2 rounded shadow-sm hover:bg-opacity-90">
          Register New Instance
        </Link>
      </div>

      <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_180px_180px]">
        <input
          value={search}
          onChange={(event) => {
            setPage(0);
            setSearch(event.target.value);
          }}
          placeholder="Search label, host, or database"
          className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-light-text-primary dark:border-gray-700 dark:bg-gray-900 dark:text-dark-text-primary"
        />
        <select
          value={roleFilter}
          onChange={(event) => {
            setPage(0);
            setRoleFilter(event.target.value);
          }}
          className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-light-text-primary dark:border-gray-700 dark:bg-gray-900 dark:text-dark-text-primary"
        >
          <option value="">All roles</option>
          <option value="PRIMARY">PRIMARY</option>
          <option value="REPLICA">REPLICA</option>
          <option value="SECONDARY">SECONDARY</option>
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
          <option value="INACTIVE">INACTIVE</option>
        </select>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {dbs.map((db) => (
            <div key={db.id} className="bg-white dark:bg-dark-surface p-6 rounded-lg border border-gray-200 dark:border-gray-800 shadow-sm flex justify-between items-start">
                <div className="flex items-start space-x-4">
                    <div className={`p-3 rounded-full ${db.role === 'PRIMARY' ? 'bg-light-primary/10 text-light-primary dark:bg-dark-primary/10 dark:text-dark-primary' : 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400'}`}>
                        <Database size={24} />
                    </div>
                    <div>
                        <h3 className="text-lg font-bold flex items-center text-light-text-primary dark:text-dark-text-primary">
                            {db.instance_label}
                            {db.role === 'PRIMARY' && <span className="ml-2 px-2 py-0.5 rounded text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 font-bold">PRIMARY</span>}
                            {db.role === 'REPLICA' && <span className="ml-2 px-2 py-0.5 rounded text-xs bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300">REPLICA</span>}
                            {db.status === 'INACTIVE' && <span className="ml-2 px-2 py-0.5 rounded text-xs bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300">INACTIVE</span>}
                        </h3>
                        {db.database_id && databases[db.database_id] && (
                            <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary mt-1">
                                Logical Database: <Link href={`/databases/${db.database_id}`} className="font-medium text-light-primary dark:text-dark-primary hover:underline">{databases[db.database_id].name}</Link>
                            </p>
                        )}
                        <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary font-mono">{db.host}:{db.port}</p>
                        {db.db_name && <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary">Database: <span className="font-mono">{db.db_name}</span></p>}
                        {db.username && <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary">User: <span className="font-mono">{db.username}</span></p>}
                    </div>
                </div>

                <div className="flex items-center space-x-2">
                     <Link
                        href={`/database-instances/${db.id}/edit`}
                        className="flex items-center space-x-1 text-sm text-light-primary dark:text-dark-primary hover:opacity-80 px-3 py-1.5 border border-light-primary dark:border-dark-primary rounded transition-opacity"
                     >
                         <Edit size={14} />
                         <span>Edit</span>
                     </Link>
                     <button
                        onClick={() => handleDelete(db.id, db.instance_label)}
                        className="flex items-center space-x-1 text-sm text-red-600 dark:text-red-400 hover:opacity-80 px-3 py-1.5 border border-red-600 dark:border-red-400 rounded transition-opacity"
                     >
                         <Trash2 size={14} />
                         <span>Delete</span>
                     </button>
                     {db.role !== 'PRIMARY' && db.status === 'ACTIVE' && (
                         <button
                            onClick={() => {
                                setFailoverTarget(db);
                                setPrimaryToFail(currentPrimary?.id || '');
                            }}
                            className="flex items-center space-x-2 text-sm text-light-warning dark:text-dark-warning hover:opacity-80 px-3 py-1 border border-light-warning dark:border-dark-warning rounded transition-opacity"
                         >
                             <ShieldAlert size={16} />
                             <span>Promote</span>
                         </button>
                     )}
                </div>
            </div>
        ))}
        {dbs.length === 0 && <div className="text-center text-light-text-secondary dark:text-dark-text-secondary py-8">No instances registered.</div>}
      </div>
      <div className="flex items-center justify-between text-sm">
        <div className="text-light-text-secondary dark:text-dark-text-secondary">
          Showing {(meta.offset ?? 0) + (dbs.length > 0 ? 1 : 0)}-{(meta.offset ?? 0) + dbs.length} of {meta.total ?? dbs.length}
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

      {/* Failover Modal */}
      {failoverTarget && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white dark:bg-dark-surface p-6 rounded-lg shadow-xl max-w-md w-full border border-gray-200 dark:border-gray-700">
                <h3 className="text-xl font-bold mb-4 text-light-danger dark:text-dark-danger flex items-center">
                    <ShieldAlert className="mr-2" /> Confirm Failover
                </h3>
                <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary mb-6">
                    You are about to promote <strong className="text-light-text-primary dark:text-dark-text-primary">{failoverTarget.instance_label}</strong> to PRIMARY.
                    This will rebind all sync sources from the old primary to this instance.
                </p>

                <div className="mb-6">
                    <label className="block text-sm font-medium text-light-text-primary dark:text-dark-text-primary mb-1">Old Primary (to mark FAILED)</label>
                    <select
                        className="w-full border border-gray-300 dark:border-gray-600 rounded p-2 bg-white dark:bg-dark-surface text-light-text-primary dark:text-dark-text-primary"
                        value={primaryToFail}
                        onChange={(e) => setPrimaryToFail(e.target.value)}
                    >
                        <option value="">-- None (Just Promote) --</option>
                        {dbs.filter(d => d.role === 'PRIMARY').map(d => (
                            <option key={d.id} value={d.id}>{d.instance_label} ({d.host})</option>
                        ))}
                    </select>
                </div>

                <div className="flex justify-end space-x-3">
                    <button
                        onClick={() => setFailoverTarget(null)}
                        className="px-4 py-2 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleFailover}
                        disabled={loading}
                        className="px-4 py-2 bg-light-danger dark:bg-dark-danger text-white rounded hover:opacity-90 disabled:opacity-50 transition-opacity"
                    >
                        {loading ? 'Promoting...' : 'Confirm Promotion'}
                    </button>
                </div>
            </div>
        </div>
      )}
    </div>
  );
}
