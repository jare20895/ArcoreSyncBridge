import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import {
  AccountInfo,
  AuthenticationResult,
  EventType,
  PublicClientApplication,
} from '@azure/msal-browser';
import {
  AuthConfig,
  Principal,
  getAuthConfig,
  getCurrentUser,
  setAccessTokenProvider,
} from '@/services/api';

type AuthContextValue = {
  authConfig: AuthConfig | null;
  principal: Principal | null;
  loading: boolean;
  error: string | null;
  login: () => Promise<void>;
  logout: () => Promise<void>;
  requiresLogin: boolean;
  isAuthenticated: boolean;
};

const AuthContext = createContext<AuthContextValue | null>(null);

const authorityHost = process.env.NEXT_PUBLIC_AUTH_AUTHORITY_HOST || 'https://login.microsoftonline.com';
const tenantId = process.env.NEXT_PUBLIC_AUTH_TENANT_ID;
const clientId = process.env.NEXT_PUBLIC_AUTH_CLIENT_ID;
const apiScope = process.env.NEXT_PUBLIC_AUTH_SCOPE;

const buildRedirectUri = () => {
  if (typeof window === 'undefined') {
    return undefined;
  }
  return `${window.location.origin}/login`;
};

const hasAzureConfig = Boolean(tenantId && clientId && apiScope);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [authConfig, setAuthConfig] = useState<AuthConfig | null>(null);
  const [principal, setPrincipal] = useState<Principal | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const msalRef = useRef<PublicClientApplication | null>(null);

  const acquireAccessToken = useCallback(async (): Promise<string | null> => {
    if (!msalRef.current || !apiScope) {
      return null;
    }

    const account = msalRef.current.getActiveAccount() || msalRef.current.getAllAccounts()[0];
    if (!account) {
      return null;
    }

    const result = await msalRef.current.acquireTokenSilent({
      account,
      scopes: [apiScope],
    });
    return result.accessToken;
  }, []);

  const hydratePrincipal = useCallback(async () => {
    const currentUser = await getCurrentUser();
    setPrincipal(currentUser);
  }, []);

  useEffect(() => {
    let alive = true;

    const bootstrap = async () => {
      try {
        const config = await getAuthConfig();
        if (!alive) {
          return;
        }
        setAuthConfig(config);

        if (!config.interactive_login) {
          setAccessTokenProvider(null);
          try {
            const currentUser = await getCurrentUser();
            if (alive) {
              setPrincipal(currentUser);
            }
          } catch {
            if (alive) {
              setPrincipal(null);
            }
          }
          return;
        }

        if (!hasAzureConfig || !tenantId || !clientId || !apiScope) {
          setError('JWT auth is enabled, but the frontend Azure auth environment is incomplete.');
          setAccessTokenProvider(null);
          return;
        }

        const instance = new PublicClientApplication({
          auth: {
            clientId,
            authority: `${authorityHost}/${tenantId}`,
            redirectUri: buildRedirectUri(),
          },
          cache: {
            cacheLocation: 'sessionStorage',
          },
        });
        msalRef.current = instance;
        instance.addEventCallback((event) => {
          if (
            event.eventType === EventType.LOGIN_SUCCESS ||
            event.eventType === EventType.ACQUIRE_TOKEN_SUCCESS
          ) {
            const payload = event.payload as AuthenticationResult | null;
            if (payload?.account) {
              instance.setActiveAccount(payload.account);
            }
          }
        });

        await instance.initialize();
        const redirectResult = await instance.handleRedirectPromise();
        if (redirectResult?.account) {
          instance.setActiveAccount(redirectResult.account);
        }

        const knownAccount = instance.getActiveAccount() || instance.getAllAccounts()[0] || null;
        if (knownAccount) {
          instance.setActiveAccount(knownAccount);
          setAccessTokenProvider(acquireAccessToken);
          await hydratePrincipal();
        } else {
          setAccessTokenProvider(acquireAccessToken);
          setPrincipal(null);
        }
      } catch (authError: any) {
        if (alive) {
          setError(authError?.message || 'Failed to initialize authentication');
          setPrincipal(null);
          setAccessTokenProvider(null);
        }
      } finally {
        if (alive) {
          setLoading(false);
        }
      }
    };

    bootstrap();

    return () => {
      alive = false;
    };
  }, [acquireAccessToken, hydratePrincipal]);

  const login = useCallback(async () => {
    if (!msalRef.current || !apiScope) {
      return;
    }
    await msalRef.current.loginRedirect({
      scopes: [apiScope],
      redirectStartPage: typeof window !== 'undefined' ? window.location.href : undefined,
    });
  }, []);

  const logout = useCallback(async () => {
    setPrincipal(null);
    if (!msalRef.current) {
      return;
    }
    await msalRef.current.logoutRedirect({
      postLogoutRedirectUri: buildRedirectUri(),
    });
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      authConfig,
      principal,
      loading,
      error,
      login,
      logout,
      requiresLogin: Boolean(authConfig?.interactive_login),
      isAuthenticated: Boolean(principal),
    }),
    [authConfig, principal, loading, error, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
