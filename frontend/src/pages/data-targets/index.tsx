import React, { useEffect, useState } from 'react';
import {
  getConnections,
  getSharePointSites,
  resolveSharePointSite,
  extractSharePointSites,
  getSharePointLists,
  extractSharePointLists,
  getSharePointColumns,
  extractSharePointColumns
} from '../../services/api';

export default function DataTargetsPage() {
  const [connections, setConnections] = useState<any[]>([]);
  const [sites, setSites] = useState<any[]>([]);
  const [lists, setLists] = useState<any[]>([]);
  const [columns, setColumns] = useState<any[]>([]);

  const [selectedConnectionId, setSelectedConnectionId] = useState('');
  const [selectedSiteId, setSelectedSiteId] = useState('');
  const [selectedListId, setSelectedListId] = useState('');

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

  useEffect(() => {
    if (!selectedConnectionId) {
      setSites([]);
      setSelectedSiteId('');
      setSelectedListId('');
      setLists([]);
      setColumns([]);
      return;
    }
    // Set default hostname for manual form if available
    const conn = connections.find(c => c.id === selectedConnectionId);
    if (conn && conn.hostname) {
        setSiteForm(prev => ({ ...prev, hostname: conn.hostname }));
    }

    setSelectedSiteId('');
    setSelectedListId('');
    setLists([]);
    setColumns([]);
    loadSites(selectedConnectionId);
  }, [selectedConnectionId]);

  const loadSites = (connId: string) => {
    getSharePointSites(connId)
      .then(setSites)
      .catch(() => setError('Failed to load SharePoint sites'));
  };

  useEffect(() => {
    if (!selectedSiteId) {
      setLists([]);
      setSelectedListId('');
      setColumns([]);
      return;
    }
    setSelectedListId('');
    setColumns([]);
    getSharePointLists(selectedSiteId)
      .then(setLists)
      .catch(() => setError('Failed to load SharePoint lists'));
  }, [selectedSiteId]);

  useEffect(() => {
    if (!selectedListId) {
      setColumns([]);
      return;
    }
    getSharePointColumns(selectedListId)
      .then(setColumns)
      .catch(() => setError('Failed to load SharePoint columns'));
  }, [selectedListId]);

  const handleExtractSites = async () => {
      if (!selectedConnectionId) {
          setError('Select a connection first');
          return;
      }
      setSiteExtractLoading(true);
      setError('');
      try {
          await extractSharePointSites(selectedConnectionId);
          loadSites(selectedConnectionId);
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
      loadSites(selectedConnectionId);
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
                <p className="text-xs text-gray-500 mt-1">No sites found. Click "Discover Sites" to scan your tenant.</p>
            )}
          </div>
        </div>

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
        )}
      </section>
    </div>
  );
}
