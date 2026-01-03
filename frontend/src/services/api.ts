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

export const getSyncDefinitions = async () => {
  const res = await api.get('/sync-definitions/');
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

export const getSyncRuns = async () => {
  const res = await api.get('/runs/');
  return res.data;
};

export default api;
