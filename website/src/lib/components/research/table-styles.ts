/** Shared class names, so every table on the page reads the same (a paper-style table: heavy rule, header rule, hairlines). */
export const TABLE = "w-full border-collapse text-left text-[0.9375rem] leading-snug";
export const THEAD = "border-y-2 border-ink [&_th]:text-[0.8125rem] [&_th]:font-medium [&_th]:text-muted-foreground";
export const TBODY = "[&>tr]:border-b [&>tr]:border-rule [&>tr:last-child]:border-ink";
export const TH = "py-2 pr-4 align-bottom";
export const TH_LAST = "py-2 pr-0 align-bottom";
export const TH_NUM = "py-2 pr-1 pl-3 text-right align-bottom";
export const TD = "py-2.5 pr-4 align-top";
export const TD_LAST = "py-2.5 pr-0 align-top";
export const NUM = "py-2.5 pl-3 pr-1 text-right font-mono tabular align-top whitespace-nowrap";
/** Same as NUM, left aligned (the score column of the experiment index). */
export const NUM_LEFT = "py-2.5 pl-3 pr-1 text-left font-mono tabular align-top whitespace-nowrap";
