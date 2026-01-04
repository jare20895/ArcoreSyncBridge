import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8055';

const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
});

// Applications
export const getApplications = async () => {
  const res = await api.get('/applications/');
  return res.data;
};

export const getApplication = async (id: string) => {
  const res = await api.get(`/applications/${id}`);
  return res.data;
};

export const createApplication = async (data: any) => {
  const res = await api.post('/applications/', data);
  return res.data;
};

export const updateApplication = async (id: string, data: any) => {
  const res = await api.put(`/applications/${id}`, data);
  return res.data;
};

export const deleteApplication = async (id: string) => {
  const res = await api.delete(`/applications/${id}`);
  return res.data;
};

// Databases
export const getDatabases = async (applicationId?: string) => {
  const params = applicationId ? { application_id: applicationId } : {};
  const res = await api.get('/databases/', { params });
  return res.data;
};

export const getDatabase = async (id: string) => {
  const res = await api.get(`/databases/${id}`);
  return res.data;
};

export const createDatabase = async (data: any) => {
  const res = await api.post('/databases/', data);
  return res.data;
};

export const updateDatabase = async (id: string, data: any) => {
  const res = await api.put(`/databases/${id}`, data);
  return res.data;
};

export const deleteDatabase = async (id: string) => {
  const res = await api.delete(`/databases/${id}`);
  return res.data;
};

// Database Instances
export const getDatabaseInstances = async () => {
  const res = await api.get('/database-instances/');
  return res.data;
};

export const createDatabaseInstance = async (data: any) => {
  const res = await api.post('/database-instances/', data);
  return res.data;
};

export const updateDatabaseInstance = async (id: string, data: any) => {
  const res = await api.put(`/database-instances/${id}`, data);
  return res.data;
};

export const deleteDatabaseInstance = async (id: string) => {
  const res = await api.delete(`/database-instances/${id}`);
  return res.data;
};

export const testDatabaseConnection = async (data: any) => {
  // If instance_id is provided (editing mode with no password), use stored credentials
  if (data.instance_id && !data.password) {
    const res = await api.post(`/database-instances/${data.instance_id}/test-connection`);
    return res.data;
  }
  // Otherwise test with provided credentials
  const { instance_id, ...connectionData } = data;
  const res = await api.post('/database-instances/test-connection', connectionData);
  return res.data;
};

// Data Sources (Database Inventory)
export const getSourceTables = async (databaseId: string) => {
  const res = await api.get('/data-sources/tables', { params: { database_id: databaseId } });
  return res.data;
};

export const extractSourceTables = async (data: { database_id: string; instance_id: string; schema?: string }) => {
  const res = await api.post('/data-sources/tables/extract', data);
  return res.data;
};

export const extractSourceTableDetails = async (data: { instance_id: string; table_ids: string[] }) => {
  const res = await api.post('/data-sources/tables/extract-details', data);
  return res.data;
};

export const getSourceTableDetails = async (tableId: string) => {
  const res = await api.get(`/data-sources/tables/${tableId}`);
  return res.data;
};

export const provisionSharePointList = async (data: any) => {
  const res = await api.post('/provisioning/list', data);
  return res.data;
};

export const getConnections = async () => {
  const res = await api.get('/sharepoint-connections/');
  return res.data;
};

export const createConnection = async (data: any) => {
  const res = await api.post('/sharepoint-connections/', data);
  return res.data;
};

export const updateConnection = async (id: string, data: any) => {
  const res = await api.put(`/sharepoint-connections/${id}`, data);
  return res.data;
};

// Data Targets (SharePoint Inventory)
export const getSharePointSites = async (connectionId?: string) => {
  const res = await api.get('/data-targets/sites', {
    params: connectionId ? { connection_id: connectionId } : {}
  });
  return res.data;
};

export const extractSharePointSites = async (connectionId: string, query: string = "*") => {
  const res = await api.post('/data-targets/sites/extract', null, {
    params: { connection_id: connectionId, query }
  });
  return res.data;
};

export const resolveSharePointSite = async (data: { connection_id: string; hostname: string; site_path: string }) => {
  const res = await api.post('/data-targets/sites/resolve', data);
  return res.data;
};

export const getSharePointLists = async (siteId: string) => {
  const res = await api.get(`/data-targets/sites/${siteId}/lists`);
  return res.data;
};

export const extractSharePointLists = async (siteId: string) => {
  const res = await api.post(`/data-targets/sites/${siteId}/lists/extract`);
  return res.data;
};

export const getSharePointListsBySourceTable = async (tableId: string) => {
  const res = await api.get('/data-targets/lists/by-source', {
    params: { source_table_id: tableId }
  });
  return res.data;
};

export const getSharePointColumns = async (listId: string) => {
  const res = await api.get(`/data-targets/lists/${listId}/columns`);
  return res.data;
};

export const extractSharePointColumns = async (listId: string) => {
  const res = await api.post(`/data-targets/lists/${listId}/columns/extract`);
  return res.data;
};

export const getSyncDefinitions = async () => {
  const res = await api.get('/sync-definitions/');
  return res.data;
};

export const getSyncDefinition = async (id: string) => {
  const res = await api.get(`/sync-definitions/${id}`);
  return res.data;
};

export const createSyncDefinition = async (data: any) => {
  const res = await api.post('/sync-definitions/', data);
  return res.data;
};

export const updateSyncDefinition = async (id: string, data: any) => {
  const res = await api.put(`/sync-definitions/${id}`, data);
  return res.data;
};

export const deleteSyncDefinition = async (id: string) => {
  const res = await api.delete(`/sync-definitions/${id}`);
  return res.data;
};

// Field Mappings
export const getFieldMappings = async (syncDefId: string) => {
  const res = await api.get(`/field-mappings/sync-definition/${syncDefId}`);
  return res.data;
};

export const createFieldMapping = async (syncDefId: string, data: any) => {
  const res = await api.post(`/field-mappings/?sync_def_id=${syncDefId}`, data);
  return res.data;
};

export const updateFieldMapping = async (mappingId: string, data: any) => {
  const res = await api.put(`/field-mappings/${mappingId}`, data);
  return res.data;
};

export const deleteFieldMapping = async (mappingId: string) => {
  const res = await api.delete(`/field-mappings/${mappingId}`);
  return res.data;
};

export const bulkUpdateFieldMappings = async (syncDefId: string, mappings: any[]) => {
  const res = await api.post(`/field-mappings/sync-definition/${syncDefId}/bulk`, mappings);
  return res.data;
};

export const generateDriftReport = async (data: { sync_def_id: string, check_type: string }) => {
  const res = await api.post('/ops/drift-report', data);
  return res.data;
};

export const triggerFailover = async (data: { new_primary_instance_id: string, old_primary_instance_id?: string }) => {
  const res = await api.post('/ops/failover', data);
  return res.data;
};

export const triggerSync = async (syncDefId: string) => {
  const res = await api.post(`/ops/sync/${syncDefId}`);
  return res.data;
};

export const resetSyncCursors = async (syncDefId: string) => {
  const res = await api.delete(`/ops/sync/${syncDefId}/cursors`);
  return res.data;
};

export const getSyncRuns = async () => {
  const res = await api.get('/runs/');
  return res.data;
};

export default api;
