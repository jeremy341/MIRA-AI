import { getDictionary } from "$i18n";
import type { Locale } from "$i18n/config";
import type { DocsUi } from "$i18n/docs/ui";
import type { CodeLabels, TocItem } from "./types";
import type { DocPage } from "$lib/docs-content";

/** Labels for a code block, from the shared copy strings and the docs interface strings. */
export function codeLabelsFor(lang: Locale, ui: DocsUi): CodeLabels {
  const copy = getDictionary(lang).common.copy;
  return {
    copy: copy.copy,
    copied: copy.copied,
    failed: copy.failed,
    copiedMessage: copy.copiedMessage,
    failedMessage: copy.failedMessage,
    copyCodeLabel: ui.copyCodeLabel,
    terminal: ui.terminal,
    outputLabel: ui.outputLabel,
  };
}

/** "On this page" entries: every section (level 2) and the h3 headings inside it (level 3). */
export function tocItemsFor(page: DocPage): TocItem[] {
  return page.sections.flatMap((section) => [
    { id: section.id, title: section.title, level: 2 as const },
    ...section.blocks.flatMap((block) =>
      block.type === "h3" ? [{ id: block.id, title: block.text, level: 3 as const }] : [],
    ),
  ]);
}
