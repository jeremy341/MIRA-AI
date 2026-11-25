/** Ids that tie a form control to its hint and error text. Used by Field and by the controls. */

export function hintId(id: string): string {
  return `${id}-hint`;
}

export function errorId(id: string): string {
  return `${id}-error`;
}

/** The value for `aria-describedby`, or undefined when there is no hint and no error. */
export function describedBy(id: string, options: { hint?: string; error?: string }): string | undefined {
  const ids: string[] = [];
  if (options.hint) ids.push(hintId(id));
  if (options.error) ids.push(errorId(id));
  return ids.length ? ids.join(' ') : undefined;
}
