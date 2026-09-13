import { useEffect, useRef } from "react";

export function usePolling(callback: () => void, enabled: boolean, intervalMs = 2000): void {
  const saved = useRef(callback);
  saved.current = callback;

  useEffect(() => {
    if (!enabled) {
      return;
    }
    const id = window.setInterval(() => {
      saved.current();
    }, intervalMs);
    return () => window.clearInterval(id);
  }, [enabled, intervalMs]);
}
