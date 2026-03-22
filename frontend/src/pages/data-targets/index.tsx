import React, { useEffect, useState, useCallback } from 'react';
import {
  getConnections,
  getSharePointSitesPage,
  resolveSharePointSite,
  extractSharePointSites,
  getSharePointListsPage,
  extractSharePointLists,
  getSharePointColumnsPage,
  extractSharePointColumns
} from '../../services/api';
import { FilterToolbar } from '../../components/ui/FilterToolbar';
import { ListPagination } from '../../components/ui/ListPagination';

const PAGE_SIZE = 20;

export default function DataTargetsPage() {
  const [connections, setConnections] = useState<any[]>([]);
  const [sites, setSites] = useState<any[]>([]);
  const [lists, setLists] = useState<any[]>([]);
  const [columns, setColumns] = useState<any[]>([]);

  const [selectedConnectionId, setSelectedConnectionId] = useState('');
  const [selectedSiteId, setSelectedSiteId] = useState('');
  const [selectedListId, setSelectedListId] = useState('');
  const [sitesMeta, setSitesMeta] = useState<{ total?: number; offset?: number }>({});
  const [listsMeta, setListsMeta] = useState<{ total?: number; offset?: number }>({});
  const [columnsMeta, setColumnsMeta] = useState<{ total?: number; offset?: number }>({});
  const [siteSearch, setSiteSearch] = useState('');
  const [sitePage, setSitePage] = useState(0);
  const [listSearch, setListSearch] = useState('');
  const [listProvisionedFilter, setListProvisionedFilter] = useState('');
  const [listPage, setListPage] = useState(0);
  const [columnSearch, setColumnSearch] = useState('');
  const [columnReadonlyFilter, setColumnReadonlyFilter] = useState('');
  const [columnPage, setColumnPage] = useState(0);

  // Manual fallback state
  const [showManualResolve, setShowManualResolve] = useState(false);
  const [siteForm, setSiteForm] = useState({ hostname: '', sitePath: '' });
  
  const [loading, setLoading] = useState(false);
  const [siteExtractLoading, setSiteExtractLoading] = useState(false);
  const [columnsLoading, setColumnsLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    getConnections()
      .then(setConnections)
      .catch(() => setError('Failed to load SharePoint connections'));
  }, []);

  const loadSites = useCallback((connId: string, page = sitePage, search = siteSearch) => {
    getSharePointSitesPage({
      connection_id: connId,
      q: search || undefined,
      offset: page * PAGE_SIZE,
      limit: PAGE_SIZE,
    })
      .then((response) => {
        setSites(response.data);
        setSitesMeta(response.meta ?? {});
      })
      .catch(() => setError('Failed to load SharePoint sites'));
  }, [sitePage, siteSearch]);

  const loadLists = useCallback((siteId: string, page = listPage, search = listSearch, provisioned = listProvisionedFilter) => {
    getSharePointListsPage(siteId, {
      q: search || undefined,
      is_provisioned: provisioned === '' ? undefined : provisioned === 'true',
      offset: page * PAGE_SIZE,
      limit: PAGE_SIZE,
    })
      .then((response) => {
        setLists(response.data);
        setListsMeta(response.meta ?? {});
      })
      .catch(() => setError('Failed to load SharePoint lists'));
  }, [listPage, listProvisionedFilter, listSearch]);

  const loadColumns = useCallback((listId: string, page = columnPage, search = columnSearch, readonlyFilter = columnReadonlyFilter) => {
    getSharePointColumnsPage(listId, {
      q: search || undefined,
      is_readonly: readonlyFilter === '' ? undefined : readonlyFilter === 'true',
      offset: page * PAGE_SIZE,
      limit: PAGE_SIZE,
    })
      .then((response) => {
        setColumns(response.data);
        setColumnsMeta(response.meta ?? {});
      })
      .catch(() => setError('Failed to load SharePoint columns'));
  }, [columnPage, columnReadonlyFilter, columnSearch]);

  useEffect(() => {
    if (!selectedConnectionId) {
      setSites([]);
      setSitesMeta({});
      setSelectedSiteId('');
      setSelectedListId('');
      setLists([]);
      setListsMeta({});
      setColumns([]);
      setColumnsMeta({});
      return;
    }
    const conn = connections.find(c => c.id === selectedConnectionId);
    if (conn && conn.hostname) {
        setSiteForm(prev => ({ ...prev, hostname: conn.hostname }));
    }

    setSitePage(0);
    setSiteSearch('');
    setSelectedSiteId('');
    setSelectedListId('');
    setLists([]);
    setListsMeta({});
    setColumns([]);
    setColumnsMeta({});
    loadSites(selectedConnectionId, 0, '');
  }, [connections, loadSites, selectedConnectionId]);

  useEffect(() => {
    if (!selectedConnectionId) return;
    loadSites(selectedConnectionId);
  }, [loadSites, selectedConnectionId, sitePage, siteSearch]);

  useEffect(() => {
    if (!selectedSiteId) {
      setLists([]);
      setListsMeta({});
      setSelectedListId('');
      setColumns([]);
      setColumnsMeta({});
      return;
    }
    setListPage(0);
    setListSearch('');
    setListProvisionedFilter('');
    setSelectedListId('');
    setColumns([]);
    setColumnsMeta({});
    loadLists(selectedSiteId, 0, '', '');
  }, [loadLists, selectedSiteId]);

  useEffect(() => {
    if (!selectedSiteId) return;
    loadLists(selectedSiteId);
  }, [listPage, listProvisionedFilter, listSearch, loadLists, selectedSiteId]);

  useEffect(() => {
    if (!selectedListId) {
      setColumns([]);
      setColumnsMeta({});
      return;
    }
    setColumnPage(0);
    setColumnSearch('');
    setColumnReadonlyFilter('');
    loadColumns(selectedListId, 0, '', '');
  }, [loadColumns, selectedListId]);

  useEffect(() => {
    if (!selectedListId) return;
    loadColumns(selectedListId);
  }, [columnPage, columnReadonlyFilter, columnSearch, loadColumns, selectedListId]);

  const handleExtractSites = async () => {
      if (!selectedConnectionId) {
          setError('Select a connection first');
          return;
      }
      setSiteExtractLoading(true);
      setError('');
      try {
          await extractSharePointSites(selectedConnectionId);
          loadSites(selectedConnectionId, 0, siteSearch);
      } catch (err: any) {
          setError(err.response?.data?.detail || 'Failed to extract sites');
      } finally {
          setSiteExtractLoading(false);
      }
  };

  const handleResolveSite = async () => {
    if (!selectedConnectionId || !siteForm.hostname || !siteForm.sitePath) {
      setError('Select a connection and provide hostname + site path');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const site = await resolveSharePointSite({
        connection_id: selectedConnectionId,
        hostname: siteForm.hostname,
        site_path: siteForm.sitePath
      });
      loadSites(selectedConnectionId, 0, siteSearch);
      setSelectedSiteId(site.id);
      setShowManualResolve(false);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to resolve site');
    } finally {
      setLoading(false);
    }
  };

  const handleExtractLists = async () => {
    if (!selectedSiteId) {
      setError('Select a site to extract lists');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const data = await extractSharePointLists(selectedSiteId);
      setLists(data);
      setListsMeta({ total: data.length, offset: 0 });
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to extract lists');
    } finally {
      setLoading(false);
    }
  };

  const handleExtractColumns = async () => {
    if (!selectedListId) {
      setError('Select a list to extract columns');
      return;
    }
    setColumnsLoading(true);
    setError('');
    try {
      const data = await extractSharePointColumns(selectedListId);
      setColumns(data);
      setColumnsMeta({ total: data.length, offset: 0 });
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to extract columns');
    } finally {
      setColumnsLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold font-secondary text-light-text-primary dark:text-dark-text-primary">Data Targets</h1>
        <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary">
          Discover SharePoint sites, lists, and columns for target selection.
        </p>
      </div>

      {error && (
        <div className="bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 p-3 rounded">
          {error}
        </div>
      )}

      <section className="bg-white dark:bg-dark-surface border border-gray-200 dark:border-gray-800 rounded-lg p-6 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Site Discovery</h2>
            {selectedConnectionId && (
                <div className="space-x-2">
                    <button
                        onClick={() => setShowManualResolve(!showManualResolve)}
                        className="px-3 py-2 text-sm text-light-primary hover:underline"
                    >
                        {showManualResolve ? 'Cancel Manual Add' : 'Manually Add Site'}
                    </button>
                    <button
                        onClick={handleExtractSites}
                        className="px-3 py-2 text-sm bg-gray-900 text-white rounded hover:opacity-90"
                        disabled={siteExtractLoading}
                    >
                        {siteExtractLoading ? 'Scanning Graph...' : 'Discover Sites'}
                    </button>
                </div>
            )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-light-text-primary dark:text-dark-text-primary">SharePoint Connection</label>
            <select
              value={selectedConnectionId}
              onChange={(e) => setSelectedConnectionId(e.target.value)}
              className="mt-1 w-full border border-gray-300 dark:border-gray-700 rounded p-2 bg-white dark:bg-dark-surface text-sm"
            >
              <option value="">Select connection</option>
              {connections.map((conn) => (
                <option key={conn.id} value={conn.id}>{conn.tenant_id} {conn.hostname ? `(${conn.hostname})` : ''}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-light-text-primary dark:text-dark-text-primary">Site</label>
            <select
              value={selectedSiteId}
              onChange={(e) => setSelectedSiteId(e.target.value)}
              className="mt-1 w-full border border-gray-300 dark:border-gray-700 rounded p-2 bg-white dark:bg-dark-surface text-sm"
              disabled={!selectedConnectionId || sites.length === 0}
            >
              <option value="">Select site</option>
              {sites.map((site) => (
                <option key={site.id} value={site.id}>{site.site_path} ({site.hostname})</option>
              ))}
            </select>
            {selectedConnectionId && sites.length === 0 && !siteExtractLoading && (
                <p className="text-xs text-gray-500 mt-1">No sites found. Click &quot;Discover Sites&quot; to scan your tenant.</p>
            )}
          </div>
        </div>

        <FilterToolbar className="md:grid-cols-[minmax(0,1fr)_180px]">
          <input
            value={siteSearch}
            onChange={(e) => {
              setSitePage(0);
              setSiteSearch(e.target.value);
            }}
            placeholder="Search hostname or site path"
            className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-light-text-primary dark:border-gray-700 dark:bg-gray-900 dark:text-dark-text-primary"
          />
          <div className="rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-light-text-secondary dark:border-gray-700 dark:bg-gray-900 dark:text-dark-text-secondary">
            {sitesMeta.total ?? sites.length} sites
          </div>
        </FilterToolbar>

        {/* Manual Fallback Form */}
        {showManualResolve && (
            <div className="mt-4 p-4 border border-dashed border-gray-300 rounded bg-gray-50 dark:bg-gray-800/50">
                <h3 className="text-sm font-semibold mb-2">Manually Add Site</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label className="block text-xs font-medium text-gray-500">Hostname</label>
                        <input
                        value={siteForm.hostname}
                        onChange={(e) => setSiteForm({ ...siteForm, hostname: e.target.value })}
                        className="mt-1 w-full border border-gray-300 rounded p-1 text-sm"
                        placeholder="contoso.sharepoint.com"
                        />
                    </div>
                    <div>
                        <label className="block text-xs font-medium text-gray-500">Site Path</label>
                        <input
                        value={siteForm.sitePath}
                        onChange={(e) => setSiteForm({ ...siteForm, sitePath: e.target.value })}
                        className="mt-1 w-full border border-gray-300 rounded p-1 text-sm"
                        placeholder="/sites/Operations"
                        />
                    </div>
                </div>
                <button
                    onClick={handleResolveSite}
                    className="mt-2 px-3 py-1 bg-light-primary text-white text-xs rounded"
                    disabled={loading}
                >
                    {loading ? 'Resolving...' : 'Add Site'}
                </button>
            </div>
        )}

        <ListPagination
          offset={sitesMeta.offset}
          total={sitesMeta.total}
          count={sites.length}
          hasPrevious={sitePage > 0}
          hasNext={(sitesMeta.offset ?? 0) + sites.length < (sitesMeta.total ?? sites.length)}
          onPrevious={() => setSitePage((current) => Math.max(0, current - 1))}
          onNext={() => setSitePage((current) => current + 1)}
          className="rounded-lg border border-gray-200 dark:border-gray-800"
        />
      </section>

      <section className="bg-white dark:bg-dark-surface border border-gray-200 dark:border-gray-800 rounded-lg p-6 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">List Inventory</h2>
          <button
            onClick={handleExtractLists}
            className="px-3 py-2 text-sm bg-light-primary dark:bg-dark-primary text-white rounded hover:opacity-90"
            disabled={loading || !selectedSiteId}
          >
            {loading ? 'Extracting...' : 'Extract Lists'}
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-light-text-primary dark:text-dark-text-primary">Resolved Sites</label>
            <select
              value={selectedSiteId}
              onChange={(e) => setSelectedSiteId(e.target.value)}
              className="mt-1 w-full border border-gray-300 dark:border-gray-700 rounded p-2 bg-white dark:bg-dark-surface text-sm"
            >
              <option value="">Select site</option>
              {sites.map((site) => (
                <option key={site.id} value={site.id}>{site.hostname}{site.site_path}</option>
              ))}
            </select>
          </div>
        </div>

        <FilterToolbar className="lg:grid-cols-[minmax(0,1fr)_180px_180px]">
          <input
            value={listSearch}
            onChange={(e) => {
              setListPage(0);
              setListSearch(e.target.value);
            }}
            placeholder="Search list name or template"
            className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-light-text-primary dark:border-gray-700 dark:bg-gray-900 dark:text-dark-text-primary"
          />
          <select
            value={listProvisionedFilter}
            onChange={(e) => {
              setListPage(0);
              setListProvisionedFilter(e.target.value);
            }}
            className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-light-text-primary dark:border-gray-700 dark:bg-gray-900 dark:text-dark-text-primary"
          >
            <option value="">All lists</option>
            <option value="true">Provisioned only</option>
            <option value="false">Discovered only</option>
          </select>
          <div className="rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-light-text-secondary dark:border-gray-700 dark:bg-gray-900 dark:text-dark-text-secondary">
            {listsMeta.total ?? lists.length} lists
          </div>
        </FilterToolbar>

        {lists.length === 0 ? (
          <div className="text-sm text-light-text-secondary dark:text-dark-text-secondary">
            No lists stored yet. Extract lists to populate the catalog.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700 text-sm">
              <thead className="bg-gray-50 dark:bg-gray-800">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">List</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Template</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Columns</th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-dark-surface divide-y divide-gray-200 dark:divide-gray-700">
                {lists.map((list) => (
                  <tr key={list.id} className={selectedListId === list.id ? 'bg-light-primary/5 dark:bg-dark-primary/10' : ''}>
                    <td
                      className="px-4 py-2 font-medium cursor-pointer"
                      onClick={() => setSelectedListId(list.id)}
                    >
                      {list.display_name}
                    </td>
                    <td className="px-4 py-2 text-xs font-mono text-light-text-secondary dark:text-dark-text-secondary">
                        {list.list_id}
                    </td>
                    <td className="px-4 py-2 text-light-text-secondary dark:text-dark-text-secondary">{list.template || '-'}</td>
                    <td className="px-4 py-2 text-light-text-secondary dark:text-dark-text-secondary">{list.columns_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <ListPagination
          offset={listsMeta.offset}
          total={listsMeta.total}
          count={lists.length}
          hasPrevious={listPage > 0}
          hasNext={(listsMeta.offset ?? 0) + lists.length < (listsMeta.total ?? lists.length)}
          onPrevious={() => setListPage((current) => Math.max(0, current - 1))}
          onNext={() => setListPage((current) => current + 1)}
          className="rounded-lg border border-gray-200 dark:border-gray-800"
        />
      </section>

      <section className="bg-white dark:bg-dark-surface border border-gray-200 dark:border-gray-800 rounded-lg p-6 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">List Columns</h2>
          <button
            onClick={handleExtractColumns}
            className="px-3 py-2 text-sm bg-gray-900 text-white rounded hover:opacity-90"
            disabled={columnsLoading || !selectedListId}
          >
            {columnsLoading ? 'Extracting...' : 'Extract Columns'}
          </button>
        </div>

        {selectedListId === '' ? (
          <div className="text-sm text-light-text-secondary dark:text-dark-text-secondary">
            Select a list to view and extract its columns.
          </div>
        ) : columns.length === 0 ? (
          <div className="text-sm text-light-text-secondary dark:text-dark-text-secondary">
            No columns stored yet. Extract columns for the selected list.
          </div>
        ) : (
          <>
            <FilterToolbar className="lg:grid-cols-[minmax(0,1fr)_180px_180px]">
              <input
                value={columnSearch}
                onChange={(e) => {
                  setColumnPage(0);
                  setColumnSearch(e.target.value);
                }}
                placeholder="Search column name or type"
                className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-light-text-primary dark:border-gray-700 dark:bg-gray-900 dark:text-dark-text-primary"
              />
              <select
                value={columnReadonlyFilter}
                onChange={(e) => {
                  setColumnPage(0);
                  setColumnReadonlyFilter(e.target.value);
                }}
                className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-light-text-primary dark:border-gray-700 dark:bg-gray-900 dark:text-dark-text-primary"
              >
                <option value="">All columns</option>
                <option value="true">Read-only only</option>
                <option value="false">Writable only</option>
              </select>
              <div className="rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-light-text-secondary dark:border-gray-700 dark:bg-gray-900 dark:text-dark-text-secondary">
                {columnsMeta.total ?? columns.length} columns
              </div>
            </FilterToolbar>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700 text-sm">
                <thead className="bg-gray-50 dark:bg-gray-800">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Column</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Required</th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Read Only</th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-dark-surface divide-y divide-gray-200 dark:divide-gray-700">
                  {columns.map((col) => (
                    <tr key={col.id}>
                      <td className="px-4 py-2 font-medium">{col.column_name}</td>
                      <td className="px-4 py-2 text-light-text-secondary dark:text-dark-text-secondary">{col.column_type}</td>
                      <td className="px-4 py-2 text-light-text-secondary dark:text-dark-text-secondary">{col.is_required ? 'Yes' : 'No'}</td>
                      <td className="px-4 py-2 text-light-text-secondary dark:text-dark-text-secondary">{col.is_readonly ? 'Yes' : 'No'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
        <ListPagination
          offset={columnsMeta.offset}
          total={columnsMeta.total}
          count={columns.length}
          hasPrevious={columnPage > 0}
          hasNext={(columnsMeta.offset ?? 0) + columns.length < (columnsMeta.total ?? columns.length)}
          onPrevious={() => setColumnPage((current) => Math.max(0, current - 1))}
          onNext={() => setColumnPage((current) => current + 1)}
          className="rounded-lg border border-gray-200 dark:border-gray-800"
        />
      </section>
    </div>
  );
}
