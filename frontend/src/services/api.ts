import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8055';

const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
});

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
