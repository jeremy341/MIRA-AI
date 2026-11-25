/** Toast queue rules, pure. The reactive store is in stores/toasts.svelte.ts. */

export type ToastKind = 'success' | 'error' | 'info' | 'warning';

export interface Toast {
  id: number;
  kind: ToastKind;
  message: string;
}

/** Three at most, so a burst of messages never covers much of the page. The oldest leave first. */
export const MAX_TOASTS = 3;

/** Errors stay longer so they can be read. */
export const TOAST_DURATION_MS: Record<ToastKind, number> = {
  success: 4000,
  info: 4000,
  warning: 6000,
  error: 8000,
};

/** Appends a toast and drops the oldest ones beyond `max`. */
export function enqueue(list: readonly Toast[], toast: Toast, max = MAX_TOASTS): Toast[] {
  const next = [...list, toast];
  return next.length > max ? next.slice(next.length - max) : next;
}

export function dismiss(list: readonly Toast[], id: number): Toast[] {
  return list.filter((toast) => toast.id !== id);
}
