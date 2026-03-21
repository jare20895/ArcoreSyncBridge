import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { Activity, ArrowRight, RefreshCw, ShieldCheck, Users } from 'lucide-react';

import { getAuditLog, getCurrentUser, getManagedUsers } from '../services/api';

type Principal = {
  user_id?: string | null;
  email: string;
  role: string;
  auth_mode: string;
};

type AuditEntry = {
  id: string;
  actor_email: string;
  actor_role: string;
  action: string;
  resource_type: string;
  resource_id?: string | null;
  request_id?: string | null;
  method?: string | null;
  path?: string | null;
  created_at: string;
  details?: Record<string, unknown> | null;
};

type ManagedUser = {
  id: string;
  email: string;
  display_name?: string | null;
  role: string;
  status: string;
  last_login_at?: string | null;
};

const QUICK_LINKS = [
  {
    title: 'Run History',
    description: 'Inspect execution-level outcomes and operational failures.',
    href: '/runs',
    icon: Activity,
  },
  {
    title: 'Sync Definitions',
    description: 'Review mappings, schedules, CDC state, and cursor operations.',
    href: '/sync-definitions',
    icon: ShieldCheck,
  },
];

export default function GovernancePage() {
  const [principal, setPrincipal] = useState<Principal | null>(null);
  const [auditEntries, setAuditEntries] = useState<AuditEntry[]>([]);
  const [users, setUsers] = useState<ManagedUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError(null);

    try {
      const currentUser = await getCurrentUser();
      setPrincipal(currentUser);

      if (currentUser.role === 'admin' || currentUser.role === 'platform_admin') {
        const [auditRows, managedUsers] = await Promise.all([
          getAuditLog({ limit: 20 }),
          getManagedUsers(),
        ]);
        setAuditEntries(auditRows);
        setUsers(managedUsers);
      } else {
        setAuditEntries([]);
        setUsers([]);
      }
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || 'Failed to load governance data.');
    } finally {
      setLoading(false);
    }
  };

  const formatDateTime = (value?: string | null) => {
    if (!value) return 'Never';
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(new Date(value));
  };

  const isAdmin = principal?.role === 'admin' || principal?.role === 'platform_admin';

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div className="max-w-3xl">
          <h1 className="text-3xl font-bold font-secondary text-light-text-primary dark:text-dark-text-primary">
            Governance
          </h1>
          <p className="mt-2 text-sm text-light-text-secondary dark:text-dark-text-secondary">
            Review access posture, recent administrative activity, and the audit trail behind protected actions.
          </p>
        </div>
        <button
          onClick={loadData}
          className="inline-flex items-center gap-2 self-start rounded-lg bg-light-primary px-4 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-opacity-90 dark:bg-dark-primary"
        >
          <RefreshCw size={16} />
          Refresh
        </button>
      </div>

      <div className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
        <section className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-800 dark:bg-dark-surface">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-light-text-primary dark:text-dark-text-primary">
                Access Context
              </h2>
              <p className="mt-1 text-sm text-light-text-secondary dark:text-dark-text-secondary">
                Current authenticated identity and the role resolved by the backend.
              </p>
            </div>
            <ShieldCheck size={18} className="text-light-primary dark:text-dark-primary" />
          </div>

          {loading ? (
            <div className="mt-6 text-sm text-light-text-secondary dark:text-dark-text-secondary">Loading access context...</div>
          ) : error ? (
            <div className="mt-6 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-900/40 dark:bg-red-950/30 dark:text-red-300">
              {error}
            </div>
          ) : principal ? (
            <div className="mt-6 grid gap-4 sm:grid-cols-3">
              <div className="rounded-lg bg-gray-50 p-4 dark:bg-gray-900">
                <div className="text-xs uppercase tracking-wide text-light-text-secondary dark:text-dark-text-secondary">User</div>
                <div className="mt-2 text-sm font-medium text-light-text-primary dark:text-dark-text-primary">{principal.email}</div>
              </div>
              <div className="rounded-lg bg-gray-50 p-4 dark:bg-gray-900">
                <div className="text-xs uppercase tracking-wide text-light-text-secondary dark:text-dark-text-secondary">Role</div>
                <div className="mt-2 text-sm font-medium text-light-text-primary dark:text-dark-text-primary">{principal.role}</div>
              </div>
              <div className="rounded-lg bg-gray-50 p-4 dark:bg-gray-900">
                <div className="text-xs uppercase tracking-wide text-light-text-secondary dark:text-dark-text-secondary">Auth Mode</div>
                <div className="mt-2 text-sm font-medium text-light-text-primary dark:text-dark-text-primary">{principal.auth_mode}</div>
              </div>
            </div>
          ) : null}
        </section>

        <section className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-800 dark:bg-dark-surface">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-light-text-primary dark:text-dark-text-primary">
                Governance Links
              </h2>
              <p className="mt-1 text-sm text-light-text-secondary dark:text-dark-text-secondary">
                Jump directly into the operational workflows tied to audited changes.
              </p>
            </div>
          </div>

          <div className="mt-4 space-y-3">
            {QUICK_LINKS.map((item) => (
              <Link
                key={item.title}
                href={item.href}
                className="flex items-start justify-between rounded-lg border border-gray-200 px-4 py-3 transition hover:border-light-primary/40 hover:bg-gray-50 dark:border-gray-800 dark:hover:bg-gray-900"
              >
                <div className="flex gap-3">
                  <div className="rounded-lg bg-light-primary/10 p-2 text-light-primary dark:bg-dark-primary/20 dark:text-dark-primary">
                    <item.icon size={16} />
                  </div>
                  <div>
                    <div className="text-sm font-semibold text-light-text-primary dark:text-dark-text-primary">{item.title}</div>
                    <div className="mt-1 text-sm text-light-text-secondary dark:text-dark-text-secondary">{item.description}</div>
                  </div>
                </div>
                <ArrowRight size={16} className="mt-1 text-light-text-secondary dark:text-dark-text-secondary" />
              </Link>
            ))}
          </div>
        </section>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.25fr_0.75fr]">
        <section className="rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-800 dark:bg-dark-surface">
          <div className="flex items-center justify-between border-b border-gray-200 px-5 py-4 dark:border-gray-800">
            <div>
              <h2 className="text-lg font-semibold text-light-text-primary dark:text-dark-text-primary">Recent Audit Activity</h2>
              <p className="mt-1 text-sm text-light-text-secondary dark:text-dark-text-secondary">
                Latest protected mutations and operational actions recorded by the backend.
              </p>
            </div>
          </div>

          {!isAdmin ? (
            <div className="p-5 text-sm text-light-text-secondary dark:text-dark-text-secondary">
              Audit log visibility is currently limited to `admin` and `platform_admin` roles.
            </div>
          ) : auditEntries.length === 0 ? (
            <div className="p-5 text-sm text-light-text-secondary dark:text-dark-text-secondary">No audit events recorded yet.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[760px]">
                <thead className="bg-gray-50 dark:bg-gray-900">
                  <tr>
                    <th className="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">When</th>
                    <th className="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">Actor</th>
                    <th className="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">Action</th>
                    <th className="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">Resource</th>
                    <th className="px-5 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">Request</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 dark:divide-gray-800">
                  {auditEntries.map((entry) => (
                    <tr key={entry.id} className="align-top">
                      <td className="px-5 py-4 text-sm text-light-text-primary dark:text-dark-text-primary">{formatDateTime(entry.created_at)}</td>
                      <td className="px-5 py-4">
                        <div className="text-sm font-medium text-light-text-primary dark:text-dark-text-primary">{entry.actor_email}</div>
                        <div className="mt-1 text-xs uppercase tracking-wide text-light-text-secondary dark:text-dark-text-secondary">{entry.actor_role}</div>
                      </td>
                      <td className="px-5 py-4 text-sm text-light-text-primary dark:text-dark-text-primary">{entry.action}</td>
                      <td className="px-5 py-4">
                        <div className="text-sm text-light-text-primary dark:text-dark-text-primary">{entry.resource_type}</div>
                        <div className="mt-1 font-mono text-xs text-light-text-secondary dark:text-dark-text-secondary">{entry.resource_id || 'n/a'}</div>
                      </td>
                      <td className="px-5 py-4">
                        <div className="text-xs uppercase tracking-wide text-light-text-secondary dark:text-dark-text-secondary">{entry.method || 'n/a'}</div>
                        <div className="mt-1 font-mono text-xs text-light-text-secondary dark:text-dark-text-secondary">{entry.request_id || 'n/a'}</div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <section className="rounded-xl border border-gray-200 bg-white shadow-sm dark:border-gray-800 dark:bg-dark-surface">
          <div className="flex items-center justify-between border-b border-gray-200 px-5 py-4 dark:border-gray-800">
            <div>
              <h2 className="text-lg font-semibold text-light-text-primary dark:text-dark-text-primary">Managed Access</h2>
              <p className="mt-1 text-sm text-light-text-secondary dark:text-dark-text-secondary">
                Persisted users and their effective roles.
              </p>
            </div>
            <Users size={18} className="text-light-primary dark:text-dark-primary" />
          </div>

          {!isAdmin ? (
            <div className="p-5 text-sm text-light-text-secondary dark:text-dark-text-secondary">
              User-management visibility is limited to administrative roles.
            </div>
          ) : users.length === 0 ? (
            <div className="p-5 text-sm text-light-text-secondary dark:text-dark-text-secondary">No managed users found.</div>
          ) : (
            <div className="divide-y divide-gray-200 dark:divide-gray-800">
              {users.map((user) => (
                <div key={user.id} className="px-5 py-4">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <div className="text-sm font-semibold text-light-text-primary dark:text-dark-text-primary">
                        {user.display_name || user.email}
                      </div>
                      <div className="mt-1 text-sm text-light-text-secondary dark:text-dark-text-secondary">{user.email}</div>
                    </div>
                    <div className="rounded-full bg-gray-100 px-3 py-1 text-xs font-medium uppercase tracking-wide text-gray-700 dark:bg-gray-900 dark:text-gray-300">
                      {user.role}
                    </div>
                  </div>
                  <div className="mt-3 flex items-center justify-between text-xs text-light-text-secondary dark:text-dark-text-secondary">
                    <span>Status: {user.status}</span>
                    <span>Last login: {formatDateTime(user.last_login_at)}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
