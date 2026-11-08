export interface Period {
  id: string;
  label: string;
  start: string;
  endExclusive: string;
  partial?: boolean;
}

const year = (y: number): Period => ({ id: String(y), label: String(y), start: `${y}-01-01`, endExclusive: `${y + 1}-01-01` });

// MODIS samples cover 2021–2026; POWER covers 1991–2026. Default is the documented 2025 replay.
export const PERIODS: Period[] = [
  year(2025),
  year(2024),
  year(2023),
  year(2022),
  year(2021),
  { id: "2026", label: "2026 · parsial", start: "2026-01-01", endExclusive: "2026-11-08", partial: true },
];

export const DEFAULT_PERIOD = PERIODS[0];
