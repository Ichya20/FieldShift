import { ChevronDown, Lock, RefreshCw } from "lucide-react";
import { Fragment, useState } from "react";
import type { ApiError } from "../../lib/api";
import { monthStarts, position } from "../../lib/dates";
import { fmtDateShort, fmtMonthShort, fmtWindow, num, signed } from "../../lib/format";
import { useMediaQuery } from "../../lib/hooks";
import { CROPS, GENERATION_ERRORS, RULES, RULE_ORDER, STRATEGY_LABEL, missingLabel, sequenceLabel, timeModeLabel } from "../../lib/labels";
import type { CompareResponse, RuleId, Strategy } from "../../lib/types";
import { SourceButton } from "../Evidence";
import { StatusBadge } from "../StatusBadge";
import { PLACE_LABEL } from "../location/PlacePicker";
import { RuleEvidence } from "./details";

export type Comparison =
  | { state: "idle" }
  | { state: "loading"; origin: "form" | "demo" }
  | { state: "ready"; origin: "form" | "demo"; result: CompareResponse; requestKey: string | null }
  | { state: "error"; origin: "form" | "demo"; error: ApiError };

interface Props {
  comparison: Comparison;
  stale: boolean;
  onRecompute: () => void;
  onRetry: () => void;
  onCompose: () => void;
  onDemo: () => void;
  onCopyDemo: () => void;
}

export function ComparisonSection({ comparison, stale, onRecompute, onRetry, onCompose, onDemo, onCopyDemo }: Props) {
  return (
    <section id="perbandingan" className="section section--compare" aria-labelledby="perbandingan-title">
      <div className="container">
        <header className="section-head section-head--row">
          <div>
            <h2 id="perbandingan-title">Perbandingan strategi</h2>
            <p>Bukti, kendala, dan informasi yang kurang pada rotasi berjalan dan dua alternatif, pada periode yang sama.</p>
          </div>
          {comparison.state === "ready" && (
            <button type="button" className="button button--secondary" onClick={onCompose}>
              Ubah skenario
            </button>
          )}
        </header>

        <div aria-live="polite">
          {comparison.state === "idle" && <EmptyBoard onCompose={onCompose} onDemo={onDemo} />}
          {comparison.state === "loading" && <LoadingBoard />}
          {comparison.state === "error" && (
            <div className="notice notice--conflict" role="alert">
              <div>
                <p>
                  <strong>{comparison.error.isInputError ? "Periksa isian." : "Data belum dapat dimuat. Coba lagi."}</strong>{" "}
                  {comparison.error.isInputError
                    ? "Layanan menolak sebagian isian. Rincian ditandai pada formulir."
                    : "Isian Anda tetap tersimpan selama sesi ini."}
                </p>
                {comparison.error.details.length > 0 && (
                  <ul className="plain-list">
                    {comparison.error.details.map((detail) => (
                      <li key={`${detail.field}-${detail.code}`}>{detail.message}</li>
                    ))}
                  </ul>
                )}
                <div className="notice__actions">
                  {comparison.error.isInputError ? (
                    <button type="button" className="button button--secondary button--small" onClick={onCompose}>
                      Ubah skenario
                    </button>
                  ) : (
                    <button type="button" className="button button--secondary button--small" onClick={onRetry}>
                      <RefreshCw aria-hidden="true" size={16} /> Coba lagi
                    </button>
                  )}
                </div>
              </div>
            </div>
          )}
          {comparison.state === "ready" && (
            <Results result={comparison.result} origin={comparison.origin} stale={stale} onRecompute={onRecompute} onCopyDemo={onCopyDemo} />
          )}
        </div>
      </div>
    </section>
  );
}

function EmptyBoard({ onCompose, onDemo }: { onCompose: () => void; onDemo: () => void }) {
  return (
    <div className="board board--empty">
      <div className="board__columns">
        {(["existing", "candidate_1", "candidate_2"] as const).map((id) => (
          <div key={id} className="board__column">
            <p className="board__label">{STRATEGY_LABEL[id]}</p>
            <p className="board__empty">Belum ada skenario</p>
          </div>
        ))}
      </div>
      <div className="board__cta">
        <p>Susun rotasi berjalan dan pilihan tanaman, atau buka contoh historis 2025 yang memakai kalender asumsi.</p>
        <div className="notice__actions">
          <button type="button" className="button button--primary" onClick={onCompose}>
            Susun skenario
          </button>
          <button type="button" className="button button--secondary" onClick={onDemo}>
            Lihat contoh 2025
          </button>
        </div>
      </div>
    </div>
  );
}

function LoadingBoard() {
  return (
    <div className="board" aria-busy="true">
      <p className="board__loading">Memeriksa skenario…</p>
      <div className="board__columns">
        {(["existing", "candidate_1", "candidate_2"] as const).map((id) => (
          <div key={id} className="board__column">
            <p className="board__label">{STRATEGY_LABEL[id]}</p>
            <div className="skeleton" style={{ height: 22, width: "60%" }} />
            <div className="skeleton" style={{ height: 16, width: "80%", marginTop: 10 }} />
          </div>
        ))}
      </div>
    </div>
  );
}

function Results({ result, origin, stale, onRecompute, onCopyDemo }: { result: CompareResponse; origin: "form" | "demo"; stale: boolean; onRecompute: () => void; onCopyDemo: () => void }) {
  const wide = useMediaQuery("(min-width: 960px)");
  const strategies = result.strategies;
  const available = strategies.filter((s) => s.sequence !== null).length;
  const context = result.context;
  const window = context.window;
  const location = context.location.example_id ? PLACE_LABEL[context.location.example_id] : "Titik pilihan";
  const generation = result.generation;
  const message =
    result.analysis_status === "invalid_input"
      ? "Sebagian isian tidak dapat diproses. Periksa catatan di bawah."
      : available === 3
        ? "Tiga skenario untuk ditinjau. Sebagian pemeriksaan masih memerlukan informasi."
        : available === 0
          ? "Belum ada urutan yang dapat dibandingkan. Lengkapi rotasi berjalan dan pilihan tanaman."
          : `${available} skenario untuk ditinjau. Slot yang kosong dijelaskan di kolomnya.`;

  return (
    <div className="results">
      <div className="results__context">
        <p className="results__where">
          {location} · {window ? fmtWindow(window.start_date, window.end_exclusive) : "Periode belum diisi"} · {timeModeLabel(context.requested_time_mode)}
        </p>
        <div className="results__tags">
          <span className="tag">{result.input_kind === "scenario_assumption" ? "Skenario asumsi" : "Isian pengguna"}</span>
          {origin === "demo" && <span className="tag">Contoh 2025 dari API demo</span>}
          <span className="tag">Metode {result.method_version}</span>
        </div>
      </div>
      <p className="results__message">{message}</p>
      {stale && (
        <div className="notice notice--review" role="status">
          <div>
            Isian telah berubah sejak hasil ini dihitung. Hasil di bawah masih untuk isian sebelumnya.
            <div className="notice__actions">
              <button type="button" className="button button--primary button--small" onClick={onRecompute}>
                Hitung ulang
              </button>
            </div>
          </div>
        </div>
      )}
      {origin === "demo" && (
        <p className="meta results__demo">
          Hasil ini memakai request demo backend, bukan isian formulir Anda.{" "}
          <button type="button" className="text-button" onClick={onCopyDemo}>
            Salin asumsi demo ke formulir
          </button>
        </p>
      )}
      {generation.errors.length > 0 && (
        <div className="notice notice--conflict">
          <ul className="plain-list">
            {generation.errors.map((error) => (
              <li key={`${error.field}-${error.code}`}>{GENERATION_ERRORS[error.code] ?? `${error.field}: ${error.code}`}</li>
            ))}
          </ul>
        </div>
      )}

      {wide ? <Board result={result} /> : <MobileSummary result={result} />}
      <Calendar result={result} wide={wide} />
      <SharedClimate result={result} />
      {wide ? <Matrix result={result} /> : <Aspects result={result} />}
      <p className="disclaimer">Alat bantu eksplorasi. Pertimbangan lapangan perlu ditinjau bersama petani atau penyuluh.</p>
    </div>
  );
}

function StrategyEmpty({ strategy, result }: { strategy: Strategy; result: CompareResponse }) {
  const status = result.generation.generation_status;
  return (
    <div className="board__empty-detail">
      <p className="board__empty">{strategy.strategy_id === "existing" ? "Rotasi berjalan belum lengkap" : "Belum ada alternatif untuk konfigurasi ini"}</p>
      <p className="meta">
        {strategy.strategy_id === "existing"
          ? "Isi urutan tanaman dan konfirmasi kelanjutan rotasi; riwayat tidak dibuat dari data yang tidak diketahui."
          : status === "insufficient_alternatives"
            ? "Pilihan tanaman atau slot terkunci menyisakan kurang dari dua kandidat. Tinjau pilihan tanaman atau slot terkunci."
            : `Perlu: ${result.generation.missing_inputs.map((code) => missingLabel(`planning.${code}`).toLowerCase()).join(", ") || "periksa isian"}.`}
      </p>
    </div>
  );
}

function SequenceChips({ strategy, locked }: { strategy: Strategy; locked: number }) {
  if (!strategy.sequence) return null;
  return (
    <ol className="sequence" aria-label={sequenceLabel(strategy.sequence)}>
      {strategy.sequence.map((crop, index) => (
        <Fragment key={index}>
          {index > 0 && (
            <li className="sequence__arrow" aria-hidden="true">
              →
            </li>
          )}
          <li className={`sequence__item sequence__item--${crop}`}>
            {index < locked && <Lock aria-label="slot terkunci" size={13} />}
            {CROPS[crop].name}
          </li>
        </Fragment>
      ))}
    </ol>
  );
}

const lockedOf = (result: CompareResponse, strategy: Strategy) => {
  const existing = result.generation.strategies.existing;
  if (!existing || !strategy.sequence) return 0;
  let count = 0;
  // A slot counts as locked when it is unchanged in every generated alternative.
  const all = [result.generation.strategies.candidate_1, result.generation.strategies.candidate_2].filter(Boolean) as string[][];
  for (let i = 0; i < existing.length; i++) {
    if (all.length && all.every((sequence) => sequence[i] === existing[i])) count = i + 1;
    else break;
  }
  return count;
};

function Board({ result }: { result: CompareResponse }) {
  return (
    <div className="board" role="table" aria-label="Ringkasan tiga strategi">
      <div className="board__row board__row--head" role="row">
        <span role="columnheader" className="board__rowlabel">
          <span className="visually-hidden">Aspek</span>
        </span>
        {result.strategies.map((strategy) => (
          <span key={strategy.strategy_id} role="columnheader" className="board__label">
            {STRATEGY_LABEL[strategy.strategy_id]}
          </span>
        ))}
      </div>
      <div className="board__row" role="row">
        <span role="rowheader" className="board__rowlabel">
          Urutan
        </span>
        {result.strategies.map((strategy) => (
          <div key={strategy.strategy_id} role="cell" className="board__cell">
            {strategy.sequence ? <SequenceChips strategy={strategy} locked={lockedOf(result, strategy)} /> : <StrategyEmpty strategy={strategy} result={result} />}
          </div>
        ))}
      </div>
      <div className="board__row" role="row">
        <span role="rowheader" className="board__rowlabel">
          Status
        </span>
        {result.strategies.map((strategy) => (
          <div key={strategy.strategy_id} role="cell" className="board__cell">
            {strategy.sequence && <StatusBadge status={strategy.status === "complete_for_selected_checks" ? strategy.status : "partial"} />}
          </div>
        ))}
      </div>
      <div className="board__row" role="row">
        <span role="rowheader" className="board__rowlabel">
          Dasar urutan
        </span>
        {result.strategies.map((strategy) => (
          <p key={strategy.strategy_id} role="cell" className="board__cell meta">
            {strategy.sequence ? strategy.generated_reason : "—"}
          </p>
        ))}
      </div>
      <div className="board__row" role="row">
        <span role="rowheader" className="board__rowlabel">
          Perlu dilengkapi
        </span>
        {result.strategies.map((strategy) => (
          <div key={strategy.strategy_id} role="cell" className="board__cell">
            {strategy.sequence && <MissingList codes={strategy.missing_inputs} />}
          </div>
        ))}
      </div>
    </div>
  );
}

function MissingList({ codes }: { codes: string[] }) {
  const [all, setAll] = useState(false);
  if (!codes.length) return <p className="meta">Tidak ada informasi yang diminta untuk pemeriksaan terpilih.</p>;
  const visible = all ? codes : codes.slice(0, 4);
  return (
    <div className="missing">
      <p className="missing__count">{codes.length} informasi</p>
      <ul>
        {visible.map((code) => (
          <li key={code}>{missingLabel(code)}</li>
        ))}
      </ul>
      {codes.length > 4 && (
        <button type="button" className="text-button" onClick={() => setAll((v) => !v)} aria-expanded={all}>
          {all ? "Ringkas" : `Lihat ${codes.length - 4} lainnya`}
        </button>
      )}
    </div>
  );
}

function MobileSummary({ result }: { result: CompareResponse }) {
  return (
    <ul className="mobile-strategies">
      {result.strategies.map((strategy) => (
        <li key={strategy.strategy_id} className="panel">
          <div className="mobile-strategies__head">
            <p className="board__label">{STRATEGY_LABEL[strategy.strategy_id]}</p>
            {strategy.sequence && <StatusBadge status={strategy.status === "complete_for_selected_checks" ? strategy.status : "partial"} compact />}
          </div>
          {strategy.sequence ? <SequenceChips strategy={strategy} locked={lockedOf(result, strategy)} /> : <StrategyEmpty strategy={strategy} result={result} />}
          {strategy.sequence && (
            <details className="mobile-strategies__details">
              <summary>Detail strategi</summary>
              <p className="meta">{strategy.generated_reason}</p>
              <MissingList codes={strategy.missing_inputs} />
            </details>
          )}
        </li>
      ))}
    </ul>
  );
}

function Calendar({ result, wide }: { result: CompareResponse; wide: boolean }) {
  const window = result.context.window;
  if (!window) return null;
  const start = window.start_date;
  const end = window.end_exclusive;
  const months = monthStarts(start, end);
  const pct = (iso: string) => `${(position(iso, start, end) * 100).toFixed(3)}%`;
  const width = (a: string, b: string) => `${Math.max(0, (position(b, start, end) - position(a, start, end)) * 100).toFixed(3)}%`;
  const label = result.input_kind === "scenario_assumption" ? "Kalender berdasarkan asumsi" : "Kalender dari isian pengguna";

  if (!wide) {
    return (
      <section className="panel calendar-list" aria-labelledby="calendar-title">
        <h3 id="calendar-title">Kalender · {fmtWindow(start, end)}</h3>
        <p className="meta">{label}. Hari panen masih menempati petak.</p>
        {result.strategies.map((strategy) => (
          <div key={strategy.strategy_id} className="calendar-list__strategy">
            <p className="board__label">{STRATEGY_LABEL[strategy.strategy_id]}</p>
            {strategy.sequence ? (
              <ul>
                {strategy.cycles.map((cycle) => (
                  <li key={cycle.slot_index}>
                    <span className={`crop-dot crop-dot--${cycle.crop_id}`} aria-hidden="true" /> {CROPS[cycle.crop_id].name}:{" "}
                    {cycle.calendar.status === "calendar_computed"
                      ? `${fmtDateShort(cycle.calendar.field_start)} → panen ${fmtDateShort(cycle.calendar.earliest_harvest_date)}${cycle.calendar.latest_harvest_date !== cycle.calendar.earliest_harvest_date ? `–${fmtDateShort(cycle.calendar.latest_harvest_date)}` : ""}`
                      : "kalender belum dihitung"}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="meta">Belum ada urutan.</p>
            )}
          </div>
        ))}
      </section>
    );
  }

  return (
    <section className="panel calendar" aria-labelledby="calendar-title">
      <div className="calendar__head">
        <h3 id="calendar-title">Kalender pada periode yang sama</h3>
        <p className="meta">
          {label} · {fmtWindow(start, end)} · hari panen masih menempati petak
        </p>
      </div>
      <div className="calendar__grid">
        <div className="calendar__axis" aria-hidden="true">
          <span />
          <div className="calendar__months">
            {months.map((month) => (
              <span key={month} style={{ left: pct(month) }}>
                {fmtMonthShort(month)}
                {months.length > 14 ? ` ${month.slice(2, 4)}` : ""}
              </span>
            ))}
          </div>
        </div>
        {result.strategies.map((strategy) => {
          const locked = lockedOf(result, strategy);
          return (
            <div key={strategy.strategy_id} className="calendar__lane">
              <div className="calendar__name">
                <span className="board__label">{STRATEGY_LABEL[strategy.strategy_id]}</span>
                <span className="meta">{strategy.sequence ? sequenceLabel(strategy.sequence) : "Belum ada urutan"}</span>
              </div>
              <div className="calendar__track">
                {months.map((month) => (
                  <span key={month} className="calendar__tick" style={{ left: pct(month) }} aria-hidden="true" />
                ))}
                {strategy.cycles.map((cycle) => {
                  const c = cycle.calendar;
                  if (c.status !== "calendar_computed" || !c.field_start || !c.earliest_release_date || !c.latest_release_date) {
                    return (
                      <span key={cycle.slot_index} className="calendar__pending" style={{ left: pct(cycle.calendar_inputs.sowing_date ?? start), width: "18%" }}>
                        {CROPS[cycle.crop_id].name}: tanggal atau durasi belum lengkap
                      </span>
                    );
                  }
                  const title = `${CROPS[cycle.crop_id].name}: ${fmtDateShort(c.field_start)} sampai panen ${fmtDateShort(c.earliest_harvest_date)}${c.latest_harvest_date !== c.earliest_harvest_date ? `–${fmtDateShort(c.latest_harvest_date)}` : ""}`;
                  return (
                    <Fragment key={cycle.slot_index}>
                      <span className={`calendar__bar calendar__bar--${cycle.crop_id}`} style={{ left: pct(c.field_start), width: width(c.field_start, c.earliest_release_date) }} title={title}>
                        {cycle.slot_index < locked && <Lock aria-label="slot terkunci" size={12} />}
                        <span>
                          {CROPS[cycle.crop_id].name} · {fmtDateShort(c.field_start).replace(/ \d{4}$/, "")}–{fmtDateShort(c.earliest_harvest_date).replace(/ \d{4}$/, "")}
                        </span>
                      </span>
                      {c.latest_release_date !== c.earliest_release_date && (
                        <span className={`calendar__range calendar__range--${cycle.crop_id}`} style={{ left: pct(c.earliest_release_date), width: width(c.earliest_release_date, c.latest_release_date) }} title="Rentang panen" />
                      )}
                    </Fragment>
                  );
                })}
                {strategy.transitions.map((transition) => {
                  const previous = strategy.cycles[transition.previous_slot_index]?.calendar;
                  if (!previous?.latest_release_date || !transition.latest_ready_date) return null;
                  return (
                    <span
                      key={`gap-${transition.previous_slot_index}`}
                      className={`calendar__gap${transition.status === "calendar_conflict" || transition.status === "potential_calendar_conflict" ? " calendar__gap--conflict" : ""}`}
                      style={{ left: pct(previous.latest_release_date), width: width(previous.latest_release_date, transition.latest_ready_date) }}
                      title={`Jeda persiapan ${transition.preparation_gap_days ?? "?"} hari`}
                    />
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
      <p className="lane__legend">
        <span className="legend-swatch legend-swatch--gap" aria-hidden="true" /> Jeda persiapan
        <span className="legend-swatch legend-swatch--conflict" aria-hidden="true" /> Benturan atau kemungkinan benturan
        <Lock aria-hidden="true" size={13} /> Slot terkunci, sama pada alternatif
      </p>
    </section>
  );
}

function SharedClimate({ result }: { result: CompareResponse }) {
  const layer = result.context.layers.climate;
  const summary = layer.summary;
  if (!summary) return null;
  const value = (key: "rainfall_total_mm" | "reference_eto_total_mm" | "rain_minus_reference_eto_total_mm") =>
    summary.mode === "historical_analogue_not_forecast" ? summary.statistics[key].mean : summary[key];
  return (
    <section className="panel shared-climate" aria-labelledby="shared-climate-title">
      <h3 id="shared-climate-title">Konteks iklim bersama</h3>
      <p className="meta">Sama untuk ketiga strategi. Selisih jendela tanam bukan air yang dihemat.</p>
      <dl className="metric-strip metric-strip--compact num">
        <div className="metric">
          <dt>Hujan regional</dt>
          <dd className="metric__value">
            {num(value("rainfall_total_mm"), 2)} <span className="metric__unit">mm</span>
          </dd>
        </div>
        <div className="metric">
          <dt>ETo referensi</dt>
          <dd className="metric__value">
            {num(value("reference_eto_total_mm"), 2)} <span className="metric__unit">mm</span>
          </dd>
        </div>
        <div className="metric">
          <dt>P−ETo · bukan kebutuhan irigasi</dt>
          <dd className="metric__value">
            {signed(value("rain_minus_reference_eto_total_mm"), 2)} <span className="metric__unit">mm</span>
          </dd>
        </div>
      </dl>
      <SourceButton
        item={{
          title: "Konteks iklim periode perbandingan",
          kind: "public_data",
          sourceRefs: layer.source_refs,
          period: result.context.window ? fmtWindow(result.context.window.start_date, result.context.window.end_exclusive) : undefined,
          support: "Titik grid POWER regional; bukan cuaca petak",
          limitations: layer.warnings,
        }}
      />
    </section>
  );
}

function Matrix({ result }: { result: CompareResponse }) {
  const [open, setOpen] = useState<RuleId | null>(null);
  const highlighted = new Set(result.strategies.flatMap((s) => s.highlighted_rule_ids));
  return (
    <section className="panel matrix" aria-labelledby="matrix-title">
      <div className="matrix__head">
        <h3 id="matrix-title">Dua belas pemeriksaan</h3>
        <p className="meta">Status menjelaskan bukti dan kebutuhan informasi. Bukan skor dan bukan peringkat.</p>
      </div>
      <table className="matrix__table">
        <thead>
          <tr>
            <th scope="col">Pemeriksaan</th>
            {result.strategies.map((strategy) => (
              <th key={strategy.strategy_id} scope="col">
                {STRATEGY_LABEL[strategy.strategy_id]}
                <span className="meta">{strategy.sequence ? sequenceLabel(strategy.sequence) : "Belum ada urutan"}</span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {RULE_ORDER.map((rule) => {
            const expanded = open === rule;
            return (
              <Fragment key={rule}>
                <tr className={`matrix__row${expanded ? " is-open" : ""}${highlighted.has(rule) ? " is-focus" : ""}`}>
                  <th scope="row">
                    <button type="button" className="matrix__toggle" aria-expanded={expanded} aria-controls={`rule-${rule}`} onClick={() => setOpen(expanded ? null : rule)}>
                      <ChevronDown aria-hidden="true" size={18} className="matrix__chevron" />
                      <span>
                        <span className="matrix__rule">{RULES[rule].label}</span>
                        {highlighted.has(rule) && <span className="focus-mark">Sesuai fokus Anda</span>}
                        <span className="meta">{RULES[rule].about}</span>
                      </span>
                    </button>
                  </th>
                  {result.strategies.map((strategy) => {
                    const finding = strategy.findings.find((item) => item.rule_id === rule);
                    return <td key={strategy.strategy_id}>{strategy.sequence && finding ? <StatusBadge status={finding.status} compact /> : <span className="meta">—</span>}</td>;
                  })}
                </tr>
                {expanded && (
                  <tr className="matrix__detail" id={`rule-${rule}`}>
                    <td />
                    {result.strategies.map((strategy) => (
                      <td key={strategy.strategy_id}>{strategy.sequence ? <FindingDetail rule={rule} strategy={strategy} /> : <span className="meta">Belum ada urutan.</span>}</td>
                    ))}
                  </tr>
                )}
              </Fragment>
            );
          })}
        </tbody>
      </table>
    </section>
  );
}

function FindingDetail({ rule, strategy }: { rule: RuleId; strategy: Strategy }) {
  const finding = strategy.findings.find((item) => item.rule_id === rule);
  if (!finding) return null;
  return (
    <div className="finding">
      <p>{finding.explanation}</p>
      <RuleEvidence rule={rule} strategy={strategy} />
      {finding.missing_inputs.length > 0 && (
        <div className="finding__block">
          <p className="finding__label">Perlu dilengkapi</p>
          <ul className="plain-list">
            {finding.missing_inputs.map((code) => (
              <li key={code}>{missingLabel(code)}</li>
            ))}
          </ul>
        </div>
      )}
      {finding.next_action && (
        <div className="finding__block">
          <p className="finding__label">Langkah berikutnya</p>
          <p>{finding.next_action}</p>
        </div>
      )}
      <SourceButton
        label="Lihat bukti"
        item={{
          title: `${RULES[rule].label} · ${STRATEGY_LABEL[strategy.strategy_id]}`,
          kind: "app_calculation",
          sourceRefs: finding.source_refs,
          method: `${RULES[rule].about} Metode FieldShift 0.1.0; validasi agronomi lokal belum dilakukan.`,
          assumptions: finding.assumptions,
        }}
      />
    </div>
  );
}

function Aspects({ result }: { result: CompareResponse }) {
  const [open, setOpen] = useState<RuleId | null>(null);
  const highlighted = new Set(result.strategies.flatMap((s) => s.highlighted_rule_ids));
  return (
    <section className="aspects" aria-labelledby="aspects-title">
      <h3 id="aspects-title">Bandingkan per aspek</h3>
      <p className="meta">Setiap aspek menampilkan ketiga strategi. Status bukan skor dan bukan peringkat.</p>
      <ul className="aspects__list">
        {RULE_ORDER.map((rule) => {
          const expanded = open === rule;
          return (
            <li key={rule} className={`panel aspect${highlighted.has(rule) ? " is-focus" : ""}`}>
              <button type="button" className="aspect__toggle" aria-expanded={expanded} aria-controls={`aspect-${rule}`} onClick={() => setOpen(expanded ? null : rule)}>
                <span>
                  <span className="matrix__rule">{RULES[rule].label}</span>
                  {highlighted.has(rule) && <span className="focus-mark">Sesuai fokus Anda</span>}
                </span>
                <ChevronDown aria-hidden="true" size={18} className="matrix__chevron" />
              </button>
              <ul className="aspect__rows">
                {result.strategies.map((strategy) => {
                  const finding = strategy.findings.find((item) => item.rule_id === rule);
                  return (
                    <li key={strategy.strategy_id}>
                      <span>
                        <span className="aspect__strategy">{STRATEGY_LABEL[strategy.strategy_id]}</span>
                        <span className="meta">{strategy.sequence ? sequenceLabel(strategy.sequence) : "Belum ada urutan"}</span>
                      </span>
                      {strategy.sequence && finding ? <StatusBadge status={finding.status} compact /> : <span className="meta">—</span>}
                    </li>
                  );
                })}
              </ul>
              {expanded && (
                <div id={`aspect-${rule}`} className="aspect__detail">
                  {result.strategies
                    .filter((strategy) => strategy.sequence)
                    .map((strategy) => (
                      <div key={strategy.strategy_id} className="aspect__strategy-detail">
                        <p className="board__label">{STRATEGY_LABEL[strategy.strategy_id]}</p>
                        <FindingDetail rule={rule} strategy={strategy} />
                      </div>
                    ))}
                </div>
              )}
            </li>
          );
        })}
      </ul>
    </section>
  );
}
