import { useEffect } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '@/components/auth/AuthProvider';

export function AuthGate({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { loading, principal, requiresLogin, error } = useAuth();

  useEffect(() => {
    if (!loading && requiresLogin && !principal && router.pathname !== '/login') {
      const next = encodeURIComponent(router.asPath || '/');
      router.replace(`/login?next=${next}`);
    }
  }, [loading, principal, requiresLogin, router]);

  if (router.pathname === '/login') {
    return <>{children}</>;
  }

  if (loading || (requiresLogin && !principal)) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-light-bg dark:bg-dark-bg px-6">
        <div className="w-full max-w-md rounded-2xl border border-gray-200 bg-light-surface p-8 text-center shadow-sm dark:border-gray-800 dark:bg-dark-surface">
          <h1 className="text-xl font-semibold text-light-text-primary dark:text-dark-text-primary">
            Loading authentication
          </h1>
          <p className="mt-3 text-sm text-light-text-secondary dark:text-dark-text-secondary">
            {error || 'Establishing your session and loading access context.'}
          </p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
