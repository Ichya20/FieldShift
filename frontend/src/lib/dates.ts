// Date-only ISO helpers in UTC, so local time zones never shift a calendar day.

const DAY = 86_400_000;

export function parseIso(iso: string): Date {
  return new Date(`${iso}T00:00:00Z`);
}

export function toIso(date: Date): string {
  return date.toISOString().slice(0, 10);
}

export function isIsoDate(value: string | null | undefined): value is string {
  if (!value || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const parsed = parseIso(value);
  return !Number.isNaN(parsed.getTime()) && toIso(parsed) === value;
}

export function addDays(iso: string, days: number): string {
  return toIso(new Date(parseIso(iso).getTime() + days * DAY));
}

export function daysBetween(start: string, end: string): number {
  return Math.round((parseIso(end).getTime() - parseIso(start).getTime()) / DAY);
}

/** Fraction of [start, endExclusive) at which `iso` falls; clamped to 0..1. */
export function position(iso: string, start: string, endExclusive: string): number {
  const span = daysBetween(start, endExclusive);
  if (span <= 0) return 0;
  return Math.min(1, Math.max(0, daysBetween(start, iso) / span));
}

/** Calendar months covering [start, endExclusive), as YYYY-MM-01 strings. */
export function monthStarts(start: string, endExclusive: string): string[] {
  const out: string[] = [];
  const first = parseIso(start);
  let cursor = new Date(Date.UTC(first.getUTCFullYear(), first.getUTCMonth(), 1));
  const end = parseIso(endExclusive);
  while (cursor < end) {
    out.push(toIso(cursor));
    cursor = new Date(Date.UTC(cursor.getUTCFullYear(), cursor.getUTCMonth() + 1, 1));
  }
  return out;
}

export function yearOf(iso: string): number {
  return parseIso(iso).getUTCFullYear();
}
