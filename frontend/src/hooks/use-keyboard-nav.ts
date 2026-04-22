import { useEffect } from 'react';

interface UseKeyboardNavOptions {
  onPrev: () => void;
  onNext: () => void;
  enabled?: boolean;
}

export function useKeyboardNav({ onPrev, onNext, enabled = true }: UseKeyboardNavOptions): void {
  useEffect(() => {
    if (!enabled) return;

    function handleKeyDown(event: KeyboardEvent): void {
      const target = event.target as HTMLElement;
      if (
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.isContentEditable
      ) {
        return;
      }

      if (event.key === 'ArrowUp') {
        event.preventDefault();
        onPrev();
      } else if (event.key === 'ArrowDown') {
        event.preventDefault();
        onNext();
      }
    }

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [onPrev, onNext, enabled]);
}
