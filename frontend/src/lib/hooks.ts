import { useCallback, useEffect, useRef, useState, useSyncExternalStore } from "react";
import { ApiError, api, isAbort } from "./api";
import type { CatalogResponse, ContextResponse, CropReference, MonthlyClimateResponse, ResolvedLocation, TimeMode } from "./types";
import type { Period } from "./periods";
import { placeToLocation, type Place } from "./scenario";

export type Load<T> =
  | { state: "loading"; data?: undefined; error?: undefined }
  | { state: "ready"; data: T; error?: undefined }
  | { state: "error"; data?: undefined; error: ApiError };

const toApiError = (error: unknown) =>
  error instanceof ApiError ? error : new ApiError(0, "unknown", "Data belum dapat dimuat.");

export interface ReferenceData {
  locations: ResolvedLocation[];
  crops: CropReference[];
  catalog: CatalogResponse;
}

export function useReferenceData() {
  const [load, setLoad] = useState<Load<ReferenceData>>({ state: "loading" });
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setLoad({ state: "loading" });
    Promise.all([api.locations(controller.signal), api.crops(controller.signal), api.catalog(controller.signal)])
      .then(([locations, crops, catalog]) =>
        setLoad({ state: "ready", data: { locations: locations.locations, crops: crops.crops, catalog } }),
      )
      .catch((error) => {
        if (!isAbort(error)) setLoad({ state: "error", error: toApiError(error) });
      });
    return () => controller.abort();
  }, [attempt]);
  const retry = useCallback(() => setAttempt((value) => value + 1), []);
  return { ...load, retry };
}

export interface LocationEvidence {
  context: ContextResponse;
  monthly: MonthlyClimateResponse;
}

/** Context layers plus the monthly climate slices for the same place, period and time mode. */
export function useLocationEvidence(place: Place, period: Period, timeMode: TimeMode) {
  const [load, setLoad] = useState<Load<LocationEvidence> | { state: "idle" }>({ state: "loading" });
  const [attempt, setAttempt] = useState(0);
  const location = placeToLocation(place);
  const key = JSON.stringify([location, period.start, period.endExclusive, timeMode, attempt]);
  useEffect(() => {
    if (!location) {
      setLoad({ state: "idle" });
      return;
    }
    const controller = new AbortController();
    const body = { location, window: { start_date: period.start, end_exclusive: period.endExclusive }, time_mode: timeMode };
    setLoad({ state: "loading" });
    Promise.all([api.context(body, controller.signal), api.monthlyClimate(body, controller.signal)])
      .then(([context, monthly]) => setLoad({ state: "ready", data: { context, monthly } }))
      .catch((error) => {
        if (!isAbort(error)) setLoad({ state: "error", error: toApiError(error) });
      });
    return () => controller.abort();
    // `key` captures every input of the request.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);
  const retry = useCallback(() => setAttempt((value) => value + 1), []);
  return { load, retry };
}

export function useMediaQuery(query: string): boolean {
  const subscribe = useCallback(
    (notify: () => void) => {
      const media = window.matchMedia(query);
      media.addEventListener("change", notify);
      return () => media.removeEventListener("change", notify);
    },
    [query],
  );
  return useSyncExternalStore(
    subscribe,
    () => window.matchMedia(query).matches,
    () => false,
  );
}

export const useReducedMotion = () => useMediaQuery("(prefers-reduced-motion: reduce)");

/** Highlights the header link of the section currently in view. */
export function useActiveSection(ids: string[]): string | null {
  const [active, setActive] = useState<string | null>(null);
  const idsKey = ids.join("|");
  useEffect(() => {
    const visible = new Map<string, number>();
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) visible.set(entry.target.id, entry.isIntersecting ? entry.intersectionRatio : 0);
        let best: string | null = null;
        let ratio = 0;
        for (const [id, value] of visible) {
          if (value > ratio) {
            best = id;
            ratio = value;
          }
        }
        setActive(best);
      },
      { rootMargin: "-30% 0px -55% 0px", threshold: [0, 0.01, 0.2, 0.5] },
    );
    for (const id of idsKey.split("|")) {
      const element = document.getElementById(id);
      if (element) observer.observe(element);
    }
    return () => observer.disconnect();
  }, [idsKey]);
  return active;
}

/** Element visibility for pausing work (e.g. the 3D render loop) while offscreen. */
export function useInView<T extends Element>(rootMargin = "100px") {
  const ref = useRef<T | null>(null);
  const [inView, setInView] = useState(true);
  useEffect(() => {
    const element = ref.current;
    if (!element) return;
    const observer = new IntersectionObserver(([entry]) => setInView(entry.isIntersecting), { rootMargin });
    observer.observe(element);
    return () => observer.disconnect();
  }, [rootMargin]);
  return { ref, inView };
}
