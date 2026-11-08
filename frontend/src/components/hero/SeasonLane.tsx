import { DEMO, type DemoCycle } from "../../lib/demo";
import { addDays, monthStarts, position } from "../../lib/dates";
import { fmtDayMonth, fmtMonthShort } from "../../lib/format";
import { CROPS } from "../../lib/labels";

interface Props {
  cycles: DemoCycle[];
  phase: number;
  onPhase: (phase: number) => void;
}

const START = DEMO.horizonStart;
const END = DEMO.horizonEndExclusive;
const pct = (iso: string) => `${(position(iso, START, END) * 100).toFixed(3)}%`;
const width = (from: string, to: string) => `${((position(to, START, END) - position(from, START, END)) * 100).toFixed(3)}%`;

/** The demo calendar as a lane; each crop bar is also the season control for the diorama. */
export function SeasonLane({ cycles, phase, onPhase }: Props) {
  const months = monthStarts(START, END);
  const first = cycles[0];
  const ready = addDays(first.release, DEMO.prepGapDays);
  const last = cycles[cycles.length - 1];
  return (
    <div className="lane" role="group" aria-label="Kalender asumsi demo 2025">
      <div className="lane__track" role="radiogroup" aria-label="Musim pada diorama">
        <span
          className="lane__gap"
          style={{ left: pct(first.release), width: width(first.release, ready) }}
          title={`Jeda persiapan ${DEMO.prepGapDays} hari (asumsi)`}
        />
        <span className="lane__idle" style={{ left: pct(ready), width: width(ready, cycles[1]?.start ?? ready) }} />
        <span className="lane__idle lane__idle--open" style={{ left: pct(last.release), width: width(last.release, END) }} />
        {cycles.map((cycle, index) => (
          <button
            key={index}
            type="button"
            role="radio"
            aria-checked={phase === index}
            className={`lane__bar lane__bar--${cycle.crop}${phase === index ? " is-active" : ""}`}
            style={{ left: pct(cycle.start), width: width(cycle.start, cycle.release) }}
            onClick={() => onPhase(index)}
            onKeyDown={(event) => {
              if (event.key === "ArrowRight" || event.key === "ArrowLeft") {
                event.preventDefault();
                onPhase(index === 0 ? 1 : 0);
                const sibling = event.currentTarget.parentElement?.querySelectorAll<HTMLButtonElement>(".lane__bar")[index === 0 ? 1 : 0];
                sibling?.focus();
              }
            }}
            tabIndex={phase === index ? 0 : -1}
          >
            <span className="lane__bar-label">
              <span className="lane__season">Musim {index + 1} · </span>
              {CROPS[cycle.crop].name}
            </span>
            <span className="lane__bar-dates">
              {fmtDayMonth(cycle.start)}–{fmtDayMonth(cycle.harvest)} · {cycle.days} hari
            </span>
          </button>
        ))}
      </div>
      <div className="lane__axis" aria-hidden="true">
        {months.map((month) => (
          <span key={month} style={{ left: pct(month) }}>
            {fmtMonthShort(month)}
          </span>
        ))}
      </div>
      <p className="lane__legend">
        <span className="legend-swatch legend-swatch--gap" aria-hidden="true" /> Jeda persiapan {DEMO.prepGapDays} hari
        <span className="legend-swatch legend-swatch--open" aria-hidden="true" /> Belum ditentukan
      </p>
    </div>
  );
}
