import React, { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from 'react';
import { AlertTriangle } from 'lucide-react';

interface ConfirmOptions {
  title: string;
  description: string;
  confirmLabel?: string;
  cancelLabel?: string;
  tone?: 'default' | 'danger';
}

interface ConfirmState extends ConfirmOptions {
  isOpen: boolean;
  resolve: (value: boolean) => void;
}

interface ConfirmDialogContextValue {
  confirm: (options: ConfirmOptions) => Promise<boolean>;
}

const ConfirmDialogContext = createContext<ConfirmDialogContextValue | null>(null);

export function ConfirmDialogProvider({ children }: { children: ReactNode }) {
  const [dialog, setDialog] = useState<ConfirmState | null>(null);

  const closeDialog = useCallback((result: boolean) => {
    setDialog((current) => {
      if (!current) {
        return current;
      }

      current.resolve(result);
      return null;
    });
  }, []);

  const confirm = useCallback((options: ConfirmOptions) => {
    return new Promise<boolean>((resolve) => {
      setDialog({
        ...options,
        isOpen: true,
        resolve,
      });
    });
  }, []);

  const value = useMemo(() => ({ confirm }), [confirm]);

  return (
    <ConfirmDialogContext.Provider value={value}>
      {children}
      {dialog?.isOpen ? (
        <div
          className="fixed inset-0 z-[110] flex items-center justify-center bg-black/60 px-4"
          role="presentation"
          onClick={() => closeDialog(false)}
        >
          <div
            role="alertdialog"
            aria-modal="true"
            aria-labelledby="confirm-dialog-title"
            aria-describedby="confirm-dialog-description"
            className="w-full max-w-md rounded-2xl border border-gray-200 bg-white p-6 shadow-2xl dark:border-gray-800 dark:bg-dark-surface"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="flex items-start gap-3">
              <div
                className={`mt-0.5 rounded-full p-2 ${
                  dialog.tone === 'danger'
                    ? 'bg-red-100 text-red-700 dark:bg-red-950/60 dark:text-red-300'
                    : 'bg-amber-100 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300'
                }`}
              >
                <AlertTriangle className="h-5 w-5" aria-hidden="true" />
              </div>
              <div className="flex-1">
                <h2
                  id="confirm-dialog-title"
                  className="text-lg font-semibold text-light-text-primary dark:text-dark-text-primary"
                >
                  {dialog.title}
                </h2>
                <p
                  id="confirm-dialog-description"
                  className="mt-2 text-sm text-light-text-secondary dark:text-dark-text-secondary"
                >
                  {dialog.description}
                </p>
              </div>
            </div>
            <div className="mt-6 flex justify-end gap-3">
              <button
                type="button"
                onClick={() => closeDialog(false)}
                className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 transition hover:bg-gray-50 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800"
              >
                {dialog.cancelLabel || 'Cancel'}
              </button>
              <button
                type="button"
                onClick={() => closeDialog(true)}
                className={`rounded-lg px-4 py-2 text-sm font-medium text-white transition hover:opacity-90 ${
                  dialog.tone === 'danger'
                    ? 'bg-red-600 dark:bg-red-500'
                    : 'bg-light-primary dark:bg-dark-primary'
                }`}
              >
                {dialog.confirmLabel || 'Confirm'}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </ConfirmDialogContext.Provider>
  );
}

export function useConfirmDialog() {
  const context = useContext(ConfirmDialogContext);

  if (!context) {
    throw new Error('useConfirmDialog must be used within a ConfirmDialogProvider');
  }

  return context;
}
