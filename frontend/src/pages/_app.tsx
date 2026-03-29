import '@/styles/globals.css'
import 'reactflow/dist/style.css'
import type { AppProps } from 'next/app'
import { useRouter } from 'next/router'
import Layout from '@/components/Layout'
import { ToastProvider } from '@/components/ui/ToastProvider'
import { ConfirmDialogProvider } from '@/components/ui/ConfirmDialogProvider'
import { AuthGate } from '@/components/auth/AuthGate'
import { AuthProvider } from '@/components/auth/AuthProvider'

export default function App({ Component, pageProps }: AppProps) {
  const router = useRouter()
  const isLoginRoute = router.pathname === '/login'

  return (
    <AuthProvider>
      <ToastProvider>
        <ConfirmDialogProvider>
          <AuthGate>
            {isLoginRoute ? (
              <Component {...pageProps} />
            ) : (
              <Layout>
                <Component {...pageProps} />
              </Layout>
            )}
          </AuthGate>
        </ConfirmDialogProvider>
      </ToastProvider>
    </AuthProvider>
  )
}
