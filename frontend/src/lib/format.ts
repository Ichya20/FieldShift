import { addDays, parseIso } from "./dates";

const MINUS = "\u2212";
const cache = new Map<string, Intl.NumberFormat>();

function numberFormat(digits: number) {
  const key = String(digits);
  let format = cache.get(key);
  if (!format) {
    format = new Intl.NumberFormat("id-ID", { minimumFractionDigits: digits, maximumFractionDigits: digits });
    cache.set(key, format);
  }
  return format;
}

/** Indonesian grouping and decimal comma: 2964.05 → "2.964,05". Unknown stays an em dash. */
export function num(value: number | null | undefined, digits = 2): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return "—";
  const text = numberFormat(digits).format(Math.abs(value));
  return value < 0 && text.replace(/[0,.]/g, "") !== "" ? MINUS + text : text;
}

/** Signed difference, e.g. P−ETo: "+1.591,95". */
export function signed(value: number | null | undefined, digits = 2): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return "—";
  const text = numberFormat(digits).format(Math.abs(value));
  if (text.replace(/[0,.]/g, "") === "") return text;
  return (value > 0 ? "+" : MINUS) + text;
}

export function coord(value: number | null | undefined, digits = 6): string {
  return num(value, digits);
}

export function percent(fraction: number | null | undefined, digits = 1): string {
  if (fraction === null || fraction === undefined) return "—";
  return `${num(fraction * 100, digits)}%`;
}

const dateLong = new Intl.DateTimeFormat("id-ID", { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" });
const dateShort = new Intl.DateTimeFormat("id-ID", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" });
const dayMonth = new Intl.DateTimeFormat("id-ID", { day: "numeric", month: "short", timeZone: "UTC" });
const monthShort = new Intl.DateTimeFormat("id-ID", { month: "short", timeZone: "UTC" });
const monthLong = new Intl.DateTimeFormat("id-ID", { month: "long", year: "numeric", timeZone: "UTC" });

export const fmtDate = (iso: string | null | undefined) => (iso ? dateLong.format(parseIso(iso)) : "—");
export const fmtDateShort = (iso: string | null | undefined) => (iso ? dateShort.format(parseIso(iso)) : "—");
export const fmtDayMonth = (iso: string | null | undefined) => (iso ? dayMonth.format(parseIso(iso)) : "—");
export const fmtMonthShort = (iso: string) => monthShort.format(parseIso(iso)).replace(".", "");
export const fmtMonthLong = (iso: string) => monthLong.format(parseIso(iso));

/** "1 Januari–31 Desember 2025" for a half-open window (end exclusive is shown inclusive). */
export function fmtWindow(start: string, endExclusive: string): string {
  const last = addDays(endExclusive, -1);
  const a = parseIso(start);
  const b = parseIso(last);
  if (a.getUTCFullYear() === b.getUTCFullYear()) {
    const head = new Intl.DateTimeFormat("id-ID", { day: "numeric", month: "long", timeZone: "UTC" }).format(a);
    return `${head}–${fmtDate(last)}`;
  }
  return `${fmtDate(start)}–${fmtDate(last)}`;
}

export function fmtWindowShort(start: string, endExclusive: string): string {
  return `${fmtDateShort(start)}–${fmtDateShort(addDays(endExclusive, -1))}`;
}
