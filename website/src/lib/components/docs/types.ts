export type NavGroup = { id: string; label: string; pages: { slug: string; title: string }[] };

export type TocItem = { id: string; title: string; level: 2 | 3 };

export type CodeLabels = {
  copy: string;
  copied: string;
  failed: string;
  copiedMessage: string;
  failedMessage: string;
  /** Contains {title}. */
  copyCodeLabel: string;
  terminal: string;
  outputLabel: string;
};
