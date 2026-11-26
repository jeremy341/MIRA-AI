/** The slice of `document` this needs, so tests can pass a fake. */
export type VisibilitySource = Pick<Document, "hidden" | "addEventListener" | "removeEventListener">;

/**
 * Run `task` every `everyMs` while the page is visible. A hidden tab does nothing; when it is shown again and a run
 * is overdue, the task runs at once. The first run is left to the caller. Returns a function that stops it.
 */
export function repeatWhileVisible(task: () => void, everyMs: number, page: VisibilitySource = document): () => void {
  let last = Date.now();
  const runIfDue = () => {
    if (page.hidden || Date.now() - last < everyMs) return;
    last = Date.now();
    task();
  };
  const timer = setInterval(runIfDue, everyMs);
  page.addEventListener("visibilitychange", runIfDue);
  return () => {
    clearInterval(timer);
    page.removeEventListener("visibilitychange", runIfDue);
  };
}
