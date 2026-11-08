import { useCallback, useMemo, useRef, useState } from "react";
import { ApiError, api } from "./lib/api";
import { useLocationEvidence, useReferenceData } from "./lib/hooks";
import { DEFAULT_PERIOD, type Period } from "./lib/periods";
import { buildRequest, demoForm, fieldForApiPath, initialForm, validate, type FormIssue, type Place, type ScenarioForm, type Step } from "./lib/scenario";
import type { CompareRequestBody, TimeMode } from "./lib/types";
import { EvidenceProvider } from "./components/Evidence";
import { Header } from "./components/Header";
import { Hero } from "./components/hero/Hero";
import { LocationSection } from "./components/location/LocationSection";
import { ScenarioSection } from "./components/scenario/ScenarioSection";
import { ComparisonSection, type Comparison } from "./components/compare/ComparisonSection";
import { Footer, SourcesSection } from "./components/SourcesSection";

const scrollToId = (id: string) => document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });

export function App() {
  const reference = useReferenceData();
  const [place, setPlace] = useState<Place>({ kind: "example", exampleId: "klaten_cropland_primary" });
  const [period, setPeriod] = useState<Period>(DEFAULT_PERIOD);
  const [timeMode, setTimeMode] = useState<TimeMode>("historical_replay");
  const evidence = useLocationEvidence(place, period, timeMode);

  const [form, setForm] = useState<ScenarioForm>(() => initialForm(DEFAULT_PERIOD, "historical_replay"));
  const [showErrors, setShowErrors] = useState(false);
  const [apiIssues, setApiIssues] = useState<FormIssue[]>([]);
  const [comparison, setComparison] = useState<Comparison>({ state: "idle" });
  const [stepRequest, setStepRequest] = useState<{ step: Step; field?: string; nonce: number } | null>(null);
  const [demoAsk, setDemoAsk] = useState(0);
  const lastRequest = useRef<{ body: CompareRequestBody | null; origin: "form" | "demo" } | null>(null);

  const update = useCallback((updater: (form: ScenarioForm) => ScenarioForm) => {
    setForm((current) => updater(current));
    setApiIssues([]);
  }, []);

  const issues = useMemo(() => [...validate(form, place), ...apiIssues], [form, place, apiIssues]);
  const currentKey = useMemo(() => {
    const body = buildRequest(form, place);
    return body ? JSON.stringify(body) : null;
  }, [form, place]);
  const stale = comparison.state === "ready" && comparison.origin === "form" && comparison.requestKey !== currentKey;

  const run = useCallback(async (body: CompareRequestBody | null, origin: "form" | "demo") => {
    lastRequest.current = { body, origin };
    setComparison({ state: "loading", origin });
    requestAnimationFrame(() => scrollToId("perbandingan"));
    try {
      if (origin === "demo" || !body) {
        const demo = await api.demo();
        setComparison({ state: "ready", origin: "demo", result: demo.analysis, requestKey: null });
      } else {
        const result = await api.compare(body);
        setComparison({ state: "ready", origin: "form", result, requestKey: JSON.stringify(body) });
      }
    } catch (error) {
      const apiError = error instanceof ApiError ? error : new ApiError(0, "unknown", "Analisis belum dapat diproses.");
      if (apiError.isInputError && apiError.details.length) {
        setApiIssues(
          apiError.details.map((detail) => {
            const target = fieldForApiPath(detail.field);
            return { field: target.field, step: target.step, message: detail.message };
          }),
        );
        setShowErrors(true);
      }
      setComparison({ state: "error", origin, error: apiError });
    }
  }, []);

  const submit = useCallback(() => {
    const found = validate(form, place);
    if (found.length) {
      setShowErrors(true);
      setStepRequest({ step: found[0].step, field: found[0].field, nonce: Date.now() });
      return;
    }
    setShowErrors(false);
    void run(buildRequest(form, place), "form");
  }, [form, place, run]);

  const applyDemo = useCallback(() => {
    setForm(demoForm());
    setShowErrors(false);
    setApiIssues([]);
  }, []);

  const changePlace = useCallback((next: Place) => setPlace(next), []);

  return (
    <EvidenceProvider catalog={reference.state === "ready" ? reference.data.catalog.sources : undefined}>
      <a className="skip-link" href="#kondisi">
        Langsung ke kondisi lokasi
      </a>
      <Header />
      <main>
        <Hero />
        <LocationSection
          reference={reference}
          place={place}
          onPlace={changePlace}
          period={period}
          onPeriod={setPeriod}
          timeMode={timeMode}
          onTimeMode={setTimeMode}
          evidence={evidence}
          onCompose={() => {
            setStepRequest({ step: 1, nonce: Date.now() });
            scrollToId("skenario");
          }}
          onDemo={() => void run(null, "demo")}
        />
        <ScenarioSection
          form={form}
          update={update}
          place={place}
          onPlace={changePlace}
          crops={reference.state === "ready" ? reference.data.crops : []}
          issues={issues}
          showErrors={showErrors}
          busy={comparison.state === "loading"}
          onSubmit={submit}
          onApplyDemo={applyDemo}
          stepRequest={stepRequest}
          demoAsk={demoAsk}
        />
        <ComparisonSection
          comparison={comparison}
          stale={stale}
          onRecompute={submit}
          onRetry={() => lastRequest.current && void run(lastRequest.current.body, lastRequest.current.origin)}
          onCompose={() => scrollToId("skenario")}
          onDemo={() => void run(null, "demo")}
          onCopyDemo={() => {
            setDemoAsk((value) => value + 1);
            scrollToId("skenario");
          }}
        />
        <SourcesSection catalog={reference.state === "ready" ? reference.data.catalog.sources : undefined} />
      </main>
      <Footer />
    </EvidenceProvider>
  );
}
