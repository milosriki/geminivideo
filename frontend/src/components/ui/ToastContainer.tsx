import React from 'react';
import { AnimatePresence } from 'framer-motion';
import { useToastStore } from '../../stores/toastStore';
import { Toast } from './Toast';

/**
 * ToastContainer component that displays toast notifications
 *
 * Usage:
 * Add this component to your App.tsx:
 *
 * import { ToastContainer } from './components/ui';
 *
 * function App() {
 *   return (
 *     <>
 *       <YourAppContent />
 *       <ToastContainer />
 *     </>
 *   );
 * }
 */
export const ToastContainer: React.FC = () => {
  const { toasts, removeToast } = useToastStore();

  // Limit to 5 visible toasts
  const visibleToasts = toasts.slice(-5);

  return (
    <div
      className="fixed top-4 right-4 z-[9999] flex flex-col gap-3 pointer-events-none"
      aria-live="polite"
      aria-atomic="true"
    >
      <AnimatePresence mode="popLayout">
        {visibleToasts.map((toast) => (
          <div key={toast.id} className="pointer-events-auto">
            <Toast toast={toast} onClose={() => removeToast(toast.id)} />
          </div>
        ))}
      </AnimatePresence>
    </div>
  );
};
