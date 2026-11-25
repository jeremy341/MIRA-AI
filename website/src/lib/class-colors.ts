import { CLASS_BY_ID, type ClassId } from "./site";

/** Border colour for a class. Plastic yellow gets its darker variant so the border reaches 3:1 on paper. */
export function classBorderVar(cls: ClassId): string {
  return cls === "plastic" ? "var(--class-plastic-ink)" : CLASS_BY_ID[cls].cssVar;
}

/** Class tag text colour: white on every class fill except plastic yellow, which takes ink. */
export function tagTextColor(cls: ClassId): string {
  return cls === "plastic" ? "var(--ink)" : "#ffffff";
}
