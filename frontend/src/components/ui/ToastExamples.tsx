import React from 'react';
import { useToast } from '../../hooks/useToast';

/**
 * ToastExamples - Demo component showing all toast variants and usage patterns
 *
 * This is a reference implementation showing how to use the toast system.
 * You can integrate these examples into your existing components.
 */
export const ToastExamples: React.FC = () => {
  const toast = useToast();

  const handleSuccessToast = () => {
    toast.success('Success!', 'Your changes have been saved successfully.');
  };

  const handleErrorToast = () => {
    toast.error('Error occurred', 'Failed to save changes. Please try again.');
  };

  const handleWarningToast = () => {
    toast.warning('Warning', 'This action cannot be undone.');
  };

  const handleInfoToast = () => {
    toast.info('New features available', 'Check out our latest updates.');
  };

  const handleCustomDuration = () => {
    toast.success('Quick notification', 'This will disappear in 2 seconds', 2000);
  };

  const handleLongDuration = () => {
    toast.info('Extended notification', 'This will stay for 10 seconds', 10000);
  };

  const handleMultipleToasts = () => {
    toast.success('First toast', 'This is the first notification');
    setTimeout(() => {
      toast.info('Second toast', 'This is the second notification');
    }, 500);
    setTimeout(() => {
      toast.warning('Third toast', 'This is the third notification');
    }, 1000);
  };

  const handleManualDismiss = () => {
    const id = toast.info(
      'Manual dismiss',
      'Click the button to dismiss this notification',
      999999
    );

    // Dismiss after 3 seconds
    setTimeout(() => {
      toast.dismiss(id);
    }, 3000);
  };

  return (
    <div className="p-8 space-y-4 bg-zinc-900 min-h-screen">
      <h1 className="text-3xl font-bold text-white mb-8">Toast Notification Examples</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Basic Variants */}
        <div className="space-y-2">
          <h2 className="text-xl font-semibold text-white mb-3">Basic Variants</h2>
          <button
            onClick={handleSuccessToast}
            className="w-full px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
          >
            Show Success Toast
          </button>

          <button
            onClick={handleErrorToast}
            className="w-full px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
          >
            Show Error Toast
          </button>

          <button
            onClick={handleWarningToast}
            className="w-full px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-lg transition-colors"
          >
            Show Warning Toast
          </button>

          <button
            onClick={handleInfoToast}
            className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
          >
            Show Info Toast
          </button>
        </div>

        {/* Custom Duration */}
        <div className="space-y-2">
          <h2 className="text-xl font-semibold text-white mb-3">Custom Duration</h2>
          <button
            onClick={handleCustomDuration}
            className="w-full px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors"
          >
            Quick Toast (2s)
          </button>

          <button
            onClick={handleLongDuration}
            className="w-full px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors"
          >
            Long Toast (10s)
          </button>
        </div>

        {/* Advanced Usage */}
        <div className="space-y-2">
          <h2 className="text-xl font-semibold text-white mb-3">Advanced Usage</h2>
          <button
            onClick={handleMultipleToasts}
            className="w-full px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
          >
            Multiple Toasts
          </button>

          <button
            onClick={handleManualDismiss}
            className="w-full px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
          >
            Manual Dismiss Demo
          </button>
        </div>
      </div>

      {/* Code Examples */}
      <div className="mt-8 space-y-4">
        <h2 className="text-2xl font-semibold text-white">Code Examples</h2>

        <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-white mb-2">Basic Usage</h3>
          <pre className="text-sm text-zinc-300 overflow-x-auto">
{`import { useToast } from './hooks/useToast';

function MyComponent() {
  const toast = useToast();

  const handleClick = () => {
    toast.success('Success!', 'Operation completed');
  };

  return <button onClick={handleClick}>Click me</button>;
}`}
          </pre>
        </div>

        <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-white mb-2">All Variants</h3>
          <pre className="text-sm text-zinc-300 overflow-x-auto">
{`// Success
toast.success('Title', 'Message');

// Error
toast.error('Title', 'Message');

// Warning
toast.warning('Title', 'Message');

// Info
toast.info('Title', 'Message');

// Custom duration (in milliseconds)
toast.success('Title', 'Message', 3000);`}
          </pre>
        </div>

        <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-white mb-2">Manual Dismiss</h3>
          <pre className="text-sm text-zinc-300 overflow-x-auto">
{`const id = toast.info('Title', 'Message', 999999);

// Later, dismiss manually
toast.dismiss(id);`}
          </pre>
        </div>

        <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-white mb-2">Error Handling Example</h3>
          <pre className="text-sm text-zinc-300 overflow-x-auto">
{`async function saveData() {
  try {
    await api.save(data);
    toast.success('Saved!', 'Your changes have been saved.');
  } catch (error) {
    toast.error('Save failed', error.message);
  }
}`}
          </pre>
        </div>
      </div>
    </div>
  );
};
