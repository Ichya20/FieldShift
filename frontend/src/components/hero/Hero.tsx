import { ArrowRight } from "lucide-react";
import { useMemo, useState } from "react";
import { HERO_SCENARIOS, demoCycles } from "../../lib/demo";
import { fmtDate } from "../../lib/format";
import { CROPS, sequenceLabel } from "../../lib/labels";
import { Diorama } from "./Diorama";
import { SeasonLane } from "./SeasonLane";

export function Hero() {
  const [scenarioId, setScenarioId] = useState("padi-jagung");
  const [phase, setPhase] = useState(0);
  const scenario = HERO_SCENARIOS.find((item) => item.id === scenarioId) ?? HERO_SCENARIOS[0];
  const cycles = useMemo(() => demoCycles(scenario.sequence), [scenario]);
  const crop = scenario.sequence[phase];
  const cycle = cycles[phase];
  const label = `Ilustrasi satu petak sawah dengan penampang tanah 1 meter. Musim ${phase + 1}: ${CROPS[crop].name}, ${fmtDate(cycle.start)} sampai ${fmtDate(cycle.harvest)}, kalender asumsi demo.`;

  return (
    <section className="hero" id="top" aria-labelledby="hero-title">
      <div className="container hero__grid">
        <div className="hero__text">
          <h1 id="hero-title">Rotasi tanaman, lebih terarah.</h1>
          <p className="hero__lead">
            Bandingkan pilihan rotasi melalui konteks iklim, tanah, dan vegetasi untuk area contoh Yogyakarta–Klaten.
          </p>
          <a className="button button--primary button--large" href="#kondisi">
            Mulai eksplorasi
            <ArrowRight aria-hidden="true" size={18} />
          </a>
        </div>

        <figure className="hero__visual">
          <Diorama crop={crop} token={`${phase}:${crop}`} label={label} />
          <figcaption className="hero__controls">
            <fieldset className="segmented" aria-describedby="hero-caption">
              <legend className="segmented__legend">Skenario</legend>
              <div className="segmented__options">
                {HERO_SCENARIOS.map((item) => (
                  <label key={item.id} className="segmented__option">
                    <input
                      type="radio"
                      name="hero-scenario"
                      value={item.id}
                      checked={item.id === scenarioId}
                      onChange={() => setScenarioId(item.id)}
                    />
                    <span>
                      <span className="crop-dots" aria-hidden="true">
                        {item.sequence.map((id, index) => (
                          <i key={index} className={`crop-dot crop-dot--${id}`} />
                        ))}
                      </span>
                      {sequenceLabel(item.sequence)}
                    </span>
                  </label>
                ))}
              </div>
            </fieldset>
            <SeasonLane cycles={cycles} phase={phase} onPhase={setPhase} />
            <p className="hero__caption" id="hero-caption">
              <strong>Ilustrasi skenario.</strong> Petak yang sama berganti tanaman antar musim, mengikuti kalender asumsi demo
              2025. Bukan citra lahan, batas petak, atau prediksi pertumbuhan.
            </p>
          </figcaption>
        </figure>
      </div>
    </section>
  );
}
