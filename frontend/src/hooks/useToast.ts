import { useCallback } from 'react';
import { useToastStore, ToastVariant } from '../stores/toastStore';

interface ToastOptions {
  title: string;
  message?: string;
  duration?: number;
}

interface ToastHelpers {
  success: (title: string, message?: string, duration?: number) => string;
  error: (title: string, message?: string, duration?: number) => string;
  warning: (title: string, message?: string, duration?: number) => string;
  info: (title: string, message?: string, duration?: number) => string;
  toast: (variant: ToastVariant, options: ToastOptions) => string;
  dismiss: (id: string) => void;
}

/**
 * Hook for triggering toast notifications
 *
 * @example
 * const toast = useToast();
 *
 * // Show success toast
 * toast.success('Success!', 'Your changes have been saved.');
 *
 * // Show error toast
 * toast.error('Error', 'Failed to save changes.');
 *
 * // Show warning toast
 * toast.warning('Warning', 'This action cannot be undone.');
 *
 * // Show info toast
 * toast.info('Info', 'New features are available.');
 *
 * // Show custom toast with options
 * const id = toast.toast('success', {
 *   title: 'Custom Toast',
 *   message: 'With custom duration',
 *   duration: 10000
 * });
 *
 * // Manually dismiss a toast
 * toast.dismiss(id);
 */
export const useToast = (): ToastHelpers => {
  const { addToast, removeToast } = useToastStore();

  const success = useCallback(
    (title: string, message?: string, duration?: number) => {
      return addToast({ variant: 'success', title, message, duration });
    },
    [addToast]
  );

  const error = useCallback(
    (title: string, message?: string, duration?: number) => {
      return addToast({ variant: 'error', title, message, duration });
    },
    [addToast]
  );

  const warning = useCallback(
    (title: string, message?: string, duration?: number) => {
      return addToast({ variant: 'warning', title, message, duration });
    },
    [addToast]
  );

  const info = useCallback(
    (title: string, message?: string, duration?: number) => {
      return addToast({ variant: 'info', title, message, duration });
    },
    [addToast]
  );

  const toast = useCallback(
    (variant: ToastVariant, options: ToastOptions) => {
      return addToast({ variant, ...options });
    },
    [addToast]
  );

  const dismiss = useCallback(
    (id: string) => {
      removeToast(id);
    },
    [removeToast]
  );

  return {
    success,
    error,
    warning,
    info,
    toast,
    dismiss,
  };
};
