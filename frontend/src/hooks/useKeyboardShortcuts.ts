/**
 * Keyboard Shortcuts Hook
 *
 * Manages keyboard shortcuts for demo mode and presentation navigation.
 */

import { useEffect, useCallback, useRef } from 'react';

export interface KeyboardShortcut {
  key: string;
  ctrlKey?: boolean;
  shiftKey?: boolean;
  altKey?: boolean;
  description: string;
  handler: () => void;
}

export interface UseKeyboardShortcutsOptions {
  enabled?: boolean;
  shortcuts: KeyboardShortcut[];
}

export function useKeyboardShortcuts(options: UseKeyboardShortcutsOptions) {
  const { enabled = true, shortcuts } = options;
  const shortcutsRef = useRef(shortcuts);

  // Update shortcuts ref when they change
  useEffect(() => {
    shortcutsRef.current = shortcuts;
  }, [shortcuts]);

  useEffect(() => {
    if (!enabled) return;

    const handleKeyPress = (e: KeyboardEvent) => {
      // Ignore if user is typing in an input field
      const target = e.target as HTMLElement;
      if (
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.isContentEditable
      ) {
        return;
      }

      // Find matching shortcut
      const shortcut = shortcutsRef.current.find(s => {
        const keyMatch = s.key.toLowerCase() === e.key.toLowerCase();
        const ctrlMatch = s.ctrlKey === undefined || s.ctrlKey === (e.ctrlKey || e.metaKey);
        const shiftMatch = s.shiftKey === undefined || s.shiftKey === e.shiftKey;
        const altMatch = s.altKey === undefined || s.altKey === e.altKey;

        return keyMatch && ctrlMatch && shiftMatch && altMatch;
      });

      if (shortcut) {
        e.preventDefault();
        shortcut.handler();
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [enabled]);

  return {
    shortcuts: shortcutsRef.current
  };
}

/**
 * Demo mode keyboard shortcuts
 */
export function useDemoKeyboardShortcuts(handlers: {
  toggleDemo?: () => void;
  nextSlide?: () => void;
  prevSlide?: () => void;
  toggleFullscreen?: () => void;
  exit?: () => void;
}) {
  const shortcuts: KeyboardShortcut[] = [];

  if (handlers.toggleDemo) {
    shortcuts.push({
      key: 'd',
      description: 'Toggle demo mode',
      handler: handlers.toggleDemo
    });
  }

  if (handlers.nextSlide) {
    shortcuts.push(
      {
        key: 'ArrowRight',
        description: 'Next slide',
        handler: handlers.nextSlide
      },
      {
        key: ' ',
        description: 'Next slide',
        handler: handlers.nextSlide
      }
    );
  }

  if (handlers.prevSlide) {
    shortcuts.push({
      key: 'ArrowLeft',
      description: 'Previous slide',
      handler: handlers.prevSlide
    });
  }

  if (handlers.toggleFullscreen) {
    shortcuts.push({
      key: 'f',
      description: 'Toggle fullscreen',
      handler: handlers.toggleFullscreen
    });
  }

  if (handlers.exit) {
    shortcuts.push({
      key: 'Escape',
      description: 'Exit presentation',
      handler: handlers.exit
    });
  }

  return useKeyboardShortcuts({ shortcuts });
}

/**
 * Keyboard shortcuts help panel component
 */
export function KeyboardShortcutsHelp({ shortcuts }: { shortcuts: KeyboardShortcut[] }) {
  if (shortcuts.length === 0) return null;

  return (
    <div className="p-4 rounded-lg bg-zinc-800/50 border border-zinc-700/50 backdrop-blur-sm">
      <div className="text-sm font-medium mb-3">Keyboard Shortcuts</div>
      <div className="space-y-2">
        {shortcuts.map((shortcut, idx) => (
          <div key={idx} className="flex items-center justify-between text-xs">
            <span className="text-zinc-400">{shortcut.description}</span>
            <kbd className="px-2 py-1 rounded bg-zinc-700 text-zinc-300 font-mono">
              {formatShortcutKey(shortcut)}
            </kbd>
          </div>
        ))}
      </div>
    </div>
  );
}

function formatShortcutKey(shortcut: KeyboardShortcut): string {
  const parts: string[] = [];

  if (shortcut.ctrlKey) parts.push('Ctrl');
  if (shortcut.shiftKey) parts.push('Shift');
  if (shortcut.altKey) parts.push('Alt');

  // Format the main key
  let key = shortcut.key;
  if (key === ' ') key = 'Space';
  else if (key === 'ArrowLeft') key = '←';
  else if (key === 'ArrowRight') key = '→';
  else if (key === 'ArrowUp') key = '↑';
  else if (key === 'ArrowDown') key = '↓';

  parts.push(key);

  return parts.join('+');
}
