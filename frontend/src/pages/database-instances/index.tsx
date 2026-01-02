import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { getDatabaseInstances, triggerFailover } from '../../services/api';
import { Database, ShieldAlert, ArrowRight } from 'lucide-react';

export default function DatabaseInstancesList() {
  const [dbs, setDbs] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [failoverTarget, setFailoverTarget] = useState<any>(null); // Instance being promoted
  const [primaryToFail, setPrimaryToFail] = useState<string>('');

  useEffect(() => {
    loadDbs();
  }, []);

  const loadDbs = () => {
    getDatabaseInstances().then(setDbs).catch(console.error);
  };

  const handleFailover = async () => {
    if (!failoverTarget) return;
    setLoading(true);
    try {
        await triggerFailover({
            new_primary_instance_id: failoverTarget.id,
            old_primary_instance_id: primaryToFail || undefined
        });
        alert(`Successfully promoted ${failoverTarget.instance_label}`);
        setFailoverTarget(null);
        setPrimaryToFail('');
        loadDbs();
    } catch (e: any) {
        alert("Failover failed: " + (e.response?.data?.detail || e.message));
    } finally {
        setLoading(false);
    }
  };

  // Find current primary for default selection in modal
  const currentPrimary = dbs.find(d => d.role === 'PRIMARY');

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
             <h1 className="text-2xl font-bold font-secondary">Database Instances</h1>
             <p className="text-sm text-gray-500">Manage registered database nodes and replication topology.</p>
        </div>
        <Link href="/database-instances/new" className="bg-light-primary text-white px-4 py-2 rounded shadow-sm hover:bg-opacity-90">
          Register New Instance
        </Link>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {dbs.map((db) => (
            <div key={db.id} className="bg-white dark:bg-dark-surface p-6 rounded-lg border border-gray-200 dark:border-gray-800 shadow-sm flex justify-between items-center">
                <div className="flex items-center space-x-4">
                    <div className={`p-3 rounded-full ${db.role === 'PRIMARY' ? 'bg-light-primary/10 text-light-primary' : 'bg-gray-100 text-gray-500'}`}>
                        <Database size={24} />
                    </div>
                    <div>
                        <h3 className="text-lg font-bold flex items-center">
                            {db.instance_label}
                            {db.role === 'PRIMARY' && <span className="ml-2 px-2 py-0.5 rounded text-xs bg-blue-100 text-blue-800 font-bold">PRIMARY</span>}
                            {db.role === 'REPLICA' && <span className="ml-2 px-2 py-0.5 rounded text-xs bg-gray-100 text-gray-800">REPLICA</span>}
                            {db.status === 'INACTIVE' && <span className="ml-2 px-2 py-0.5 rounded text-xs bg-red-100 text-red-800">INACTIVE</span>}
                        </h3>
                        <p className="text-sm text-gray-500 font-mono">{db.host}:{db.port}</p>
                    </div>
                </div>
                
                <div>
                     {/* Actions */}
                     {db.role !== 'PRIMARY' && db.status === 'ACTIVE' && (
                         <button 
                            onClick={() => {
                                setFailoverTarget(db);
                                setPrimaryToFail(currentPrimary?.id || '');
                            }}
                            className="flex items-center space-x-2 text-sm text-light-warning hover:text-orange-700 px-3 py-1 border border-light-warning rounded"
                         >
                             <ShieldAlert size={16} />
                             <span>Promote to Primary</span>
                         </button>
                     )}
                </div>
            </div>
        ))}
        {dbs.length === 0 && <div className="text-center text-gray-500 py-8">No instances registered.</div>}
      </div>

      {/* Failover Modal */}
      {failoverTarget && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white dark:bg-dark-surface p-6 rounded-lg shadow-xl max-w-md w-full">
                <h3 className="text-xl font-bold mb-4 text-light-danger flex items-center">
                    <ShieldAlert className="mr-2" /> Confirm Failover
                </h3>
                <p className="text-sm text-gray-600 mb-6">
                    You are about to promote <strong>{failoverTarget.instance_label}</strong> to PRIMARY.
                    This will rebind all sync sources from the old primary to this instance.
                </p>
                
                <div className="mb-6">
                    <label className="block text-sm font-medium text-gray-700 mb-1">Old Primary (to mark FAILED)</label>
                    <select 
                        className="w-full border rounded p-2"
                        value={primaryToFail}
                        onChange={(e) => setPrimaryToFail(e.target.value)}
                    >
                        <option value="">-- None (Just Promote) --</option>
                        {dbs.filter(d => d.role === 'PRIMARY').map(d => (
                            <option key={d.id} value={d.id}>{d.instance_label} ({d.host})</option>
                        ))}
                    </select>
                </div>

                <div className="flex justify-end space-x-3">
                    <button 
                        onClick={() => setFailoverTarget(null)}
                        className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded"
                    >
                        Cancel
                    </button>
                    <button 
                        onClick={handleFailover}
                        disabled={loading}
                        className="px-4 py-2 bg-light-danger text-white rounded hover:bg-red-700 disabled:opacity-50"
                    >
                        {loading ? 'Promoting...' : 'Confirm Promotion'}
                    </button>
                </div>
            </div>
        </div>
      )}
    </div>
  );
}
