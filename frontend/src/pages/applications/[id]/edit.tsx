import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { getApplication, updateApplication } from '../../../services/api';

export default function EditApplication() {
  const router = useRouter();
  const { id } = router.query;
  const [loading, setLoading] = useState(true);
  const [formData, setFormData] = useState({
    name: '',
    owner_team: '',
    description: '',
    status: 'ACTIVE'
  });
  const [error, setError] = useState('');

  useEffect(() => {
    if (!id) return;
    loadApplication();
  }, [id]);

  const loadApplication = async () => {
    try {
      const app = await getApplication(id as string);
      setFormData({
        name: app.name || '',
        owner_team: app.owner_team || '',
        description: app.description || '',
        status: app.status || 'ACTIVE'
      });
    } catch (err) {
      console.error(err);
      setError('Failed to load application');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await updateApplication(id as string, formData);
      router.push('/applications');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update application');
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
        <h1 className="text-2xl font-bold text-light-text-primary dark:text-dark-text-primary">Edit Application</h1>
        <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary mt-1">Update application details</p>
      </div>

      {error && <div className="bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 p-3 rounded mb-4">{error}</div>}

      <form onSubmit={handleSubmit} className="space-y-4">
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
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-light-text-primary dark:text-dark-text-primary">
            Owner Team
          </label>
          <input
            type="text"
            name="owner_team"
            value={formData.owner_team}
            onChange={handleChange}
            className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm p-2 bg-white dark:bg-dark-surface text-light-text-primary dark:text-dark-text-primary"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-light-text-primary dark:text-dark-text-primary">
            Description
          </label>
          <textarea
            name="description"
            value={formData.description}
            onChange={handleChange}
            rows={3}
            className="mt-1 block w-full border border-gray-300 dark:border-gray-600 rounded-md shadow-sm p-2 bg-white dark:bg-dark-surface text-light-text-primary dark:text-dark-text-primary"
          />
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
            <option value="ARCHIVED">ARCHIVED</option>
          </select>
        </div>

        <div className="flex justify-between pt-4">
          <Link
            href="/applications"
            className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-200 rounded hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
          >
            Cancel
          </Link>
          <button
            type="submit"
            className="px-6 py-2 bg-light-primary dark:bg-dark-primary text-white rounded hover:opacity-90 transition-opacity"
          >
            Update Application
          </button>
        </div>
      </form>
    </div>
  );
}
