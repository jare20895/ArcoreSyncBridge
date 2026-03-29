import { useEffect } from 'react';
import { useRouter } from 'next/router';
import { ShieldCheck } from 'lucide-react';
import { useAuth } from '@/components/auth/AuthProvider';

export default function LoginPage() {
  const router = useRouter();
  const { principal, login, loading, requiresLogin, error } = useAuth();

  useEffect(() => {
    if (!loading && principal) {
      const next = typeof router.query.next === 'string' ? router.query.next : '/';
      router.replace(next);
    }
  }, [loading, principal, router]);

  if (!requiresLogin) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-light-bg dark:bg-dark-bg px-6">
        <div className="w-full max-w-md rounded-2xl border border-gray-200 bg-light-surface p-8 shadow-sm dark:border-gray-800 dark:bg-dark-surface">
          <h1 className="text-xl font-semibold text-light-text-primary dark:text-dark-text-primary">
            Interactive login is not enabled
          </h1>
          <p className="mt-3 text-sm text-light-text-secondary dark:text-dark-text-secondary">
            This environment is using backend-managed auth mode and does not require a browser sign-in flow.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-light-bg dark:bg-dark-bg px-6">
      <div className="w-full max-w-md rounded-2xl border border-gray-200 bg-light-surface p-8 shadow-sm dark:border-gray-800 dark:bg-dark-surface">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-light-primary/10 text-light-primary dark:bg-dark-primary/15 dark:text-dark-primary">
            <ShieldCheck size={22} />
          </div>
          <div>
            <h1 className="text-xl font-semibold text-light-text-primary dark:text-dark-text-primary">
              Sign in to Arcore SyncBridge
            </h1>
            <p className="mt-1 text-sm text-light-text-secondary dark:text-dark-text-secondary">
              Use your Microsoft identity to access the control plane.
            </p>
          </div>
        </div>

        {error && (
          <div className="mt-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900/60 dark:bg-red-950/40 dark:text-red-200">
            {error}
          </div>
        )}

        <button
          type="button"
          onClick={() => void login()}
          className="mt-6 inline-flex w-full items-center justify-center rounded-xl bg-light-primary px-4 py-3 text-sm font-semibold text-white transition hover:opacity-95 dark:bg-dark-primary"
        >
          Continue with Microsoft
        </button>
      </div>
    </div>
  );
}
