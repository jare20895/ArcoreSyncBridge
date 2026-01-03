import React, { useEffect, useMemo, useState } from 'react';
import {
  getDatabases,
  getDatabaseInstances,
  getConnections,
  getSourceTables,
  extractSourceTables,
  extractSourceTableDetails,
  getSourceTableDetails,
  provisionSharePointList
} from '../../services/api';

export default function DataSourcesPage() {
  const [databases, setDatabases] = useState<any[]>([]);
  const [instances, setInstances] = useState<any[]>([]);
  const [connections, setConnections] = useState<any[]>([]);
  const [tables, setTables] = useState<any[]>([]);
  const [selectedDatabaseId, setSelectedDatabaseId] = useState('');
  const [selectedInstanceId, setSelectedInstanceId] = useState('');
  const [schemaName, setSchemaName] = useState('public');
  const [selectedTableIds, setSelectedTableIds] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [provisionForm, setProvisionForm] = useState({
    tableId: '',
    connectionId: '',
    hostname: '',
    sitePath: '',
    listName: '',
    description: '',
    skipColumns: ''
  });
  const [provisioning, setProvisioning] = useState(false);
  const [provisionError, setProvisionError] = useState('');
  const [provisionResult, setProvisionResult] = useState<any>(null);
  const [tableDetailsCache, setTableDetailsCache] = useState<Record<string, any>>({});
  
  // Advanced Provisioning State
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [columnConfig, setColumnConfig] = useState<Record<string, { type: string, included: boolean }>>({});
  const [currentTableColumns, setCurrentTableColumns] = useState<any[]>([]);

  useEffect(() => {
    Promise.all([getDatabases(), getDatabaseInstances(), getConnections()])
      .then(([dbData, instanceData, connectionData]) => {
        setDatabases(dbData);
        setInstances(instanceData);
        setConnections(connectionData);
      })
      .catch(() => setError('Failed to load catalog data'));
  }, []);

  // Determine default SP type from PG type (Client-side mirror of backend logic)
  const getDefaultSPType = (pgType: string) => {
    const t = pgType.toLowerCase();
    if (['integer', 'smallint', 'bigint', 'numeric', 'decimal', 'real', 'double precision', 'int'].includes(t)) return 'number';
    if (['boolean', 'bool'].includes(t)) return 'boolean';
    if (['timestamp without time zone', 'timestamp with time zone', 'date', 'timestamp'].includes(t)) return 'dateTime';
    return 'text';
  };

  useEffect(() => {
    if (provisionForm.tableId && showAdvanced) {
      ensureTableDetails(provisionForm.tableId).then((details) => {
        if (details && details.columns) {
            setCurrentTableColumns(details.columns);
            // Initialize config if empty or mismatch
            const newConfig: Record<string, { type: string, included: boolean }> = {};
            const skipSet = new Set(provisionForm.skipColumns.split(',').map(s => s.trim()).filter(Boolean));
            
            details.columns.forEach((col: any) => {
                newConfig[col.column_name] = {
                    type: getDefaultSPType(col.data_type),
                    included: !skipSet.has(col.column_name)
                };
            });
            setColumnConfig(newConfig);
        }
      });
    }
  }, [provisionForm.tableId, showAdvanced]); // Depend on tableId and toggle

  const handleAdvancedConfigChange = (colName: string, field: 'type' | 'included', value: any) => {
      setColumnConfig(prev => ({
          ...prev,
          [colName]: { ...prev[colName], [field]: value }
      }));
  };

  const selectedTableCount = selectedTableIds.size;

  const selectableTables = useMemo(() => {
    if (!tables.length) return [];
    return tables.sort((a, b) => a.table_name.localeCompare(b.table_name));
  }, [tables]);

  const loadTables = async () => {
    if (!selectedDatabaseId) {
      setError('Select a database first');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const data = await getSourceTables(selectedDatabaseId);
      setTables(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load tables');
    } finally {
      setLoading(false);
    }
  };

  const handleExtractTables = async () => {
    if (!selectedDatabaseId || !selectedInstanceId) {
      setError('Select both a database and database instance');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const data = await extractSourceTables({
        database_id: selectedDatabaseId,
        instance_id: selectedInstanceId,
        schema: schemaName || 'public'
      });
      setTables(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to extract tables');
    } finally {
      setLoading(false);
    }
  };

  const toggleTable = (tableId: string) => {
    const next = new Set(selectedTableIds);
    if (next.has(tableId)) {
      next.delete(tableId);
    } else {
      next.add(tableId);
    }
    setSelectedTableIds(next);
  };

  const toggleAllTables = () => {
    if (selectedTableIds.size === tables.length) {
      setSelectedTableIds(new Set());
      return;
    }
    setSelectedTableIds(new Set(tables.map((table) => table.id)));
  };

  const handleExtractDetails = async () => {
    if (!selectedInstanceId) {
      setError('Select a database instance to extract details');
      return;
    }
    if (selectedTableIds.size === 0) {
      setError('Select at least one table to extract details');
      return;
    }
    setLoading(true);
    setError('');
    try {
      await extractSourceTableDetails({
        instance_id: selectedInstanceId,
        table_ids: Array.from(selectedTableIds)
      });
      await loadTables();
      setSelectedTableIds(new Set());
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to extract table definitions');
    } finally {
      setLoading(false);
    }
  };

  const handleProvisionChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setProvisionForm({ ...provisionForm, [e.target.name]: e.target.value });
  };

  const ensureTableDetails = async (tableId: string) => {
    if (tableDetailsCache[tableId]) {
      return tableDetailsCache[tableId];
    }
    const details = await getSourceTableDetails(tableId);
    setTableDetailsCache((prev) => ({ ...prev, [tableId]: details }));
    return details;
  };

  const handleProvision = async () => {
    setProvisionError('');
    setProvisionResult(null);

    if (!provisionForm.tableId || !provisionForm.connectionId || !provisionForm.hostname || !provisionForm.sitePath || !provisionForm.listName) {
      setProvisionError('Complete the table, connection, site, and list details');
      return;
    }

    setProvisioning(true);
    try {
      const details = await ensureTableDetails(provisionForm.tableId);
      const columns = details.columns.map((col: any) => ({
        name: col.column_name,
        data_type: col.data_type,
        is_nullable: col.is_nullable,
        ordinal_position: col.ordinal_position,
        is_primary_key: col.is_primary_key
      }));

      let skipColumns: string[] = [];
      let columnConfigurations: Record<string, any> = {};

      if (showAdvanced) {
          // Use advanced config
          skipColumns = Object.entries(columnConfig)
            .filter(([_, conf]) => !conf.included)
            .map(([name]) => name);
            
          Object.entries(columnConfig).forEach(([name, conf]) => {
              if (conf.included) {
                  // Only send configuration if it differs from default? 
                  // Or just send everything is safer if we trust the UI.
                  // Construct payload based on type
                  if (conf.type === 'text') columnConfigurations[name] = { text: { allowMultipleLines: true } };
                  else if (conf.type === 'number') columnConfigurations[name] = { number: { decimalPlaces: "automatic" } };
                  else if (conf.type === 'boolean') columnConfigurations[name] = { boolean: {} };
                  else if (conf.type === 'dateTime') columnConfigurations[name] = { dateTime: { displayAs: "default" } };
              }
          });
      } else {
          // Simple mode
          skipColumns = provisionForm.skipColumns
            .split(',')
            .map((col) => col.trim())
            .filter((col) => col);
      }

      const payload = {
        table_id: provisionForm.tableId,
        connection_id: provisionForm.connectionId,
        hostname: provisionForm.hostname,
        site_path: provisionForm.sitePath,
        list_name: provisionForm.listName,
        description: provisionForm.description,
        columns,
        skip_columns: skipColumns,
        column_configurations: columnConfigurations
      };

      const result = await provisionSharePointList(payload);
      setProvisionResult(result);
    } catch (err: any) {
      setProvisionError(err.response?.data?.detail || 'Provisioning failed');
    } finally {
      setProvisioning(false);
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold font-secondary text-light-text-primary dark:text-dark-text-primary">Data Sources</h1>
        <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary">
          Capture table inventory and source schema definitions before building sync definitions.
        </p>
      </div>

      {error && (
        <div className="bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 p-3 rounded">
          {error}
        </div>
      )}

      <section className="bg-white dark:bg-dark-surface border border-gray-200 dark:border-gray-800 rounded-lg p-6 space-y-4 shadow-sm">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Source Inventory</h2>
          <div className="flex items-center space-x-2">
            <button
              onClick={loadTables}
              className="px-3 py-2 text-sm border border-gray-300 dark:border-gray-700 rounded text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-800"
              disabled={loading}
            >
              Load Stored Tables
            </button>
            <button
              onClick={handleExtractTables}
              className="px-3 py-2 text-sm bg-light-primary dark:bg-dark-primary text-white rounded hover:opacity-90"
              disabled={loading}
            >
              {loading ? 'Extracting...' : 'Extract Tables'}
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-light-text-primary dark:text-dark-text-primary">Database</label>
            <select
              className="mt-1 w-full border border-gray-300 dark:border-gray-700 rounded p-2 bg-white dark:bg-dark-surface text-sm"
              value={selectedDatabaseId}
              onChange={(e) => setSelectedDatabaseId(e.target.value)}
            >
              <option value="">Select database</option>
              {databases.map((db) => (
                <option key={db.id} value={db.id}>{db.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-light-text-primary dark:text-dark-text-primary">Database Instance</label>
            <select
              className="mt-1 w-full border border-gray-300 dark:border-gray-700 rounded p-2 bg-white dark:bg-dark-surface text-sm"
              value={selectedInstanceId}
              onChange={(e) => setSelectedInstanceId(e.target.value)}
            >
              <option value="">Select instance</option>
              {instances.map((instance) => (
                <option key={instance.id} value={instance.id}>
                  {instance.instance_label} ({instance.host})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-light-text-primary dark:text-dark-text-primary">Schema</label>
            <input
              type="text"
              value={schemaName}
              onChange={(e) => setSchemaName(e.target.value)}
              className="mt-1 w-full border border-gray-300 dark:border-gray-700 rounded p-2 bg-white dark:bg-dark-surface text-sm"
              placeholder="public"
            />
          </div>
        </div>
      </section>

      <section className="bg-white dark:bg-dark-surface border border-gray-200 dark:border-gray-800 rounded-lg p-6 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Table Inventory</h2>
          <button
            onClick={handleExtractDetails}
            className="px-3 py-2 text-sm bg-gray-900 text-white rounded hover:opacity-90"
            disabled={loading || selectedTableIds.size === 0}
          >
            Extract Definitions ({selectedTableCount})
          </button>
        </div>

        {tables.length === 0 ? (
          <div className="text-sm text-light-text-secondary dark:text-dark-text-secondary">
            No tables loaded yet. Extract tables to populate the catalog.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700 text-sm">
              <thead className="bg-gray-50 dark:bg-gray-800">
                <tr>
                  <th className="px-4 py-2 text-left">
                    <input
                      type="checkbox"
                      checked={tables.length > 0 && selectedTableIds.size === tables.length}
                      onChange={toggleAllTables}
                    />
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Table</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Schema</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Rows</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Columns</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Primary Key</th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-dark-surface divide-y divide-gray-200 dark:divide-gray-700">
                {selectableTables.map((table) => (
                  <tr key={table.id}>
                    <td className="px-4 py-2">
                      <input
                        type="checkbox"
                        checked={selectedTableIds.has(table.id)}
                        onChange={() => toggleTable(table.id)}
                      />
                    </td>
                    <td className="px-4 py-2 font-medium text-light-text-primary dark:text-dark-text-primary">{table.table_name}</td>
                    <td className="px-4 py-2 text-light-text-secondary dark:text-dark-text-secondary">{table.schema_name}</td>
                    <td className="px-4 py-2 text-light-text-secondary dark:text-dark-text-secondary">{table.table_type}</td>
                    <td className="px-4 py-2 text-light-text-secondary dark:text-dark-text-secondary">{table.row_estimate ?? '-'}</td>
                    <td className="px-4 py-2 text-light-text-secondary dark:text-dark-text-secondary">{table.columns_count}</td>
                    <td className="px-4 py-2 text-light-text-secondary dark:text-dark-text-secondary">{table.primary_key || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="bg-white dark:bg-dark-surface border border-gray-200 dark:border-gray-800 rounded-lg p-6 shadow-sm space-y-4">
        <h2 className="text-lg font-semibold">Provision SharePoint List</h2>
        <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary">
          Generate a new SharePoint list from a selected source table definition.
        </p>

        {provisionError && (
          <div className="bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 p-3 rounded">
            {provisionError}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-light-text-primary dark:text-dark-text-primary">Source Table</label>
            <select
              name="tableId"
              value={provisionForm.tableId}
              onChange={handleProvisionChange}
              className="mt-1 w-full border border-gray-300 dark:border-gray-700 rounded p-2 bg-white dark:bg-dark-surface text-sm"
            >
              <option value="">Select table</option>
              {tables.map((table) => (
                <option key={table.id} value={table.id}>
                  {table.schema_name}.{table.table_name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-light-text-primary dark:text-dark-text-primary">SharePoint Connection</label>
            <select
              name="connectionId"
              value={provisionForm.connectionId}
              onChange={handleProvisionChange}
              className="mt-1 w-full border border-gray-300 dark:border-gray-700 rounded p-2 bg-white dark:bg-dark-surface text-sm"
            >
              <option value="">Select connection</option>
              {connections.map((conn) => (
                <option key={conn.id} value={conn.id}>{conn.tenant_id}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-light-text-primary dark:text-dark-text-primary">List Name</label>
            <input
              name="listName"
              value={provisionForm.listName}
              onChange={handleProvisionChange}
              className="mt-1 w-full border border-gray-300 dark:border-gray-700 rounded p-2 bg-white dark:bg-dark-surface text-sm"
              placeholder="e.g. Project Tracker"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-light-text-primary dark:text-dark-text-primary">Hostname</label>
            <input
              name="hostname"
              value={provisionForm.hostname}
              onChange={handleProvisionChange}
              className="mt-1 w-full border border-gray-300 dark:border-gray-700 rounded p-2 bg-white dark:bg-dark-surface text-sm"
              placeholder="contoso.sharepoint.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-light-text-primary dark:text-dark-text-primary">Site Path</label>
            <input
              name="sitePath"
              value={provisionForm.sitePath}
              onChange={handleProvisionChange}
              className="mt-1 w-full border border-gray-300 dark:border-gray-700 rounded p-2 bg-white dark:bg-dark-surface text-sm"
              placeholder="/sites/Operations"
            />
          </div>
        </div>
        
        {/* Advanced Toggle */}
        <div className="flex items-center space-x-2 pt-2">
            <input 
                type="checkbox" 
                id="advToggle" 
                checked={showAdvanced} 
                onChange={() => setShowAdvanced(!showAdvanced)}
                className="rounded border-gray-300 dark:border-gray-600 text-light-primary focus:ring-light-primary"
            />
            <label htmlFor="advToggle" className="text-sm font-medium text-light-text-primary dark:text-dark-text-primary select-none cursor-pointer">
                Show Advanced Settings (Column Mapping)
            </label>
        </div>

        {/* Dynamic Column Mapping UI */}
        {showAdvanced && currentTableColumns.length > 0 ? (
            <div className="bg-gray-50 dark:bg-gray-800/50 rounded p-4 border border-gray-200 dark:border-gray-700">
                <h3 className="text-sm font-semibold mb-2 text-light-text-primary dark:text-dark-text-primary">Column Mapping Preview</h3>
                <div className="overflow-x-auto max-h-64">
                    <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700 text-sm">
                        <thead className="bg-gray-100 dark:bg-gray-800 sticky top-0">
                            <tr>
                                <th className="px-3 py-2 text-left font-medium text-gray-500 dark:text-gray-400">Include</th>
                                <th className="px-3 py-2 text-left font-medium text-gray-500 dark:text-gray-400">Column Name</th>
                                <th className="px-3 py-2 text-left font-medium text-gray-500 dark:text-gray-400">Postgres Type</th>
                                <th className="px-3 py-2 text-left font-medium text-gray-500 dark:text-gray-400">SharePoint Type</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                            {currentTableColumns.map(col => {
                                const conf = columnConfig[col.column_name] || { included: true, type: 'text' };
                                return (
                                    <tr key={col.column_name}>
                                        <td className="px-3 py-2">
                                            <input 
                                                type="checkbox"
                                                checked={conf.included}
                                                onChange={(e) => handleAdvancedConfigChange(col.column_name, 'included', e.target.checked)}
                                                className="rounded border-gray-300 dark:border-gray-600"
                                            />
                                        </td>
                                        <td className="px-3 py-2 text-light-text-primary dark:text-dark-text-primary font-mono text-xs">{col.column_name}</td>
                                        <td className="px-3 py-2 text-light-text-secondary dark:text-dark-text-secondary text-xs">{col.data_type}</td>
                                        <td className="px-3 py-2">
                                            <select 
                                                value={conf.type}
                                                onChange={(e) => handleAdvancedConfigChange(col.column_name, 'type', e.target.value)}
                                                className="text-xs border border-gray-300 dark:border-gray-600 rounded p-1 bg-white dark:bg-dark-surface"
                                                disabled={!conf.included}
                                            >
                                                <option value="text">Text</option>
                                                <option value="number">Number</option>
                                                <option value="boolean">Boolean</option>
                                                <option value="dateTime">Date/Time</option>
                                            </select>
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            </div>
        ) : (
             // Simple Skip Columns Input (Only show if NOT advanced)
            !showAdvanced && (
                <div>
                  <label className="block text-sm font-medium text-light-text-primary dark:text-dark-text-primary">Skip Columns (optional)</label>
                  <input
                    name="skipColumns"
                    value={provisionForm.skipColumns}
                    onChange={handleProvisionChange}
                    className="mt-1 w-full border border-gray-300 dark:border-gray-700 rounded p-2 bg-white dark:bg-dark-surface text-sm"
                    placeholder="created_at, updated_at"
                  />
                  <p className="text-xs text-gray-500 mt-1">Comma-separated list of columns to exclude.</p>
                </div>
            )
        )}

        <div>
          <label className="block text-sm font-medium text-light-text-primary dark:text-dark-text-primary">Description</label>
          <textarea
            name="description"
            value={provisionForm.description}
            onChange={handleProvisionChange}
            className="mt-1 w-full border border-gray-300 dark:border-gray-700 rounded p-2 bg-white dark:bg-dark-surface text-sm"
            rows={3}
          />
        </div>

        <button
          onClick={handleProvision}
          className="px-4 py-2 bg-light-primary dark:bg-dark-primary text-white rounded hover:opacity-90"
          disabled={provisioning}
        >
          {provisioning ? 'Provisioning...' : 'Generate SharePoint List'}
        </button>

        {provisionResult && (
          <div className="bg-gray-50 dark:bg-gray-800/60 border border-gray-200 dark:border-gray-700 rounded p-4 text-sm space-y-2">
            <div className="font-semibold text-light-text-primary dark:text-dark-text-primary">Provisioning Summary</div>
            <div>List: {provisionResult.list?.displayName || provisionResult.list?.id}</div>
            <div>Columns created: {provisionResult.columns_created?.length || 0}</div>
            <div>Columns skipped: {provisionResult.columns_skipped?.length || 0}</div>
            {provisionResult.errors?.length > 0 && (
              <div className="text-red-600 dark:text-red-400">Errors: {provisionResult.errors.length}</div>
            )}
          </div>
        )}
      </section>
    </div>
  );
}
