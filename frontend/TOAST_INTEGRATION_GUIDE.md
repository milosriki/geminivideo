# Toast Notification System - Integration Guide

## Overview

A complete, production-ready toast notification system for GeminiVideo with:
- 4 variants: success, error, warning, info
- Auto-dismiss with animated progress bar
- Smooth slide-in/out animations (framer-motion)
- Dark theme matching the app
- Maximum 5 visible toasts
- Manual dismiss option
- TypeScript support

## Files Created

### Components
- `/frontend/src/components/ui/Toast.tsx` - Individual toast component
- `/frontend/src/components/ui/ToastContainer.tsx` - Toast container/manager
- `/frontend/src/components/ui/ToastExamples.tsx` - Demo/example component
- `/frontend/src/components/ui/index.ts` - UI exports

### Store
- `/frontend/src/stores/toastStore.ts` - Zustand store for toast state management

### Hook
- `/frontend/src/hooks/useToast.ts` - Convenient hook for triggering toasts
- `/frontend/src/hooks/index.ts` - Hook exports

## Integration Steps

### Step 1: Add ToastContainer to App.tsx

Add the ToastContainer to your App.tsx file. This should be added ONCE at the root level:

```tsx
import { ToastContainer } from './components/ui';

function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<PageLoader />}>
        <Routes>
          {/* Your routes */}
        </Routes>
      </Suspense>

      {/* Add ToastContainer here - it will be available globally */}
      <ToastContainer />
    </BrowserRouter>
  );
}
```

### Step 2: Use the Toast Hook

In any component where you want to trigger toasts:

```tsx
import { useToast } from '../hooks/useToast';

function MyComponent() {
  const toast = useToast();

  const handleSave = async () => {
    try {
      await saveData();
      toast.success('Saved!', 'Your changes have been saved successfully.');
    } catch (error) {
      toast.error('Save failed', error.message);
    }
  };

  return (
    <button onClick={handleSave}>Save</button>
  );
}
```

## Usage Examples

### Basic Usage

```tsx
import { useToast } from '../hooks/useToast';

function Component() {
  const toast = useToast();

  // Success
  toast.success('Success!', 'Operation completed successfully');

  // Error
  toast.error('Error', 'Something went wrong');

  // Warning
  toast.warning('Warning', 'Please review before proceeding');

  // Info
  toast.info('Info', 'New features are available');
}
```

### Custom Duration

```tsx
// Short duration (2 seconds)
toast.success('Quick notification', 'This will disappear quickly', 2000);

// Long duration (10 seconds)
toast.info('Important info', 'Read this carefully', 10000);

// Default is 5000ms (5 seconds)
```

### Manual Dismiss

```tsx
// Get the toast ID
const toastId = toast.info('Loading...', 'Please wait', 999999);

// Later, dismiss manually
toast.dismiss(toastId);
```

### Real-world Examples

#### Form Submission
```tsx
const handleSubmit = async (formData) => {
  try {
    await api.submitForm(formData);
    toast.success('Form submitted', 'We\'ll get back to you soon!');
    navigate('/success');
  } catch (error) {
    toast.error('Submission failed', error.message);
  }
};
```

#### File Upload
```tsx
const handleUpload = async (file) => {
  const uploadId = toast.info('Uploading...', 'Please wait', 999999);

  try {
    await uploadFile(file);
    toast.dismiss(uploadId);
    toast.success('Upload complete', 'Your file has been uploaded');
  } catch (error) {
    toast.dismiss(uploadId);
    toast.error('Upload failed', 'Please try again');
  }
};
```

#### Async Operations with Progress
```tsx
const handleProcess = async () => {
  const processId = toast.info('Processing...', 'This may take a moment', 999999);

  try {
    const result = await longRunningOperation();
    toast.dismiss(processId);

    if (result.warnings.length > 0) {
      toast.warning('Completed with warnings', `${result.warnings.length} issues found`);
    } else {
      toast.success('Processing complete', 'All items processed successfully');
    }
  } catch (error) {
    toast.dismiss(processId);
    toast.error('Processing failed', error.message);
  }
};
```

#### Multiple Sequential Toasts
```tsx
const handleBulkOperation = async (items) => {
  for (const item of items) {
    try {
      await processItem(item);
      toast.success(`${item.name} processed`, 'Moving to next item');
    } catch (error) {
      toast.error(`Failed: ${item.name}`, error.message);
    }
  }
  toast.info('All done!', 'Bulk operation completed');
};
```

## Styling

The toast system uses a dark theme that matches the GeminiVideo app:

- **Background**: `bg-zinc-800`
- **Border**: `border-zinc-700`
- **Success**: `green-500` accent
- **Error**: `red-500` accent
- **Warning**: `amber-500` accent
- **Info**: `blue-500` accent

All colors and styles can be customized in `/frontend/src/components/ui/Toast.tsx`.

## Animations

The toast system includes:
- Slide-in from right (entrance)
- Fade out with slide right (exit)
- Smooth progress bar animation
- Stack animation when multiple toasts appear

Powered by `framer-motion` for smooth, performant animations.

## Limitations

- Maximum 5 visible toasts at once (oldest are hidden)
- z-index is set to 9999 to appear above all content
- Fixed position: top-right corner

## API Reference

### useToast Hook

```tsx
const toast = useToast();

// Methods
toast.success(title: string, message?: string, duration?: number): string
toast.error(title: string, message?: string, duration?: number): string
toast.warning(title: string, message?: string, duration?: number): string
toast.info(title: string, message?: string, duration?: number): string
toast.dismiss(id: string): void
```

### Toast Store (Direct Access)

If you need direct access to the store:

```tsx
import { useToastStore } from '../stores/toastStore';

const { toasts, addToast, removeToast } = useToastStore();
```

## Testing

To test the toast system, you can:

1. Use the ToastExamples component:
   ```tsx
   import { ToastExamples } from './components/ui';

   // Add to a route or render directly
   <ToastExamples />
   ```

2. Or test directly in any component:
   ```tsx
   const toast = useToast();
   toast.success('Test', 'This is a test notification');
   ```

## Troubleshooting

### Toasts not appearing
- Ensure `<ToastContainer />` is added to App.tsx
- Check that it's not hidden behind other elements (z-index issue)
- Verify framer-motion is installed

### TypeScript errors
- All types are exported from the store
- Use the hook for the best TypeScript experience
- Import types: `import type { Toast, ToastVariant } from '../stores/toastStore'`

### Animation issues
- Ensure framer-motion is installed: `npm install framer-motion`
- Check for conflicting CSS animations

## Advanced Customization

### Custom Toast Variants

To add a new variant, edit `/frontend/src/components/ui/Toast.tsx`:

```tsx
const variantConfig = {
  // ... existing variants
  custom: {
    icon: YourIcon,
    accentColor: 'rgb(255, 0, 255)',
    borderColor: 'border-purple-500/20',
    iconBg: 'bg-purple-500/10',
  },
};
```

### Custom Position

To change the position, edit `/frontend/src/components/ui/ToastContainer.tsx`:

```tsx
// Current: top-right
<div className="fixed top-4 right-4 z-[9999] ...">

// Example: bottom-right
<div className="fixed bottom-4 right-4 z-[9999] ...">

// Example: top-center
<div className="fixed top-4 left-1/2 -translate-x-1/2 z-[9999] ...">
```

### Custom Duration

Change default duration in `/frontend/src/stores/toastStore.ts`:

```tsx
const duration = toast.duration || 5000; // Change 5000 to your preferred default
```

## Production Checklist

- [x] TypeScript support
- [x] Error handling
- [x] Animations optimized
- [x] Accessibility (aria-live)
- [x] Mobile responsive
- [x] Dark theme
- [x] Auto-cleanup
- [x] Memory efficient
- [x] No external dependencies (except existing ones)
- [x] Full documentation

## Support

For issues or questions about the toast system, refer to:
- This integration guide
- `/frontend/src/components/ui/ToastExamples.tsx` for live examples
- `/frontend/src/hooks/useToast.ts` for API details
