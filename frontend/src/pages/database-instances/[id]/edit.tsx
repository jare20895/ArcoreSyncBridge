import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { getDatabaseInstances, updateDatabaseInstance, testDatabaseConnection } from '../../../services/api';

export default function EditDatabaseInstance() {
  const router = useRouter();
  const { id } = router.query;
  const [loading, setLoading] = useState(true);
  const [formData, setFormData] = useState({
    instance_label: '',
    host: '',
    port: 5432,
    db_name: '',
    username: '',
    password: '',
    role: 'PRIMARY',
    priority: 1,
    status: 'ACTIVE'
  });
  const [error, setError] = useState('');
  const [testStatus, setTestStatus] = useState<'idle' | 'testing' | 'success' | 'error'>('idle');
  const [testMessage, setTestMessage] = useState('');

  useEffect(() => {
    if (!id) return;
    loadInstance();
  }, [id]);

  const loadInstance = async () => {
    try {
      const instances = await getDatabaseInstances();
      const instance = instances.find((inst: any) => inst.id === id);
      if (instance) {
        setFormData({
          instance_label: instance.instance_label || '',
          host: instance.host || '',
          port: instance.port || 5432,
          db_name: instance.db_name || '',
          username: instance.username || '',
          password: '', // Don't populate password for security
          role: instance.role || 'PRIMARY',
          priority: instance.priority || 1,
          status: instance.status || 'ACTIVE'
        });
      } else {
        setError('Instance not found');
      }
    } catch (err) {
      console.error(err);
      setError('Failed to load instance');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleTestConnection = async () => {
    setTestStatus('testing');
    setTestMessage('');
    try {
      // If password is blank on edit form, test using existing instance credentials
      if (!formData.password && id) {
        // Use the instance-specific test endpoint that uses stored credentials
        const result = await testDatabaseConnection({
          host: formData.host,
          port: formData.port,
          db_name: formData.db_name,
          username: formData.username,
          password: formData.password,
          instance_id: id as string
        });
        setTestStatus('success');
        setTestMessage(result.message || 'Connection successful! (using stored password)');
      } else {
        // Test with provided password
        const result = await testDatabaseConnection({
          host: formData.host,
          port: formData.port,
          db_name: formData.db_name,
          username: formData.username,
          password: formData.password
        });
        setTestStatus('success');
        setTestMessage(result.message || 'Connection successful!');
      }
    } catch (err: any) {
      setTestStatus('error');
      setTestMessage(err.response?.data?.detail || 'Connection failed');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      // Only include password if it was changed
      const updateData: any = {
        instance_label: formData.instance_label,
        host: formData.host,
        port: formData.port,
        db_name: formData.db_name,
        username: formData.username,
        role: formData.role,
        priority: formData.priority,
        status: formData.status
      };

      // Only include password if it was provided
      if (formData.password) {
        updateData.password = formData.password;
      }

      await updateDatabaseInstance(id as string, updateData);
      router.push('/');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update instance');
    }
  };

  if (loading) {
    return (
      <div className="p-8 max-w-2xl mx-auto">
        <div className="text-light-text-primary dark:text-dark-text-primary">Loading...</div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-2xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-light-text-primary dark:text-dark-text-primary">Edit Database Instance</h1>
        <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary mt-1">Update connection details for this database instance</p>
      </div>
      {error && <div className="bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 p-3 rounded mb-4">{error}</div>}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-light-text-primary dark:text-dark-text-primary">Label</label>
          <input
            type="text"
            name="instance_label"
            value={formData.instance_label}
            onChange={handleChange}
            required
            className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm p-2 bg-white dark:bg-dark-surface text-light-text-primary dark:text-dark-text-primary"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-light-text-primary dark:text-dark-text-primary">Host</label>
            <input
              type="text"
              name="host"
              value={formData.host}
              onChange={handleChange}
              required
              className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm p-2 bg-white dark:bg-dark-surface text-light-text-primary dark:text-dark-text-primary"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-light-text-primary dark:text-dark-text-primary">Port</label>
            <input
              type="number"
              name="port"
              value={formData.port}
              onChange={handleChange}
              required
              className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm p-2 bg-white dark:bg-dark-surface text-light-text-primary dark:text-dark-text-primary"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-light-text-primary dark:text-dark-text-primary">Database Name</label>
            <input
              type="text"
              name="db_name"
              value={formData.db_name}
              onChange={handleChange}
              required
              className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm p-2 bg-white dark:bg-dark-surface text-light-text-primary dark:text-dark-text-primary"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-light-text-primary dark:text-dark-text-primary">Username</label>
            <input
              type="text"
              name="username"
              value={formData.username}
              onChange={handleChange}
              required
              className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm p-2 bg-white dark:bg-dark-surface text-light-text-primary dark:text-dark-text-primary"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-light-text-primary dark:text-dark-text-primary">Password</label>
          <input
            type="password"
            name="password"
            value={formData.password}
            onChange={handleChange}
            placeholder="Leave blank to keep current password"
            className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm p-2 bg-white dark:bg-dark-surface text-light-text-primary dark:text-dark-text-primary placeholder-gray-400 dark:placeholder-gray-500"
          />
          <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary mt-1">Only enter if you want to change the password</p>
        </div>

        <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
          <div className="flex items-center space-x-3">
            <button
              type="button"
              onClick={handleTestConnection}
              disabled={testStatus === 'testing' || !formData.host || !formData.db_name || !formData.username}
              className="flex items-center space-x-2 px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-200 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
            {testStatus === 'testing' ? (
              <>
                <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span>Testing Connection...</span>
              </>
            ) : (
              <>
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>Test Connection</span>
              </>
            )}
            </button>
            {!formData.password && (
              <span className="text-xs text-light-text-secondary dark:text-dark-text-secondary italic">
                Will use stored password
              </span>
            )}
          </div>
          {testMessage && (
            <div className={`mt-3 p-3 rounded text-sm ${
              testStatus === 'success'
                ? 'bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-300 border border-green-200 dark:border-green-700'
                : 'bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-400 border border-red-200 dark:border-red-700'
            }`}>
              {testMessage}
            </div>
          )}
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-light-text-primary dark:text-dark-text-primary">Role</label>
            <select
              name="role"
              value={formData.role}
              onChange={handleChange}
              className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm p-2 bg-white dark:bg-dark-surface text-light-text-primary dark:text-dark-text-primary"
            >
              <option value="PRIMARY">PRIMARY</option>
              <option value="READ_REPLICA">READ_REPLICA</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-light-text-primary dark:text-dark-text-primary">Status</label>
            <select
              name="status"
              value={formData.status}
              onChange={handleChange}
              className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm p-2 bg-white dark:bg-dark-surface text-light-text-primary dark:text-dark-text-primary"
            >
              <option value="ACTIVE">ACTIVE</option>
              <option value="MAINTENANCE">MAINTENANCE</option>
              <option value="INACTIVE">INACTIVE</option>
            </select>
          </div>
        </div>

        <div className="flex justify-between pt-4">
          <Link
            href="/"
            className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-200 rounded hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
          >
            Cancel
          </Link>
          <button
            type="submit"
            className="w-full ml-4 bg-light-primary dark:bg-dark-primary text-white py-2 px-4 rounded hover:opacity-90 transition-opacity"
          >
            Update Instance
          </button>
        </div>
      </form>
    </div>
  );
}
