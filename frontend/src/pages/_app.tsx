import '@/styles/globals.css'
import 'reactflow/dist/style.css'
import type { AppProps } from 'next/app'
import Layout from '@/components/Layout'
import { ToastProvider } from '@/components/ui/ToastProvider'
import { ConfirmDialogProvider } from '@/components/ui/ConfirmDialogProvider'

export default function App({ Component, pageProps }: AppProps) {
  return (
    <ToastProvider>
      <ConfirmDialogProvider>
        <Layout>
          <Component {...pageProps} />
        </Layout>
      </ConfirmDialogProvider>
    </ToastProvider>
  )
}
