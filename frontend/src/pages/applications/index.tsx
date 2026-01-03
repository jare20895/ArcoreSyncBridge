import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { Plus, Edit, Trash2 } from 'lucide-react';
import { getApplications, deleteApplication } from '../../services/api';

export default function ApplicationsPage() {
  const [applications, setApplications] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
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
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string, name: string) => {
    if (window.confirm(`Are you sure you want to delete application "${name}"? This will delete all associated databases and instances.`)) {
      try {
        await deleteApplication(id);
        loadApplications();
      } catch (err: any) {
        alert(err.response?.data?.detail || 'Failed to delete application');
      }
    }
  };

  if (loading) {
    return (
      <div className="p-8">
        <div className="text-light-text-primary dark:text-dark-text-primary">Loading...</div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-light-text-primary dark:text-dark-text-primary">Applications</h1>
          <p className="text-sm text-light-text-secondary dark:text-dark-text-secondary mt-1">
            Manage your applications and product domains
          </p>
        </div>
        <Link
          href="/applications/new"
          className="flex items-center space-x-2 px-4 py-2 bg-light-primary dark:bg-dark-primary text-white rounded hover:opacity-90 transition-opacity"
        >
          <Plus size={20} />
          <span>New Application</span>
        </Link>
      </div>

      {error && <div className="bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 p-3 rounded mb-4">{error}</div>}

      <div className="bg-light-surface dark:bg-dark-surface border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50 dark:bg-gray-800">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Name</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Owner Team</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Created</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {applications.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-6 py-8 text-center text-light-text-secondary dark:text-dark-text-secondary">
                  No applications found. Create your first application to get started.
                </td>
              </tr>
            ) : (
              applications.map((app) => (
                <tr key={app.id} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
                  <td className="px-6 py-4">
                    <Link href={`/applications/${app.id}`} className="text-light-primary dark:text-dark-primary hover:underline font-medium">
                      {app.name}
                    </Link>
                    {app.description && (
                      <div className="text-xs text-light-text-secondary dark:text-dark-text-secondary mt-1">{app.description}</div>
                    )}
                  </td>
                  <td className="px-6 py-4 text-sm text-light-text-primary dark:text-dark-text-primary">
                    {app.owner_team || '-'}
                  </td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      app.status === 'ACTIVE'
                        ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300'
                        : 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300'
                    }`}>
                      {app.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-light-text-secondary dark:text-dark-text-secondary">
                    {new Date(app.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 text-right text-sm">
                    <div className="flex items-center justify-end space-x-3">
                      <Link href={`/applications/${app.id}/edit`} className="text-light-primary dark:text-dark-primary hover:underline flex items-center space-x-1">
                        <Edit size={14} />
                        <span>Edit</span>
                      </Link>
                      <button
                        onClick={() => handleDelete(app.id, app.name)}
                        className="text-red-600 dark:text-red-400 hover:underline flex items-center space-x-1"
                      >
                        <Trash2 size={14} />
                        <span>Delete</span>
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
