import { dismiss, enqueue, TOAST_DURATION_MS, type Toast, type ToastKind } from '../toast-queue';

/** Toast notifications. Errors stay longer; at most three are shown. */
class ToastStore {
  items = $state.raw<Toast[]>([]);
  private nextId = 1;
  private timers = new Map<number, ReturnType<typeof setTimeout>>();

  show(kind: ToastKind, message: string): number {
    const id = this.nextId;
    this.nextId += 1;
    const next = enqueue(this.items, { id, kind, message });
    this.items = next;
    // Toasts that were pushed out of the queue must not keep a timer.
    for (const [timerId, timer] of this.timers) {
      if (!next.some((toast) => toast.id === timerId)) {
        clearTimeout(timer);
        this.timers.delete(timerId);
      }
    }
    const timer = setTimeout(() => this.dismiss(id), TOAST_DURATION_MS[kind]);
    this.timers.set(id, timer);
    return id;
  }

  success(message: string): number {
    return this.show('success', message);
  }

  error(message: string): number {
    return this.show('error', message);
  }

  info(message: string): number {
    return this.show('info', message);
  }

  warning(message: string): number {
    return this.show('warning', message);
  }

  dismiss(id: number): void {
    const timer = this.timers.get(id);
    if (timer !== undefined) clearTimeout(timer);
    this.timers.delete(id);
    this.items = dismiss(this.items, id);
  }
}

export const toasts = new ToastStore();
