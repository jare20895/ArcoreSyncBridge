import React, { useState } from 'react';
import { useRouter } from 'next/router';
import Layout from '../../components/Layout';
import { createConnection } from '../../services/api';
import { ArrowLeft, Save } from 'lucide-react';

export default function NewSharePointConnection() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    tenant_id: '',
    client_id: '',
    client_secret: '',
    authority_host: 'https://login.microsoftonline.com',
    scopes: 'https://graph.microsoft.com/.default',
    status: 'ACTIVE'
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      // Convert comma-separated scopes to array
      const payload = {
          ...formData,
          scopes: formData.scopes.split(',').map(s => s.trim()).filter(s => s)
      };
      
      await createConnection(payload);
      router.push('/settings'); // Redirect to Settings > Integrations
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to create connection');
    } finally {
        setLoading(false);
    }
  };

  return (
    <Layout>
      <div className="max-w-2xl mx-auto">
        <div className="flex items-center space-x-4 mb-6">
            <button onClick={() => router.back()} className="p-2 rounded hover:bg-gray-100">
                <ArrowLeft size={20} />
            </button>
            <h1 className="text-2xl font-bold font-secondary text-gray-900 dark:text-white">New SharePoint Connection</h1>
        </div>

        {error && <div className="bg-red-50 text-red-700 p-4 rounded-lg border border-red-200 mb-6">{error}</div>}
        
        <form onSubmit={handleSubmit} className="bg-white dark:bg-gray-800 p-6 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Tenant ID</label>
              <input
                type="text"
                name="tenant_id"
                value={formData.tenant_id}
                onChange={handleChange}
                required
                placeholder="e.g. dae01a42-..."
                className="w-full border-gray-300 dark:border-gray-600 rounded-lg shadow-sm p-2.5 text-sm dark:bg-gray-700 dark:text-white"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Client ID</label>
              <input
                type="text"
                name="client_id"
                value={formData.client_id}
                onChange={handleChange}
                required
                placeholder="e.g. afd34488-..."
                className="w-full border-gray-300 dark:border-gray-600 rounded-lg shadow-sm p-2.5 text-sm dark:bg-gray-700 dark:text-white"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Client Secret</label>
            <input
              type="password"
              name="client_secret"
              value={formData.client_secret}
              onChange={handleChange}
              required
              className="w-full border-gray-300 dark:border-gray-600 rounded-lg shadow-sm p-2.5 text-sm dark:bg-gray-700 dark:text-white"
            />
          </div>

          <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Authority Host</label>
              <input
                type="text"
                name="authority_host"
                value={formData.authority_host}
                onChange={handleChange}
                className="w-full border-gray-300 dark:border-gray-600 rounded-lg shadow-sm p-2.5 text-sm dark:bg-gray-700 dark:text-white"
              />
          </div>
          
          <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Scopes (comma separated)</label>
              <input
                type="text"
                name="scopes"
                value={formData.scopes}
                onChange={handleChange}
                className="w-full border-gray-300 dark:border-gray-600 rounded-lg shadow-sm p-2.5 text-sm dark:bg-gray-700 dark:text-white"
              />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Status</label>
            <select
              name="status"
              value={formData.status}
              onChange={handleChange}
              className="w-full border-gray-300 dark:border-gray-600 rounded-lg shadow-sm p-2.5 text-sm dark:bg-gray-700 dark:text-white"
            >
              <option value="ACTIVE">ACTIVE</option>
              <option value="INACTIVE">INACTIVE</option>
            </select>
          </div>

          <div className="pt-4 flex justify-end">
            <button
              type="submit"
              disabled={loading}
              className="flex items-center space-x-2 bg-light-primary text-white py-2.5 px-6 rounded-lg hover:bg-opacity-90 disabled:opacity-50 font-medium transition-colors"
            >
              <Save size={18} />
              <span>{loading ? 'Creating...' : 'Create Connection'}</span>
            </button>
          </div>
        </form>
      </div>
    </Layout>
  );
}
