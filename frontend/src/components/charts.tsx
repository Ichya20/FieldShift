import { useId, useState } from "react";
import { monthStarts, parseIso, position } from "../lib/dates";
import { fmtDateShort, fmtMonthLong, fmtMonthShort, num } from "../lib/format";
import type { VegetationSeries } from "../lib/types";

export function niceMax(value: number) {
  if (value <= 0) return 1;
  const exponent = Math.pow(10, Math.floor(Math.log10(value)));
  const fraction = value / exponent;
  const nice = fraction <= 1 ? 1 : fraction <= 2 ? 2 : fraction <= 2.5 ? 2.5 : fraction <= 5 ? 5 : 10;
  return nice * exponent;
}

export interface MonthValue {
  month: string;
  value: number | null;
  low?: number | null;
  high?: number | null;
  valid: number;
  expected: number;
}

interface BarsProps {
  title: string;
  unit: string;
  values: MonthValue[];
  tone: "rain" | "eto";
  digits?: number;
  rangeLabel?: string;
}

/** Monthly totals as bars. Incomplete months show a dash, never a bar. */
export function MonthlyBars({ title, unit, values, tone, digits = 1, rangeLabel }: BarsProps) {
  const [table, setTable] = useState(false);
  const id = useId();
  const width = 560;
  const height = 210;
  const pad = { left: 44, right: 8, top: 14, bottom: 26 };
  const plotW = width - pad.left - pad.right;
  const plotH = height - pad.top - pad.bottom;
  const max = niceMax(Math.max(1, ...values.map((m) => Math.max(m.value ?? 0, m.high ?? 0))));
  const ticks = [0, max / 2, max];
  const slot = plotW / Math.max(1, values.length);
  const barW = Math.min(30, slot * 0.62);
  const y = (v: number) => pad.top + plotH - (v / max) * plotH;
  const missing = values.some((m) => m.value === null);
  const showRange = values.some((m) => m.low !== undefined && m.low !== null);

  return (
    <figure className="chart">
      <figcaption className="chart__head">
        <h4 id={`${id}-title`}>{title}</h4>
        <button type="button" className="text-button" aria-expanded={table} onClick={() => setTable((v) => !v)}>
          {table ? "Tampilkan grafik" : "Tampilkan tabel"}
        </button>
      </figcaption>
      {table ? (
        <div className="table-scroll">
          <table className="data-table">
            <caption className="visually-hidden">{title}</caption>
            <thead>
              <tr>
                <th scope="col">Bulan</th>
                <th scope="col" className="num-col">
                  {showRange ? `Rerata (${unit})` : `Total (${unit})`}
                </th>
                {showRange && <th scope="col" className="num-col">P10–P90</th>}
                <th scope="col" className="num-col">{showRange ? "Tahun analog" : "Hari valid"}</th>
              </tr>
            </thead>
            <tbody>
              {values.map((m) => (
                <tr key={m.month}>
                  <th scope="row">{fmtMonthLong(m.month)}</th>
                  <td className="num-col">{m.value === null ? "Belum lengkap" : num(m.value, digits)}</td>
                  {showRange && <td className="num-col">{m.low === null || m.low === undefined ? "—" : `${num(m.low, digits)}–${num(m.high ?? null, digits)}`}</td>}
                  <td className="num-col">
                    {m.valid}/{m.expected}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <svg viewBox={`0 0 ${width} ${height}`} className="chart__svg" role="img" aria-labelledby={`${id}-title`}>
          {ticks.map((tick) => (
            <g key={tick}>
              <line x1={pad.left} x2={width - pad.right} y1={y(tick)} y2={y(tick)} className="chart__grid" />
              <text x={pad.left - 8} y={y(tick)} className="chart__tick" textAnchor="end" dominantBaseline="middle">
                {num(tick, 0)}
              </text>
            </g>
          ))}
          {values.map((m, i) => {
            const cx = pad.left + slot * i + slot / 2;
            return (
              <g key={m.month}>
                {m.value === null ? (
                  <text x={cx} y={y(0) - 8} className="chart__missing" textAnchor="middle">
                    –
                  </text>
                ) : (
                  <rect x={cx - barW / 2} width={barW} y={y(m.value)} height={Math.max(0.5, y(0) - y(m.value))} rx={2} className={`chart__bar chart__bar--${tone}`}>
                    <title>
                      {fmtMonthLong(m.month)}: {num(m.value, digits)} {unit} ({m.valid}/{m.expected} {showRange ? "tahun analog" : "hari valid"})
                    </title>
                  </rect>
                )}
                {m.low !== undefined && m.low !== null && m.high !== undefined && m.high !== null && (
                  <g className="chart__range">
                    <line x1={cx} x2={cx} y1={y(m.low)} y2={y(m.high)} />
                    <line x1={cx - 5} x2={cx + 5} y1={y(m.low)} y2={y(m.low)} />
                    <line x1={cx - 5} x2={cx + 5} y1={y(m.high)} y2={y(m.high)} />
                  </g>
                )}
                <text x={cx} y={height - 8} className="chart__tick" textAnchor="middle">
                  {fmtMonthShort(m.month)}
                </text>
              </g>
            );
          })}
          <line x1={pad.left} x2={width - pad.right} y1={y(0)} y2={y(0)} className="chart__axis" />
        </svg>
      )}
      {(missing || rangeLabel) && (
        <p className="chart__note">
          {missing && "– bulan dengan hari valid belum lengkap; total tidak ditampilkan. "}
          {rangeLabel}
        </p>
      )}
    </figure>
  );
}

interface VegetationProps {
  series: VegetationSeries[];
  start: string;
  endExclusive: string;
  index: "ndvi" | "evi";
}

/** Terra and Aqua on one shared time axis, strict-good observations only, gaps kept visible. */
export function VegetationPanels({ series, start, endExclusive, index }: VegetationProps) {
  const patternId = useId();
  const width = 560;
  const rowH = 112;
  const pad = { left: 36, right: 8, top: 10, bottom: 24 };
  const plotW = width - pad.left - pad.right;
  const months = monthStarts(start, endExclusive);
  const x = (iso: string) => pad.left + position(iso, start, endExclusive) * plotW;
  const sorted = [...series].sort((a, b) => (a.platform === "Terra" ? -1 : 1) - (b.platform === "Terra" ? -1 : 1));
  const multiYear = parseIso(endExclusive).getTime() - parseIso(start).getTime() > 400 * 86400000;

  return (
    <div className="veg">
      {sorted.map((s) => {
        const good = s.observations.filter((o) => o.quality_status === "good_strict" && o[index] !== null);
        const gaps = s.monthly.filter((m) => m.coverage_status !== "has_good_observations");
        const y = (v: number) => pad.top + (1 - v) * (rowH - pad.top - pad.bottom);
        return (
          <figure key={s.product} className="veg__row">
            <figcaption className="veg__head">
              <span className="veg__name">
                {s.platform} · {s.product}
              </span>
              <span className="meta num">
                {s.summary.n_good_strict} lolos kualitas · {s.summary.n_marginal_review} marginal · {s.summary.n_excluded} dikecualikan
              </span>
            </figcaption>
            <svg
              viewBox={`0 0 ${width} ${rowH}`}
              className="chart__svg"
              role="img"
              aria-label={`${index.toUpperCase()} ${s.platform}: ${good.length} observasi lolos kualitas, ${gaps.length} bulan tanpa observasi yang lolos kualitas.`}
            >
              <defs>
                <pattern id={`${patternId}-${s.product}`} width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
                  <line x1="0" y1="0" x2="0" y2="6" className="veg__hatch" />
                </pattern>
              </defs>
              {gaps.map((m) => {
                const monthStart = `${m.month}-01`;
                const next = months[months.indexOf(monthStart) + 1] ?? endExclusive;
                return (
                  <rect
                    key={m.month}
                    x={x(monthStart < start ? start : monthStart)}
                    width={Math.max(1, x(next) - x(monthStart < start ? start : monthStart))}
                    y={pad.top}
                    height={rowH - pad.top - pad.bottom}
                    fill={`url(#${patternId}-${s.product})`}
                    className="veg__gap"
                  />
                );
              })}
              {[0, 0.5, 1].map((tick) => (
                <g key={tick}>
                  <line x1={pad.left} x2={width - pad.right} y1={y(tick)} y2={y(tick)} className="chart__grid" />
                  <text x={pad.left - 6} y={y(tick)} className="chart__tick" textAnchor="end" dominantBaseline="middle">
                    {num(tick, 1)}
                  </text>
                </g>
              ))}
              {good.map((o) => (
                <circle key={o.selected_observation_date} cx={x(o.selected_observation_date)} cy={y(o[index] as number)} r={4.2} className={`veg__dot veg__dot--${s.platform.toLowerCase()}`}>
                  <title>
                    {fmtDateShort(o.selected_observation_date)}: {index.toUpperCase()} {num(o[index], 2)} (lolos kualitas)
                  </title>
                </circle>
              ))}
              {months
                .filter((_, i) => !multiYear || i % 6 === 0)
                .map((month) => (
                  <text key={month} x={x(month) + 2} y={rowH - 7} className="chart__tick">
                    {multiYear ? `${fmtMonthShort(month)} ${month.slice(2, 4)}` : fmtMonthShort(month)}
                  </text>
                ))}
            </svg>
          </figure>
        );
      })}
    </div>
  );
}

interface PhProps {
  value: number | null;
  q05: number | null;
  q95: number | null;
  optima: { label: string; min: number; max: number }[];
}

export function PhRange({ value, q05, q95, optima }: PhProps) {
  const min = 3.5;
  const max = 9;
  const pct = (v: number) => `${(((v - min) / (max - min)) * 100).toFixed(2)}%`;
  const span = (a: number, b: number) => `${(((b - a) / (max - min)) * 100).toFixed(2)}%`;
  const ticks = [4, 5, 6, 7, 8, 9];
  return (
    <div className="ph" role="img" aria-label={`Prediksi pH ${num(value, 1)}, rentang kuantil 5 sampai 95: ${num(q05, 1)} sampai ${num(q95, 1)}.`}>
      <div className="ph__row">
        <span className="ph__label">Prediksi 0–5 cm</span>
        <div className="ph__track">
          {q05 !== null && q95 !== null && <span className="ph__interval" style={{ left: pct(q05), width: span(q05, q95) }} />}
          {value !== null && <span className="ph__mean" style={{ left: pct(value) }} />}
        </div>
      </div>
      {optima.map((o) => (
        <div className="ph__row" key={o.label}>
          <span className="ph__label">{o.label}</span>
          <div className="ph__track ph__track--thin">
            <span className="ph__optimum" style={{ left: pct(o.min), width: span(o.min, o.max) }} />
          </div>
        </div>
      ))}
      <div className="ph__row" aria-hidden="true">
        <span className="ph__label" />
        <div className="ph__axis">
          {ticks.map((tick) => (
            <span key={tick} style={{ left: pct(tick) }}>
              {tick}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
