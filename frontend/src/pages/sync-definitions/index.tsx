import React, { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { Trash } from 'lucide-react';

import { deleteSyncDefinition, getSyncDefinitionsPage } from '../../services/api';
import { useToast } from '../../components/ui/ToastProvider';
import { useConfirmDialog } from '../../components/ui/ConfirmDialogProvider';
import { FilterToolbar } from '../../components/ui/FilterToolbar';
import { ListPagination } from '../../components/ui/ListPagination';
import { getErrorMessage } from '../../lib/errors';

const PAGE_SIZE = 20;

export default function SyncDefinitionsList() {
  const { showToast } = useToast();
  const { confirm } = useConfirmDialog();
  const [defs, setDefs] = useState<any[]>([]);
  const [meta, setMeta] = useState<{ total?: number; offset?: number }>({});
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [modeFilter, setModeFilter] = useState('');
  const [pausedFilter, setPausedFilter] = useState('');
  const [page, setPage] = useState(0);

  const loadDefinitions = useCallback(async () => {
    setLoading(true);
    try {
      const response = await getSyncDefinitionsPage({
        q: search || undefined,
        sync_mode: modeFilter || undefined,
        is_paused: pausedFilter === '' ? undefined : pausedFilter === 'true',
        offset: page * PAGE_SIZE,
        limit: PAGE_SIZE,
      });
      setDefs(response.data);
      setMeta(response.meta ?? {});
    } catch (error) {
      showToast({
        title: 'Load failed',
        description: getErrorMessage(error, 'Failed to load sync definitions'),
        variant: 'error',
      });
    } finally {
      setLoading(false);
    }
  }, [modeFilter, page, pausedFilter, search, showToast]);

  useEffect(() => {
    void loadDefinitions();
  }, [loadDefinitions]);

  const handleDelete = async (id: string, name: string) => {
    const confirmed = await confirm({
      title: 'Delete sync definition?',
      description: `Delete "${name}" and its mappings, sources, and targets.`,
      confirmLabel: 'Delete definition',
      tone: 'danger',
    });
    if (!confirmed) return;

    try {
      await deleteSyncDefinition(id);
      showToast({
        title: 'Definition deleted',
        description: `${name} was removed successfully.`,
        variant: 'success',
      });
      void loadDefinitions();
    } catch (error) {
      showToast({
        title: 'Delete failed',
        description: getErrorMessage(error, 'Failed to delete definition'),
        variant: 'error',
      });
    }
  };

  const hasPrevious = page > 0;
  const hasNext = (meta.offset ?? 0) + defs.length < (meta.total ?? defs.length);

  return (
    <div className="p-8">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-light-text-primary dark:text-dark-text-primary">Sync Definitions</h1>
          <p className="mt-1 text-sm text-light-text-secondary dark:text-dark-text-secondary">
            Review sync configurations, source tables, and SharePoint targets.
          </p>
        </div>
        <Link
          href="/sync-definitions/new"
          className="rounded bg-light-primary px-4 py-2 text-white transition-colors hover:opacity-90 dark:bg-dark-primary"
        >
          Create New
        </Link>
      </div>

      <FilterToolbar className="lg:grid-cols-[minmax(0,1fr)_200px_180px]">
        <input
          value={search}
          onChange={(event) => {
            setPage(0);
            setSearch(event.target.value);
          }}
          placeholder="Search definition name"
          className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-light-text-primary dark:border-gray-700 dark:bg-gray-900 dark:text-dark-text-primary"
        />
        <select
          value={modeFilter}
          onChange={(event) => {
            setPage(0);
            setModeFilter(event.target.value);
          }}
          className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-light-text-primary dark:border-gray-700 dark:bg-gray-900 dark:text-dark-text-primary"
        >
          <option value="">All modes</option>
          <option value="ONE_WAY_PUSH">ONE_WAY_PUSH</option>
          <option value="TWO_WAY">TWO_WAY</option>
        </select>
        <select
          value={pausedFilter}
          onChange={(event) => {
            setPage(0);
            setPausedFilter(event.target.value);
          }}
          className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-light-text-primary dark:border-gray-700 dark:bg-gray-900 dark:text-dark-text-primary"
        >
          <option value="">All states</option>
          <option value="false">Active</option>
          <option value="true">Paused</option>
        </select>
      </FilterToolbar>

      <div className="overflow-hidden rounded border border-gray-200 bg-light-surface shadow-sm dark:border-gray-800 dark:bg-dark-surface">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-800">
          <thead className="bg-gray-50 dark:bg-gray-900/40">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-light-text-secondary dark:text-dark-text-secondary">Name</th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-light-text-secondary dark:text-dark-text-secondary">Source</th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-light-text-secondary dark:text-dark-text-secondary">Target</th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-light-text-secondary dark:text-dark-text-secondary">Mode</th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-light-text-secondary dark:text-dark-text-secondary">State</th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-light-text-secondary dark:text-dark-text-secondary">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 bg-light-surface dark:divide-gray-800 dark:bg-dark-surface">
            {loading ? (
              <tr>
                <td colSpan={6} className="px-6 py-8 text-center text-light-text-secondary dark:text-dark-text-secondary">
                  Loading sync definitions...
                </td>
              </tr>
            ) : defs.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-6 py-8 text-center text-light-text-secondary dark:text-dark-text-secondary">
                  No definitions found.
                </td>
              </tr>
            ) : (
              defs.map((def: any) => (
                <tr key={def.id} className="transition-colors hover:bg-gray-50 dark:hover:bg-gray-800/60">
                  <td className="px-6 py-4 font-medium text-light-text-primary dark:text-dark-text-primary">{def.name}</td>
                  <td className="px-6 py-4 text-sm text-light-text-secondary dark:text-dark-text-secondary">
                    {def.source_table_name_resolved || def.source_table_name || 'Unknown Source'}
                  </td>
                  <td className="px-6 py-4 text-sm text-light-text-secondary dark:text-dark-text-secondary">
                    {def.target_list_name || 'Unknown Target'}
                  </td>
                  <td className="px-6 py-4 text-sm text-light-text-secondary dark:text-dark-text-secondary">
                    <span className={`rounded px-2 py-1 text-xs ${def.sync_mode === 'TWO_WAY' ? 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300' : 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300'}`}>
                      {def.sync_mode === 'TWO_WAY' ? 'Two-Way' : 'Push'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm">
                    <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium ${def.is_paused ? 'bg-amber-100 text-amber-800 dark:bg-amber-950/50 dark:text-amber-300' : 'bg-green-100 text-green-800 dark:bg-green-950/50 dark:text-green-300'}`}>
                      {def.is_paused ? 'Paused' : 'Active'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm">
                    <div className="flex items-center space-x-4">
                      <Link href={`/sync-definitions/${def.id}`} className="font-medium text-light-primary hover:opacity-80 dark:text-dark-primary">
                        Manage
                      </Link>
                      <button onClick={() => void handleDelete(def.id, def.name)} className="text-red-600 hover:opacity-80 dark:text-red-400">
                        <Trash size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
        <ListPagination
          offset={meta.offset}
          total={meta.total}
          count={defs.length}
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
