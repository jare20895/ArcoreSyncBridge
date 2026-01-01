import React, { useEffect, useState } from 'react';
import { getDatabaseInstances, getConnections } from '../services/api';

export default function Dashboard() {
  const [dbs, setDbs] = useState([]);
  const [conns, setConns] = useState([]);

  useEffect(() => {
    getDatabaseInstances().then(setDbs).catch(console.error);
    getConnections().then(setConns).catch(console.error);
  }, []);

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-6">Arcore SyncBridge Dashboard</h1>
      
      <div className="grid grid-cols-2 gap-8">
        <div className="border p-4 rounded shadow">
          <h2 className="text-xl font-semibold mb-4">Database Instances</h2>
          <ul>
            {dbs.map((db: any) => (
              <li key={db.id} className="border-b py-2 flex justify-between">
                <span>{db.instance_label}</span>
                <span className={`px-2 rounded text-sm ${db.status === 'ACTIVE' ? 'bg-green-100 text-green-800' : 'bg-red-100'}`}>
                  {db.status}
                </span>
              </li>
            ))}
            {dbs.length === 0 && <p className="text-gray-500">No database instances found.</p>}
          </ul>
        </div>

        <div className="border p-4 rounded shadow">
          <h2 className="text-xl font-semibold mb-4">SharePoint Connections</h2>
          <ul>
            {conns.map((conn: any) => (
              <li key={conn.id} className="border-b py-2 flex justify-between">
                <span>{conn.tenant_id}</span>
                <span className={`px-2 rounded text-sm ${conn.status === 'ACTIVE' ? 'bg-green-100 text-green-800' : 'bg-red-100'}`}>
                  {conn.status}
                </span>
              </li>
            ))}
            {conns.length === 0 && <p className="text-gray-500">No connections found.</p>}
          </ul>
        </div>
      </div>
    </div>
  );
}
