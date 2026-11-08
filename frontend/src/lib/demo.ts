import { addDays } from "./dates";
import type { CropId } from "./types";

// Mirrors backend/fieldshift/demo.py: a synthetic 2025 calendar over real historical context.
// These are scenario assumptions, never farmer records or predictions.
export const DEMO = {
  horizonStart: "2025-01-01",
  horizonEndExclusive: "2026-01-01",
  slotStarts: ["2025-01-01", "2025-06-01"] as const,
  durations: { padi: 120, jagung: 100, kedelai: 90 } as Record<CropId, number>,
  prepGapDays: 14,
  assumptions: [
    "Kalender sintetis untuk demonstrasi historis 2025, bukan riwayat petani.",
    "Padi ditanam langsung; umur padi 120, jagung 100, kedelai 90 hari sejak semai (hari nol).",
    "Tanggal mulai 1 Januari dan 1 Juni; jeda persiapan 14 hari merupakan asumsi.",
  ],
  sharedCalendarNote: "Tanggal mulai dan tanam langsung pada tiap posisi dipakai bersama oleh tanaman alternatif (asumsi demo).",
};

export interface HeroScenario {
  id: string;
  sequence: [CropId, CropId];
}

export const HERO_SCENARIOS: HeroScenario[] = [
  { id: "padi-padi", sequence: ["padi", "padi"] },
  { id: "padi-jagung", sequence: ["padi", "jagung"] },
  { id: "padi-kedelai", sequence: ["padi", "kedelai"] },
];

export interface DemoCycle {
  crop: CropId;
  start: string;
  harvest: string;
  release: string;
  days: number;
}

/** Same rule as the backend calendar: day 0 = sowing, harvest day still occupies the field. */
export function demoCycles(sequence: CropId[]): DemoCycle[] {
  return sequence.map((crop, index) => {
    const start = DEMO.slotStarts[index] ?? DEMO.slotStarts[DEMO.slotStarts.length - 1];
    const days = DEMO.durations[crop];
    const harvest = addDays(start, days);
    return { crop, start, harvest, release: addDays(harvest, 1), days };
  });
}
