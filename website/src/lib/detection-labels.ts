import type { Dictionary } from "$i18n";
import type { ClassId } from "./site";

export type DetectionFigureLabels = {
  figure: string;
  /** Fixed name of the toggle button, e.g. "Detection boxes". Its state is aria-pressed, not the text. */
  boxesToggle: string;
  /** Visible state words next to the name, e.g. "on" and "off". Hidden from assistive technology. */
  boxesOn: string;
  boxesOff: string;
  altPrefix: string;
  altNone: string;
  altListIntro: string;
  /** Contains {cls} and {conf}. */
  altItem: string;
  placeholderTitle: string;
  /** Contains {file}. */
  placeholderHint: string;
  classes: Record<ClassId, string>;
};

/** The texts DetectionFigure needs, picked out of a dictionary. */
export function detectionLabels(dict: Dictionary): DetectionFigureLabels {
  return {
    figure: dict.common.figure,
    boxesToggle: dict.figures.boxesToggle,
    boxesOn: dict.figures.boxesOn,
    boxesOff: dict.figures.boxesOff,
    altPrefix: dict.figures.altPrefix,
    altNone: dict.figures.altNone,
    altListIntro: dict.figures.altListIntro,
    altItem: dict.figures.altItem,
    placeholderTitle: dict.figures.placeholderTitle,
    placeholderHint: dict.figures.placeholderHint,
    classes: dict.common.classes,
  };
}
