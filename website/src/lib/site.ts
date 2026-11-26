/**
 * Site-wide constants. Every page and component imports links, class
 * definitions and headline facts from here so the numbers stay consistent.
 *
 * Facts below come from README.md and results/experiments_log.md in the
 * repository root. Do not add numbers that are not recorded there.
 */

export const SITE_NAME = "MIRA";
export const SITE_TITLE = "MIRA - Machine Intelligence for Recycling Automation";
export const SITE_DESCRIPTION =
  "MIRA is an open-source YOLO11n detector for glass, metal, paper, plastic and trash in camera images. Results, experiments and the mira-ai Python package.";
export const SITE_URL = "https://mira-vision.vercel.app";

export const GITHUB_URL = "https://github.com/jeremy341/MIRA-AI";
export const PYPI_URL = "https://pypi.org/project/mira-ai/";
export const HF_REPO = "Jeremy341/MIRA-AI";
export const HF_URL = `https://huggingface.co/${HF_REPO}`;
export const DATASET_ORIGINS_URL = `${GITHUB_URL}/blob/main/docs/DATASET_ORIGINS.md`;
export const EXPERIMENT_LOG_URL = `${GITHUB_URL}/blob/main/results/experiments_log.md`;
export const LICENSE_URL = `${GITHUB_URL}/blob/main/LICENSE`;

/**
 * Latest release published on PyPI (checked against https://pypi.org/pypi/mira-ai/json).
 * Keep it equal to src/version.py once a release is published, and update it with every release.
 */
export const PYPI_LATEST_VERSION = "1.1.0";

/**
 * Last known Hugging Face download count (10,323, read from the Hugging Face API on 2026-11-26).
 * Server-rendered until a live or cached value replaces it.
 */
export const FALLBACK_DOWNLOADS = 10323;

export const INSTALL_COMMAND = "pip install mira-ai";

export type NavKey = "research" | "package" | "docs";

export type NavItem = {
  key: NavKey;
  /** Path without a language prefix. */
  href: string;
};

/** Primary navigation in header order. Labels come from the dictionaries (nav.*). */
export const NAV_ITEMS: readonly NavItem[] = [
  { key: "research", href: "/research" },
  { key: "package", href: "/package" },
  { key: "docs", href: "/docs" },
];

export type ClassId = "glass" | "metal" | "paper" | "plastic" | "trash";

export type ClassDefinition = {
  id: ClassId;
  label: string;
  /** CSS custom property holding the class colour, e.g. `--class-glass`. */
  token: `--class-${ClassId}`;
  /** Ready-to-use `var(...)` reference for inline styles. */
  cssVar: `var(--class-${ClassId})`;
  /** Ultralytics class index used in the dataset. */
  index: number;
};

function defineClass(id: ClassId, label: string, index: number): ClassDefinition {
  return { id, label, token: `--class-${id}`, cssVar: `var(--class-${id})`, index };
}

/** The five MIRA classes, in dataset order. Class colour is the only colour in the UI. */
export const CLASSES: readonly ClassDefinition[] = [
  defineClass("glass", "glass", 0),
  defineClass("metal", "metal", 1),
  defineClass("paper", "paper", 2),
  defineClass("plastic", "plastic", 3),
  defineClass("trash", "trash", 4),
];

export const CLASS_BY_ID: Readonly<Record<ClassId, ClassDefinition>> = {
  glass: CLASSES[0],
  metal: CLASSES[1],
  paper: CLASSES[2],
  plastic: CLASSES[3],
  trash: CLASSES[4],
};

/**
 * Recorded results. All figures are validation metrics on the TrashNet
 * tabletop split (415 images), not real-world sorting accuracy.
 */
export const FACTS = {
  exp014Map50: 60.7,
  exp018Map50: 90.6,
  exp019Map50: 90.58,
  exp019Map5095: 82.15,
  exp019Precision: 87.2,
  exp019Recall: 84.6,
  exp019TrainingHours: 2.67,
  exp019PlasticRecall: 64.4,
  validationImages: 415,
  testImages: 1375,
  trainImages: 5108,
  experimentCount: 19,
  lastExperiment: "EXP-019",
  classCount: 5,
} as const;
