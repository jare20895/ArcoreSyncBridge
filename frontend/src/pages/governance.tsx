import React, { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { Activity, ArrowRight, RefreshCw, ShieldCheck, Users } from 'lucide-react';

import { getAuditLog, getCurrentUser, getManagedUsers, updateManagedUser } from '../services/api';

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

type ListMeta = {
  total?: number;
  limit?: number;
  offset?: number;
};

const ROLE_OPTIONS = ['viewer', 'operator', 'editor', 'admin', 'platform_admin'];
const STATUS_OPTIONS = ['ACTIVE', 'DISABLED'];

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
  const [auditMeta, setAuditMeta] = useState<ListMeta>({});
  const [auditFilters, setAuditFilters] = useState({ action: '', actorEmail: '' });
  const [auditPage, setAuditPage] = useState(0);
  const [users, setUsers] = useState<ManagedUser[]>([]);
  const [userMeta, setUserMeta] = useState<ListMeta>({});
  const [userFilters, setUserFilters] = useState({ email: '', role: '', status: '' });
  const [userPage, setUserPage] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saveState, setSaveState] = useState<Record<string, { role: string; status: string }>>({});
  const [savingUserId, setSavingUserId] = useState<string | null>(null);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

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
        const [auditResponse, managedUsersResponse] = await Promise.all([
          getAuditLog({ limit: 20, offset: 0 }),
          getManagedUsers({ limit: 20, offset: 0 }),
        ]);
        setAuditEntries(auditResponse.data);
        setAuditMeta(auditResponse.meta ?? {});
        setUsers(managedUsersResponse.data);
        setUserMeta(managedUsersResponse.meta ?? {});
        setSaveState(
          Object.fromEntries(
            managedUsersResponse.data.map((user: ManagedUser) => [
              user.id,
              { role: user.role, status: user.status },
            ])
          )
        );
      } else {
        setAuditEntries([]);
        setAuditMeta({});
        setUsers([]);
        setUserMeta({});
        setSaveState({});
      }
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || 'Failed to load governance data.');
    } finally {
      setLoading(false);
    }
  };

  const loadAuditEntries = useCallback(async (page = auditPage, filters = auditFilters) => {
    const response = await getAuditLog({
      limit: 20,
      offset: page * 20,
      action: filters.action || undefined,
      actor_email: filters.actorEmail || undefined,
    });
    setAuditEntries(response.data);
    setAuditMeta(response.meta ?? {});
  }, [auditFilters, auditPage]);

  const loadManagedUsers = useCallback(async (page = userPage, filters = userFilters) => {
    const response = await getManagedUsers({
      limit: 20,
      offset: page * 20,
      email: filters.email || undefined,
      role: filters.role || undefined,
      status: filters.status || undefined,
    });
    setUsers(response.data);
    setUserMeta(response.meta ?? {});
    setSaveState((current) => ({
      ...current,
      ...Object.fromEntries(
        response.data.map((user: ManagedUser) => [user.id, { role: user.role, status: user.status }])
      ),
    }));
  }, [userFilters, userPage]);

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

  useEffect(() => {
    if (!isAdmin || loading) {
      return;
    }
    void loadAuditEntries();
  }, [auditPage, auditFilters, isAdmin, loadAuditEntries, loading]);

  useEffect(() => {
    if (!isAdmin || loading) {
      return;
    }
    void loadManagedUsers();
  }, [userPage, userFilters, isAdmin, loadManagedUsers, loading]);

  const updateDraft = (userId: string, patch: Partial<{ role: string; status: string }>) => {
    setSaveState((current) => ({
      ...current,
      [userId]: {
        role: patch.role ?? current[userId]?.role ?? 'viewer',
        status: patch.status ?? current[userId]?.status ?? 'ACTIVE',
      },
    }));
  };

  const saveUserAccess = async (user: ManagedUser) => {
    const draft = saveState[user.id];
    if (!draft) return;
    if (draft.role === user.role && draft.status === user.status) return;

    setSavingUserId(user.id);
    setSaveMessage(null);

    try {
      await updateManagedUser(user.id, {
        role: draft.role,
        status: draft.status,
      });
      setUsers((current) =>
        current.map((item) =>
          item.id === user.id ? { ...item, role: draft.role, status: draft.status } : item
        )
      );
      setSaveMessage(`Updated access for ${user.email}.`);
      await Promise.all([loadAuditEntries(0, auditFilters), loadManagedUsers(userPage, userFilters)]);
      setAuditPage(0);
    } catch (err: any) {
      setSaveMessage(err?.response?.data?.error?.message || `Failed to update ${user.email}.`);
    } finally {
      setSavingUserId(null);
    }
  };

  const auditHasPrevious = auditPage > 0;
  const auditHasNext = (auditMeta.offset ?? 0) + auditEntries.length < (auditMeta.total ?? 0);
  const userHasPrevious = userPage > 0;
  const userHasNext = (userMeta.offset ?? 0) + users.length < (userMeta.total ?? 0);

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
            <>
              <div className="grid gap-3 border-b border-gray-200 px-5 py-4 dark:border-gray-800 md:grid-cols-2">
                <input
                  value={auditFilters.actorEmail}
                  onChange={(event) => {
                    setAuditPage(0);
                    setAuditFilters((current) => ({ ...current, actorEmail: event.target.value }));
                  }}
                  placeholder="Filter by actor email"
                  className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-light-text-primary dark:border-gray-700 dark:bg-gray-900 dark:text-dark-text-primary"
                />
                <input
                  value={auditFilters.action}
                  onChange={(event) => {
                    setAuditPage(0);
                    setAuditFilters((current) => ({ ...current, action: event.target.value }));
                  }}
                  placeholder="Filter by action"
                  className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-light-text-primary dark:border-gray-700 dark:bg-gray-900 dark:text-dark-text-primary"
                />
              </div>
              <div className="p-5 text-sm text-light-text-secondary dark:text-dark-text-secondary">No audit events recorded yet.</div>
            </>
          ) : (
            <>
              <div className="grid gap-3 border-b border-gray-200 px-5 py-4 dark:border-gray-800 md:grid-cols-2">
                <input
                  value={auditFilters.actorEmail}
                  onChange={(event) => {
                    setAuditPage(0);
                    setAuditFilters((current) => ({ ...current, actorEmail: event.target.value }));
                  }}
                  placeholder="Filter by actor email"
                  className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-light-text-primary dark:border-gray-700 dark:bg-gray-900 dark:text-dark-text-primary"
                />
                <input
                  value={auditFilters.action}
                  onChange={(event) => {
                    setAuditPage(0);
                    setAuditFilters((current) => ({ ...current, action: event.target.value }));
                  }}
                  placeholder="Filter by action"
                  className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-light-text-primary dark:border-gray-700 dark:bg-gray-900 dark:text-dark-text-primary"
                />
              </div>
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
              <div className="flex items-center justify-between border-t border-gray-200 px-5 py-4 text-sm dark:border-gray-800">
                <div className="text-light-text-secondary dark:text-dark-text-secondary">
                  Showing {(auditMeta.offset ?? 0) + (auditEntries.length > 0 ? 1 : 0)}-
                  {(auditMeta.offset ?? 0) + auditEntries.length} of {auditMeta.total ?? auditEntries.length}
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => setAuditPage((current) => Math.max(0, current - 1))}
                    disabled={!auditHasPrevious}
                    className="rounded-lg border border-gray-300 px-3 py-2 text-sm text-light-text-primary transition hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-700 dark:text-dark-text-primary dark:hover:bg-gray-900"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => setAuditPage((current) => current + 1)}
                    disabled={!auditHasNext}
                    className="rounded-lg border border-gray-300 px-3 py-2 text-sm text-light-text-primary transition hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-700 dark:text-dark-text-primary dark:hover:bg-gray-900"
                  >
                    Next
                  </button>
                </div>
              </div>
            </>
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
            <>
              <div className="grid gap-3 border-b border-gray-200 px-5 py-4 dark:border-gray-800">
                <input
                  value={userFilters.email}
                  onChange={(event) => {
                    setUserPage(0);
                    setUserFilters((current) => ({ ...current, email: event.target.value }));
                  }}
                  placeholder="Filter by email"
                  className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-light-text-primary dark:border-gray-700 dark:bg-gray-900 dark:text-dark-text-primary"
                />
                <div className="grid gap-3 sm:grid-cols-2">
                  <select
                    value={userFilters.role}
                    onChange={(event) => {
                      setUserPage(0);
                      setUserFilters((current) => ({ ...current, role: event.target.value }));
                    }}
                    className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-light-text-primary dark:border-gray-700 dark:bg-gray-900 dark:text-dark-text-primary"
                  >
                    <option value="">All roles</option>
                    {ROLE_OPTIONS.map((role) => (
                      <option key={role} value={role}>
                        {role}
                      </option>
                    ))}
                  </select>
                  <select
                    value={userFilters.status}
                    onChange={(event) => {
                      setUserPage(0);
                      setUserFilters((current) => ({ ...current, status: event.target.value }));
                    }}
                    className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-light-text-primary dark:border-gray-700 dark:bg-gray-900 dark:text-dark-text-primary"
                  >
                    <option value="">All statuses</option>
                    {STATUS_OPTIONS.map((status) => (
                      <option key={status} value={status}>
                        {status}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="p-5 text-sm text-light-text-secondary dark:text-dark-text-secondary">No managed users found.</div>
            </>
          ) : (
            <div className="divide-y divide-gray-200 dark:divide-gray-800">
              <div className="grid gap-3 px-5 py-4">
                <input
                  value={userFilters.email}
                  onChange={(event) => {
                    setUserPage(0);
                    setUserFilters((current) => ({ ...current, email: event.target.value }));
                  }}
                  placeholder="Filter by email"
                  className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-light-text-primary dark:border-gray-700 dark:bg-gray-900 dark:text-dark-text-primary"
                />
                <div className="grid gap-3 sm:grid-cols-2">
                  <select
                    value={userFilters.role}
                    onChange={(event) => {
                      setUserPage(0);
                      setUserFilters((current) => ({ ...current, role: event.target.value }));
                    }}
                    className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-light-text-primary dark:border-gray-700 dark:bg-gray-900 dark:text-dark-text-primary"
                  >
                    <option value="">All roles</option>
                    {ROLE_OPTIONS.map((role) => (
                      <option key={role} value={role}>
                        {role}
                      </option>
                    ))}
                  </select>
                  <select
                    value={userFilters.status}
                    onChange={(event) => {
                      setUserPage(0);
                      setUserFilters((current) => ({ ...current, status: event.target.value }));
                    }}
                    className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-light-text-primary dark:border-gray-700 dark:bg-gray-900 dark:text-dark-text-primary"
                  >
                    <option value="">All statuses</option>
                    {STATUS_OPTIONS.map((status) => (
                      <option key={status} value={status}>
                        {status}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              {saveMessage ? (
                <div className="border-b border-gray-200 bg-gray-50 px-5 py-3 text-sm text-light-text-secondary dark:border-gray-800 dark:bg-gray-900 dark:text-dark-text-secondary">
                  {saveMessage}
                </div>
              ) : null}
              {users.map((user) => (
                <div key={user.id} className="px-5 py-4">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <div className="text-sm font-semibold text-light-text-primary dark:text-dark-text-primary">
                        {user.display_name || user.email}
                      </div>
                      <div className="mt-1 text-sm text-light-text-secondary dark:text-dark-text-secondary">{user.email}</div>
                    </div>
                    <div className="min-w-[188px] space-y-2">
                      <label className="block text-xs uppercase tracking-wide text-light-text-secondary dark:text-dark-text-secondary">
                        Role
                      </label>
                      <select
                        value={saveState[user.id]?.role || user.role}
                        onChange={(event) => updateDraft(user.id, { role: event.target.value })}
                        className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-light-text-primary dark:border-gray-700 dark:bg-gray-900 dark:text-dark-text-primary"
                      >
                        {ROLE_OPTIONS.map((role) => (
                          <option key={role} value={role}>
                            {role}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                  <div className="mt-4 flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
                    <div className="grid gap-3 sm:grid-cols-[180px_auto] sm:items-end">
                      <div>
                        <label className="block text-xs uppercase tracking-wide text-light-text-secondary dark:text-dark-text-secondary">
                          Status
                        </label>
                        <select
                          value={saveState[user.id]?.status || user.status}
                          onChange={(event) => updateDraft(user.id, { status: event.target.value })}
                          className="mt-2 w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-light-text-primary dark:border-gray-700 dark:bg-gray-900 dark:text-dark-text-primary"
                        >
                          {STATUS_OPTIONS.map((status) => (
                            <option key={status} value={status}>
                              {status}
                            </option>
                          ))}
                        </select>
                      </div>
                      <div className="text-xs text-light-text-secondary dark:text-dark-text-secondary">
                        Last login: {formatDateTime(user.last_login_at)}
                      </div>
                    </div>
                    <button
                      onClick={() => saveUserAccess(user)}
                      disabled={
                        savingUserId === user.id ||
                        (
                          (saveState[user.id]?.role || user.role) === user.role &&
                          (saveState[user.id]?.status || user.status) === user.status
                        )
                      }
                      className="inline-flex items-center justify-center rounded-lg bg-light-primary px-4 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-opacity-90 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-dark-primary"
                    >
                      {savingUserId === user.id ? 'Saving...' : 'Save Access'}
                    </button>
                  </div>
                </div>
              ))}
              <div className="flex items-center justify-between px-5 py-4 text-sm">
                <div className="text-light-text-secondary dark:text-dark-text-secondary">
                  Showing {(userMeta.offset ?? 0) + (users.length > 0 ? 1 : 0)}-{(userMeta.offset ?? 0) + users.length} of{' '}
                  {userMeta.total ?? users.length}
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => setUserPage((current) => Math.max(0, current - 1))}
                    disabled={!userHasPrevious}
                    className="rounded-lg border border-gray-300 px-3 py-2 text-sm text-light-text-primary transition hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-700 dark:text-dark-text-primary dark:hover:bg-gray-900"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => setUserPage((current) => current + 1)}
                    disabled={!userHasNext}
                    className="rounded-lg border border-gray-300 px-3 py-2 text-sm text-light-text-primary transition hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-700 dark:text-dark-text-primary dark:hover:bg-gray-900"
                  >
                    Next
                  </button>
                </div>
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
