import React, { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import { Save, Globe, Lock, Shield, User, Database, Cloud, Edit2, EyeOff } from 'lucide-react';
import { getDatabaseInstances, getConnections, updateDatabaseInstance, updateConnection } from '../services/api';

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState('integrations');
  const [dbInstances, setDbInstances] = useState<any[]>([]);
  const [spConnections, setSpConnections] = useState<any[]>([]);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [newSecret, setNewSecret] = useState('');

  useEffect(() => {
    if (activeTab === 'security' || activeTab === 'integrations') {
        fetchData();
    }
  }, [activeTab]);

  const fetchData = async () => {
      try {
          const [dbs, conns] = await Promise.all([getDatabaseInstances(), getConnections()]);
          setDbInstances(dbs);
          setSpConnections(conns);
      } catch (e) {
          console.error("Failed to fetch settings data", e);
      }
  };

  const handleSaveSecret = async (type: 'DB' | 'SP', id: string) => {
      try {
          if (type === 'DB') {
              await updateDatabaseInstance(id, { password: newSecret });
          } else {
              await updateConnection(id, { client_secret: newSecret });
          }
          alert("Secret updated successfully");
          setEditingId(null);
          setNewSecret('');
      } catch (e) {
          console.error(e);
          alert("Failed to update secret");
      }
  };

  return (
    <Layout>
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold font-secondary text-gray-900 dark:text-white mb-8">Settings</h1>

        <div className="flex flex-col md:flex-row gap-8">
          {/* Sidebar Navigation */}
          <nav className="w-full md:w-64 space-y-1">
            <button
              onClick={() => setActiveTab('integrations')}
              className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                activeTab === 'integrations'
                  ? 'bg-light-primary text-white shadow-md'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
              }`}
            >
              <Globe size={18} />
              <span>Integrations</span>
            </button>
            <button
              onClick={() => setActiveTab('security')}
              className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                activeTab === 'security'
                  ? 'bg-light-primary text-white shadow-md'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
              }`}
            >
              <Lock size={18} />
              <span>Security & Secrets</span>
            </button>
            <button
              onClick={() => setActiveTab('profile')}
              className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                activeTab === 'profile'
                  ? 'bg-light-primary text-white shadow-md'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
              }`}
            >
              <User size={18} />
              <span>Profile</span>
            </button>
          </nav>

          {/* Main Content Area */}
          <div className="flex-1 bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-800 p-6">
            {activeTab === 'integrations' && (
              <div className="space-y-6">
                <div>
                  <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Microsoft 365</h2>
                  <p className="text-sm text-gray-500">Manage connections to SharePoint and Graph API.</p>
                </div>

                <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                  <div className="flex items-start">
                    <Shield className="text-blue-600 dark:text-blue-400 mt-1 mr-3" size={20} />
                    <div>
                      <h3 className="font-medium text-blue-900 dark:text-blue-100">Credential Management</h3>
                      <p className="text-sm text-blue-700 dark:text-blue-300 mt-1">
                        Credentials are stored securely in the database (encrypted) or loaded from environment variables.
                      </p>
                    </div>
                  </div>
                </div>

                {/* Connection List */}
                <div className="space-y-4">
                    <div className="flex justify-between items-center">
                        <h3 className="font-medium text-light-text-primary dark:text-dark-text-primary">Active Connections</h3>
                        <a href="/sharepoint-connections/new" className="text-sm text-light-primary dark:text-dark-primary hover:underline font-medium">Add New</a>
                    </div>

                    <div className="border border-gray-200 dark:border-gray-700 rounded-lg divide-y divide-gray-200 dark:divide-gray-700 bg-white dark:bg-gray-800">
                        {spConnections.map(conn => (
                            <div key={conn.id} className="p-4 flex justify-between items-center">
                                <div>
                                    <div className="font-medium text-light-text-primary dark:text-dark-text-primary">Tenant: {conn.tenant_id}</div>
                                    <div className="text-xs text-light-text-secondary dark:text-dark-text-secondary">Client ID: {conn.client_id}</div>
                                </div>
                                <span className={`px-2 py-1 text-xs rounded-full ${conn.status === 'ACTIVE' ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300' : 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300'}`}>
                                    {conn.status}
                                </span>
                            </div>
                        ))}
                        {spConnections.length === 0 && <div className="p-4 text-sm text-light-text-secondary dark:text-dark-text-secondary italic">No connections found.</div>}
                    </div>
                    
                    <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                        <h3 className="font-medium mb-3 text-light-text-primary dark:text-dark-text-primary">Global API Settings</h3>
                        <div className="grid grid-cols-1 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-light-text-primary dark:text-dark-text-primary mb-1">Graph API Version</label>
                                <select className="w-full border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm p-2 border bg-white dark:bg-dark-surface text-light-text-primary dark:text-dark-text-primary">
                                    <option>v1.0 (Recommended)</option>
                                    <option>beta</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-light-text-primary dark:text-dark-text-primary mb-1">Throttling Threshold (ms)</label>
                                <input type="number" className="w-full border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm p-2 border bg-white dark:bg-dark-surface text-light-text-primary dark:text-dark-text-primary" defaultValue={500} />
                            </div>
                        </div>
                        <div className="mt-4 flex justify-end">
                            <button className="flex items-center space-x-2 px-4 py-2 bg-light-primary dark:bg-dark-primary text-white rounded-md text-sm font-medium hover:bg-opacity-90">
                                <Save size={16} />
                                <span>Save Changes</span>
                            </button>
                        </div>
                    </div>
                </div>
              </div>
            )}

            {activeTab === 'security' && (
              <div className="space-y-8">
                <div>
                    <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Secrets Management</h2>
                    <p className="text-sm text-gray-500">Update credentials for databases and integrations.</p>
                </div>

                {/* Database Secrets */}
                <div className="space-y-4">
                    <h3 className="text-sm font-bold uppercase text-light-text-secondary dark:text-dark-text-secondary tracking-wider flex items-center">
                        <Database size={16} className="mr-2"/> Database Instances
                    </h3>
                    <div className="border border-gray-200 dark:border-gray-700 rounded-lg divide-y divide-gray-200 dark:divide-gray-700 bg-white dark:bg-gray-800">
                        {dbInstances.map(db => (
                            <div key={db.id} className="p-4 flex justify-between items-center">
                                <div>
                                    <div className="font-medium text-light-text-primary dark:text-dark-text-primary">{db.instance_label}</div>
                                    <div className="text-xs text-light-text-secondary dark:text-dark-text-secondary">{db.host}:{db.port}</div>
                                </div>
                                {editingId === db.id ? (
                                    <div className="flex items-center space-x-2">
                                        <input
                                            type="password"
                                            className="border border-gray-300 dark:border-gray-600 rounded px-2 py-1 text-sm bg-white dark:bg-dark-surface text-light-text-primary dark:text-dark-text-primary"
                                            placeholder="New Password"
                                            value={newSecret}
                                            onChange={(e) => setNewSecret(e.target.value)}
                                        />
                                        <button onClick={() => handleSaveSecret('DB', db.id)} className="text-green-600 dark:text-green-400 hover:text-green-700 dark:hover:text-green-300 text-sm font-medium">Save</button>
                                        <button onClick={() => {setEditingId(null); setNewSecret('');}} className="text-gray-500 dark:text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 text-sm">Cancel</button>
                                    </div>
                                ) : (
                                    <button
                                        onClick={() => {setEditingId(db.id); setNewSecret('');}}
                                        className="flex items-center space-x-1 px-3 py-1.5 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded text-xs font-medium text-gray-700 dark:text-gray-200 transition-colors"
                                    >
                                        <Edit2 size={12} />
                                        <span>Update Password</span>
                                    </button>
                                )}
                            </div>
                        ))}
                        {dbInstances.length === 0 && <div className="p-4 text-sm text-light-text-secondary dark:text-dark-text-secondary italic">No database instances found.</div>}
                    </div>
                </div>

                {/* SharePoint Secrets */}
                <div className="space-y-4">
                    <h3 className="text-sm font-bold uppercase text-light-text-secondary dark:text-dark-text-secondary tracking-wider flex items-center">
                        <Cloud size={16} className="mr-2"/> SharePoint Connections
                    </h3>
                    <div className="border border-gray-200 dark:border-gray-700 rounded-lg divide-y divide-gray-200 dark:divide-gray-700 bg-white dark:bg-gray-800">
                        {spConnections.map(conn => (
                            <div key={conn.id} className="p-4 flex justify-between items-center">
                                <div>
                                    <div className="font-medium text-light-text-primary dark:text-dark-text-primary">Tenant: {conn.tenant_id}</div>
                                    <div className="text-xs text-light-text-secondary dark:text-dark-text-secondary">Client ID: {conn.client_id}</div>
                                </div>
                                {editingId === conn.id ? (
                                    <div className="flex items-center space-x-2">
                                        <input
                                            type="password"
                                            className="border border-gray-300 dark:border-gray-600 rounded px-2 py-1 text-sm bg-white dark:bg-dark-surface text-light-text-primary dark:text-dark-text-primary"
                                            placeholder="New Client Secret"
                                            value={newSecret}
                                            onChange={(e) => setNewSecret(e.target.value)}
                                        />
                                        <button onClick={() => handleSaveSecret('SP', conn.id)} className="text-green-600 dark:text-green-400 hover:text-green-700 dark:hover:text-green-300 text-sm font-medium">Save</button>
                                        <button onClick={() => {setEditingId(null); setNewSecret('');}} className="text-gray-500 dark:text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 text-sm">Cancel</button>
                                    </div>
                                ) : (
                                    <button
                                        onClick={() => {setEditingId(conn.id); setNewSecret('');}}
                                        className="flex items-center space-x-1 px-3 py-1.5 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded text-xs font-medium text-gray-700 dark:text-gray-200 transition-colors"
                                    >
                                        <Edit2 size={12} />
                                        <span>Update Secret</span>
                                    </button>
                                )}
                            </div>
                        ))}
                        {spConnections.length === 0 && <div className="p-4 text-sm text-light-text-secondary dark:text-dark-text-secondary italic">No connections found.</div>}
                    </div>
                </div>
              </div>
            )}

            {activeTab === 'profile' && (
              <div className="text-center py-12 text-light-text-secondary dark:text-dark-text-secondary">
                <User size={48} className="mx-auto mb-4 text-gray-300 dark:text-gray-600" />
                <h3 className="text-lg font-medium text-light-text-primary dark:text-dark-text-primary">User Profile</h3>
                <p>Manage your account settings and preferences.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
}
