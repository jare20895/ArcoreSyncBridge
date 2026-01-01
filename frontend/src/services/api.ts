import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1', // Assuming backend on 8000 via proxy or direct
});

export const getDatabaseInstances = async () => {
  const res = await api.get('/database-instances/');
  return res.data;
};

export const getConnections = async () => {
  const res = await api.get('/sharepoint-connections/');
  return res.data;
};

export default api;
