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

import type { DocIconName } from "./DocIcon.svelte";

/** Icon of each page in the sidebar and on the cards. A page without an entry gets the plain document icon. */
export const DOC_ICONS: Record<string, DocIconName> = {
  quickstart: "rocket",
  configuration: "sliders",
  architecture: "layers",
  dashboard: "monitor",
  detect: "camera",
  sessions: "clock",
  export: "download",
  "compare-benchmark": "compare",
  "batch-import": "upload",
  analytics: "chart",
  "sorting-arm": "arm",
  "live-inference": "camera",
  datasets: "database",
  "train-evaluate": "train",
  "export-edge": "chip",
  "raspberry-pi": "chip",
  models: "box",
  cli: "terminal",
  "dashboard-api": "plug",
  limitations: "alert",
  troubleshooting: "alert",
  faq: "help",
  changelog: "list",
};

export const docIcon = (slug: string): DocIconName => DOC_ICONS[slug] ?? "doc";
