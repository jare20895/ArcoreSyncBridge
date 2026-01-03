import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { createDatabase, getApplications } from '../../services/api';

export default function NewDatabase() {
  const router = useRouter();
  const [applications, setApplications] = useState<any[]>([]);
  const [formData, setFormData] = useState({
    application_id: '',
    name: '',
    db_type: 'POSTGRES',
    environment: 'DEV',
    database_name: '',
    status: 'ACTIVE'
  });
  const [error, setError] = useState('');

  useEffect(() => {
    loadApplications();
  }, []);

  const loadApplications = async () => {
    try {
      const data = await getApplications();
      setApplications(data);
    } catch (err) {
      console.error(err);
      setError('Failed to load applications');
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createDatabase(formData);
      router.push('/databases');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create database');
    }
  };

  return (
    <div className="p-8 max-w-2xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-light-text-primary dark:text-dark-text-primary">New Database</h1>
        <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary mt-1">Create a new logical database definition</p>
      </div>

      {error && <div className="bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 p-3 rounded mb-4">{error}</div>}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-light-text-primary dark:text-dark-text-primary">
            Application <span className="text-red-500">*</span>
          </label>
          <select
            name="application_id"
            value={formData.application_id}
            onChange={handleChange}
            required
            className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm p-2 bg-white dark:bg-dark-surface text-light-text-primary dark:text-dark-text-primary"
          >
            <option value="">Select an application...</option>
            {applications.map(app => (
              <option key={app.id} value={app.id}>{app.name}</option>
            ))}
          </select>
          {applications.length === 0 && (
            <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary mt-1">
              No applications found. <Link href="/applications/new" className="text-light-primary dark:text-dark-primary hover:underline">Create one first</Link>.
            </p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-light-text-primary dark:text-dark-text-primary">
            Name <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            name="name"
            value={formData.name}
            onChange={handleChange}
            required
            className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm p-2 bg-white dark:bg-dark-surface text-light-text-primary dark:text-dark-text-primary"
            placeholder="e.g., Customer Database"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-light-text-primary dark:text-dark-text-primary">
              Database Type <span className="text-red-500">*</span>
            </label>
            <select
              name="db_type"
              value={formData.db_type}
              onChange={handleChange}
              className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm p-2 bg-white dark:bg-dark-surface text-light-text-primary dark:text-dark-text-primary"
            >
              <option value="POSTGRES">PostgreSQL</option>
              <option value="MYSQL">MySQL</option>
              <option value="SQLSERVER">SQL Server</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-light-text-primary dark:text-dark-text-primary">
              Environment <span className="text-red-500">*</span>
            </label>
            <select
              name="environment"
              value={formData.environment}
              onChange={handleChange}
              className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm p-2 bg-white dark:bg-dark-surface text-light-text-primary dark:text-dark-text-primary"
            >
              <option value="DEV">Development</option>
              <option value="STAGING">Staging</option>
              <option value="PROD">Production</option>
            </select>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-light-text-primary dark:text-dark-text-primary">
            Database Name <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            name="database_name"
            value={formData.database_name}
            onChange={handleChange}
            required
            className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm p-2 bg-white dark:bg-dark-surface text-light-text-primary dark:text-dark-text-primary font-mono"
            placeholder="e.g., customer_db"
          />
          <p className="text-xs text-light-text-secondary dark:text-dark-text-secondary mt-1">
            The actual database name on the server
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-light-text-primary dark:text-dark-text-primary">
            Status
          </label>
          <select
            name="status"
            value={formData.status}
            onChange={handleChange}
            className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm p-2 bg-white dark:bg-dark-surface text-light-text-primary dark:text-dark-text-primary"
          >
            <option value="ACTIVE">ACTIVE</option>
            <option value="DISABLED">DISABLED</option>
          </select>
        </div>

        <div className="flex justify-between pt-4">
          <Link
            href="/databases"
            className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-200 rounded hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
          >
            Cancel
          </Link>
          <button
            type="submit"
            className="px-6 py-2 bg-light-primary dark:bg-dark-primary text-white rounded hover:opacity-90 transition-opacity"
          >
            Create Database
          </button>
        </div>
      </form>
    </div>
  );
}
