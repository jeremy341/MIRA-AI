import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { repeatWhileVisible, type VisibilitySource } from "./repeat-while-visible";

function fakePage() {
  const listeners = new Set<() => void>();
  const page = {
    hidden: false,
    addEventListener: (_type: string, listener: () => void) => listeners.add(listener),
    removeEventListener: (_type: string, listener: () => void) => listeners.delete(listener),
  };
  return {
    page: page as unknown as VisibilitySource,
    listeners,
    show(visible: boolean) {
      page.hidden = !visible;
      for (const listener of listeners) listener();
    },
  };
}

describe("repeatWhileVisible", () => {
  beforeEach(() => void vi.useFakeTimers());
  afterEach(() => void vi.useRealTimers());

  it("waits a full interval before the first run, then repeats", () => {
    const task = vi.fn();
    repeatWhileVisible(task, 1000, fakePage().page);
    vi.advanceTimersByTime(999);
    expect(task).toHaveBeenCalledTimes(0);
    vi.advanceTimersByTime(2001);
    expect(task).toHaveBeenCalledTimes(3);
  });

  it("does nothing while hidden and catches up once when shown again", () => {
    const task = vi.fn();
    const { page, show } = fakePage();
    repeatWhileVisible(task, 1000, page);
    show(false);
    vi.advanceTimersByTime(10_000);
    expect(task).toHaveBeenCalledTimes(0);
    show(true);
    expect(task).toHaveBeenCalledTimes(1);
  });

  it("does not run early when the tab is only switched back and forth", () => {
    const task = vi.fn();
    const { page, show } = fakePage();
    repeatWhileVisible(task, 1000, page);
    vi.advanceTimersByTime(300);
    show(false);
    show(true);
    expect(task).toHaveBeenCalledTimes(0);
  });

  it("stops", () => {
    const task = vi.fn();
    const { page, show, listeners } = fakePage();
    repeatWhileVisible(task, 1000, page)();
    vi.advanceTimersByTime(5000);
    show(true);
    expect(task).toHaveBeenCalledTimes(0);
    expect(listeners.size).toBe(0);
  });
});
