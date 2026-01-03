import React, { useState } from 'react';
import { useRouter } from 'next/router';
import { createDatabaseInstance } from '../../services/api';

export default function NewDatabaseInstance() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    instance_label: '',
    host: '',
    port: 5432,
    db_name: '',
    username: '',
    role: 'PRIMARY',
    priority: 1,
    status: 'ACTIVE'
  });
  const [error, setError] = useState('');

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createDatabaseInstance(formData);
      router.push('/');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create instance');
    }
  };

  return (
    <div className="p-8 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-6 text-light-text-primary dark:text-dark-text-primary">New Database Instance</h1>
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

        <button
          type="submit"
          className="w-full bg-light-primary dark:bg-dark-primary text-white py-2 px-4 rounded hover:opacity-90 transition-opacity"
        >
          Create Instance
        </button>
      </form>
    </div>
  );
}
