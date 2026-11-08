import { ArrowDown, ArrowUp, Lock, LockOpen, Plus, Trash } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { addDays } from "../../lib/dates";
import { DEMO } from "../../lib/demo";
import { fmtDateShort, fmtWindow } from "../../lib/format";
import { CROPS, CROP_IDS, METHOD_LABEL, PRIORITIES, TIME_MODES, sequenceLabel, timeModeLabel } from "../../lib/labels";
import {
  ADVANCED,
  hasEntries,
  newSlot,
  type DurationForm,
  type FormIssue,
  type Place,
  type ScenarioForm,
  type SlotForm,
  type Step,
} from "../../lib/scenario";
import type { CropId, CropReference, Priority, TimeMode } from "../../lib/types";
import { PlacePicker, placeLabel } from "../location/PlacePicker";
import { ChoiceGroup, Field } from "./fields";

interface Props {
  form: ScenarioForm;
  update: (updater: (form: ScenarioForm) => ScenarioForm) => void;
  place: Place;
  onPlace: (place: Place) => void;
  crops: CropReference[];
  issues: FormIssue[];
  showErrors: boolean;
  busy: boolean;
  onSubmit: () => void;
  onApplyDemo: () => void;
  stepRequest: { step: Step; field?: string; nonce: number } | null;
  demoAsk: number;
}

const STEPS: { id: Step; label: string }[] = [
  { id: 1, label: "Lokasi & periode" },
  { id: 2, label: "Rotasi & kalender" },
  { id: 3, label: "Kondisi & prioritas" },
];

export function ScenarioSection({ form, update, place, onPlace, crops, issues, showErrors, busy, onSubmit, onApplyDemo, stepRequest, demoAsk }: Props) {
  const [step, setStep] = useState<Step>(1);
  const [focusTarget, setFocusTarget] = useState<string | null>(null);
  const dialog = useRef<HTMLDialogElement>(null);
  const formTop = useRef<HTMLDivElement>(null);
  const errorFor = (field: string) => (showErrors ? issues.find((issue) => issue.field === field)?.message : undefined);

  useEffect(() => {
    if (demoAsk > 0 && dialog.current && !dialog.current.open) dialog.current.showModal();
  }, [demoAsk]);

  useEffect(() => {
    if (!stepRequest) return;
    setStep(stepRequest.step);
    setFocusTarget(stepRequest.field ?? null);
  }, [stepRequest]);

  useEffect(() => {
    if (!focusTarget) return;
    const element = document.getElementById(focusTarget);
    const target = element?.matches("input,select,textarea,button") ? element : element?.querySelector<HTMLElement>("input,select,textarea,button");
    target?.focus();
    element?.scrollIntoView({ block: "center", behavior: "smooth" });
    setFocusTarget(null);
  }, [focusTarget, step]);

  const goTo = (next: Step) => {
    setStep(next);
    formTop.current?.scrollIntoView({ block: "start", behavior: "smooth" });
  };

  const goToIssue = (issue: FormIssue) => {
    setStep(issue.step);
    setFocusTarget(issue.field);
  };

  return (
    <section id="skenario" className="section section--scenario" aria-labelledby="skenario-title">
      <div className="container">
        <header className="section-head">
          <h2 id="skenario-title">Susun skenario</h2>
          <p>Isi yang Anda ketahui. Kolom yang dibiarkan kosong tetap tercatat “belum tahu”, bukan nol, dan pemeriksaan terkait akan menunggu informasi.</p>
        </header>

        <div className="scenario-grid">
          <div className="scenario-form" ref={formTop}>
            <nav className="stepper" aria-label="Langkah formulir">
              <ol>
                {STEPS.map((item) => {
                  const count = showErrors ? issues.filter((issue) => issue.step === item.id).length : 0;
                  return (
                    <li key={item.id}>
                      <button type="button" aria-current={step === item.id ? "step" : undefined} onClick={() => setStep(item.id)}>
                        <span className="stepper__index">{item.id}</span>
                        <span className="stepper__label">{item.label}</span>
                        {count > 0 && <span className="stepper__issues">{count} perlu dicek</span>}
                      </button>
                    </li>
                  );
                })}
              </ol>
            </nav>

            <div className="panel form-panel">
              {step === 1 && <StepLocation form={form} update={update} place={place} onPlace={onPlace} errorFor={errorFor} />}
              {step === 2 && <StepRotation form={form} update={update} crops={crops} errorFor={errorFor} />}
              {step === 3 && <StepConditions form={form} update={update} />}

              <div className="form-nav">
                {step > 1 ? (
                  <button type="button" className="button button--quiet" onClick={() => goTo((step - 1) as Step)}>
                    Kembali
                  </button>
                ) : (
                  <span />
                )}
                {step < 3 && (
                  <button type="button" className="button button--secondary" onClick={() => goTo((step + 1) as Step)}>
                    Lanjut ke {STEPS[step].label}
                  </button>
                )}
              </div>
            </div>
          </div>

          <aside className="scenario-summary" aria-label="Ringkasan isian">
            <div className="panel summary-panel">
              <div className="summary-panel__head">
                <h3>Ringkasan isian</h3>
                <button type="button" className="text-button" onClick={() => dialog.current?.showModal()}>
                  Gunakan contoh 2025
                </button>
              </div>
              <Summary form={form} place={place} />
              {showErrors && issues.length > 0 && (
                <div className="error-summary" role="alert" tabIndex={-1}>
                  <p>
                    <strong>Periksa {issues.length} isian berikut sebelum membandingkan.</strong>
                  </p>
                  <ul>
                    {issues.map((issue) => (
                      <li key={`${issue.field}-${issue.message}`}>
                        <button type="button" className="text-button" onClick={() => goToIssue(issue)}>
                          {issue.message}
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              <p className="meta">Input parsial boleh dilanjutkan. Beberapa pemeriksaan akan menunggu informasi tambahan.</p>
              <button type="button" className="button button--primary button--large summary-panel__submit" onClick={onSubmit} disabled={busy} aria-busy={busy}>
                {busy ? "Memeriksa skenario…" : "Bandingkan strategi"}
              </button>
              <p className="meta summary-panel__session">Isian digunakan selama sesi ini.</p>
            </div>
          </aside>
        </div>
      </div>

      <dialog ref={dialog} className="confirm" aria-labelledby="demo-title">
        <form method="dialog" className="confirm__body">
          <h2 id="demo-title">Isi asumsi demo 2025?</h2>
          <p>Contoh ini memakai kalender sintetis di atas data lingkungan historis nyata. Ini bukan riwayat petani.</p>
          <ul className="plain-list">
            {DEMO.assumptions.map((line) => (
              <li key={line}>{line}</li>
            ))}
            <li>{DEMO.sharedCalendarNote}</li>
            <li>Lokasi tidak diubah; perbandingan memakai lokasi yang sedang dipilih.</li>
          </ul>
          {hasEntries(form) && <p className="notice notice--review">Isian yang sudah ada akan diganti oleh asumsi demo.</p>}
          <div className="confirm__actions">
            <button value="cancel" className="button button--quiet">
              Batal
            </button>
            <button
              value="apply"
              className="button button--primary"
              onClick={() => {
                onApplyDemo();
                setStep(1);
              }}
            >
              Terapkan asumsi demo
            </button>
          </div>
        </form>
      </dialog>
    </section>
  );
}

// ---- Step 1 ---------------------------------------------------------------------

interface StepProps {
  form: ScenarioForm;
  update: Props["update"];
  errorFor?: (field: string) => string | undefined;
}

function StepLocation({ form, update, place, onPlace, errorFor }: StepProps & { place: Place; onPlace: (place: Place) => void }) {
  const error = errorFor ?? (() => undefined);
  return (
    <div className="form-step">
      <h3 className="form-step__title">Lokasi &amp; periode</h3>
      <PlacePicker name="place" place={place} onChange={onPlace} compact />
      {error("place-custom") && <p className="field__error">{error("place-custom")}</p>}

      <ChoiceGroup
        id="input-kind"
        name="input-kind"
        legend="Jenis isian"
        value={form.inputKind}
        error={error("input-kind")}
        options={[
          { value: "scenario_assumption", label: "Skenario asumsi", note: "Tanggal dan kondisi dibuat untuk eksplorasi" },
          { value: "user_reported", label: "Isian pengguna", note: "Dilaporkan petani atau penyuluh, belum diverifikasi" },
        ]}
        onChange={(value) => update((f) => ({ ...f, inputKind: value }))}
      />

      <Field
        id="assumptions"
        label={form.inputKind === "scenario_assumption" ? "Catatan asumsi (wajib)" : "Catatan asumsi"}
        hint="Satu asumsi per baris, misalnya “Tanggal tanam memakai kebiasaan musim hujan 2025”."
        error={error("assumptions")}
      >
        <textarea
          id="assumptions"
          className="input textarea"
          rows={3}
          value={form.assumptions}
          aria-invalid={Boolean(error("assumptions"))}
          onChange={(event) => update((f) => ({ ...f, assumptions: event.target.value }))}
        />
      </Field>

      <div className="field-pair">
        <Field id="period-start" label="Mulai periode" error={error("period-start")}>
          <input
            id="period-start"
            type="date"
            className="input"
            value={form.start}
            min="1900-01-01"
            max="2099-12-31"
            aria-invalid={Boolean(error("period-start"))}
            onChange={(event) => update((f) => ({ ...f, start: event.target.value }))}
          />
        </Field>
        <Field id="period-end" label="Sampai tanggal (termasuk)" error={error("period-end")}>
          <input
            id="period-end"
            type="date"
            className="input"
            value={form.endInclusive}
            min="1900-01-01"
            max="2099-12-31"
            aria-invalid={Boolean(error("period-end"))}
            onChange={(event) => update((f) => ({ ...f, endInclusive: event.target.value }))}
          />
        </Field>
      </div>

      <Field id="form-time-mode" label="Mode waktu" hint={TIME_MODES.find((mode) => mode.id === form.timeMode)?.help ?? "Belum dipilih: pemeriksaan iklim akan menunggu mode waktu."}>
        <select
          id="form-time-mode"
          className="input select"
          value={form.timeMode}
          onChange={(event) => update((f) => ({ ...f, timeMode: event.target.value as TimeMode | "" }))}
        >
          <option value="">Belum dipilih</option>
          {TIME_MODES.map((mode) => (
            <option key={mode.id} value={mode.id}>
              {mode.label}
            </option>
          ))}
        </select>
      </Field>
    </div>
  );
}

// ---- Step 2 ---------------------------------------------------------------------

function StepRotation({ form, update, crops, errorFor }: StepProps & { crops: CropReference[] }) {
  const error = errorFor ?? (() => undefined);
  const setSlot = (index: number, patch: Partial<SlotForm>) =>
    update((f) => ({ ...f, slots: f.slots.map((slot, i) => (i === index ? { ...slot, ...patch } : slot)) }));
  const move = (index: number, delta: number) =>
    update((f) => {
      const slots = [...f.slots];
      const target = index + delta;
      if (target < 0 || target >= slots.length) return f;
      [slots[index], slots[target]] = [slots[target], slots[index]];
      return { ...f, slots };
    });
  const remove = (index: number) =>
    update((f) => {
      const slots = f.slots.filter((_, i) => i !== index);
      return { ...f, slots, lockedPrefix: Math.min(f.lockedPrefix, slots.length) };
    });
  const setDuration = (crop: CropId, patch: Partial<DurationForm>) =>
    update((f) => ({ ...f, durations: { ...f.durations, [crop]: { ...f.durations[crop], ...patch } } }));

  return (
    <div className="form-step">
      <h3 className="form-step__title">Rotasi &amp; kalender</h3>
      <div className="form-block">
        <h4>Urutan rotasi berjalan</h4>
        <p className="field__hint">Satu sampai tiga slot, berurutan dalam periode. Slot terkunci dipertahankan sama pada kedua alternatif.</p>
        <ol className="slot-list">
          {form.slots.map((slot, index) => (
            <li key={slot.key} className="slot">
              <div className="slot__head">
                <span className="slot__title">Slot {index + 1}</span>
                <label className="lock-toggle">
                  <input
                    type="checkbox"
                    checked={index < form.lockedPrefix}
                    onChange={(event) => update((f) => ({ ...f, lockedPrefix: event.target.checked ? index + 1 : index }))}
                  />
                  {index < form.lockedPrefix ? <Lock aria-hidden="true" size={15} /> : <LockOpen aria-hidden="true" size={15} />}
                  <span>Kunci pada alternatif</span>
                </label>
                <div className="slot__tools">
                  <button type="button" className="icon-button" onClick={() => move(index, -1)} disabled={index === 0} aria-label={`Naikkan slot ${index + 1}`}>
                    <ArrowUp aria-hidden="true" size={17} />
                  </button>
                  <button type="button" className="icon-button" onClick={() => move(index, 1)} disabled={index === form.slots.length - 1} aria-label={`Turunkan slot ${index + 1}`}>
                    <ArrowDown aria-hidden="true" size={17} />
                  </button>
                  <button type="button" className="icon-button" onClick={() => remove(index)} disabled={form.slots.length === 1} aria-label={`Hapus slot ${index + 1}`}>
                    <Trash aria-hidden="true" size={17} />
                  </button>
                </div>
              </div>
              <div className="slot__grid">
                <Field id={`slot-${index}-crop`} label="Tanaman" error={error(`slot-${index}-crop`)}>
                  <select
                    id={`slot-${index}-crop`}
                    className="input select"
                    value={slot.cropId}
                    onChange={(event) => setSlot(index, { cropId: event.target.value as CropId | "" })}
                  >
                    <option value="">Pilih tanaman</option>
                    {CROP_IDS.map((crop) => (
                      <option key={crop} value={crop}>
                        {CROPS[crop].name}
                      </option>
                    ))}
                  </select>
                </Field>
                <Field id={`slot-${index}-method`} label="Metode tanam" error={error(`slot-${index}-method`)}>
                  <select
                    id={`slot-${index}-method`}
                    className="input select"
                    value={slot.method}
                    onChange={(event) =>
                      setSlot(index, {
                        method: event.target.value as SlotForm["method"],
                        ...(event.target.value !== "transplanted" ? { transplantingDate: "", nursery: "" } : {}),
                      })
                    }
                  >
                    <option value="">Belum tahu</option>
                    <option value="direct_seeded">{METHOD_LABEL.direct_seeded}</option>
                    <option value="transplanted">{METHOD_LABEL.transplanted}</option>
                  </select>
                </Field>
                <Field id={`slot-${index}-sowing`} label="Tanggal semai" error={error(`slot-${index}-sowing`)}>
                  <input
                    id={`slot-${index}-sowing`}
                    type="date"
                    className="input"
                    value={slot.sowingDate}
                    onChange={(event) => setSlot(index, { sowingDate: event.target.value })}
                  />
                </Field>
                {slot.method === "transplanted" && (
                  <Field id={`slot-${index}-transplanting`} label="Tanggal pindah tanam" error={error(`slot-${index}-transplanting`)}>
                    <input
                      id={`slot-${index}-transplanting`}
                      type="date"
                      className="input"
                      value={slot.transplantingDate}
                      onChange={(event) => setSlot(index, { transplantingDate: event.target.value })}
                    />
                  </Field>
                )}
                <Field id={`slot-${index}-harvest`} label="Tanggal panen yang diketahui" hint="Opsional. Hari panen masih menempati petak." error={error(`slot-${index}-harvest`)}>
                  <input
                    id={`slot-${index}-harvest`}
                    type="date"
                    className="input"
                    value={slot.harvestDate}
                    onChange={(event) => setSlot(index, { harvestDate: event.target.value })}
                  />
                </Field>
                <Field id={`slot-${index}-status`} label="Status tanggal" error={error(`slot-${index}-status`)}>
                  <select
                    id={`slot-${index}-status`}
                    className="input select"
                    value={slot.dateStatus}
                    onChange={(event) => setSlot(index, { dateStatus: event.target.value as SlotForm["dateStatus"] })}
                  >
                    <option value="">Belum tahu</option>
                    <option value="observed">Teramati</option>
                    <option value="planned">Rencana</option>
                    <option value="scenario_assumption">Asumsi skenario</option>
                  </select>
                </Field>
                {slot.method === "transplanted" && (
                  <Field id={`slot-${index}-nursery`} label="Persemaian">
                    <select
                      id={`slot-${index}-nursery`}
                      className="input select"
                      value={slot.nursery}
                      onChange={(event) => setSlot(index, { nursery: event.target.value as SlotForm["nursery"] })}
                    >
                      <option value="">Belum tahu</option>
                      <option value="separate">Terpisah dari petak utama</option>
                      <option value="main_field">Di petak utama</option>
                    </select>
                  </Field>
                )}
                {slot.cropId === "padi" && (
                  <>
                    <Field id={`slot-${index}-ecosystem`} label="Ekosistem padi">
                      <select
                        id={`slot-${index}-ecosystem`}
                        className="input select"
                        value={slot.riceEcosystem}
                        onChange={(event) => setSlot(index, { riceEcosystem: event.target.value as SlotForm["riceEcosystem"] })}
                      >
                        <option value="">Belum tahu</option>
                        <option value="irrigated_lowland">Sawah irigasi</option>
                        <option value="rainfed_lowland">Sawah tadah hujan</option>
                        <option value="rainfed_upland">Lahan kering tadah hujan</option>
                        <option value="flood_prone">Rawan banjir</option>
                      </select>
                    </Field>
                    <Field id={`slot-${index}-regime`} label="Rezim air padi" hint="Metode tanam tidak menentukan genangan.">
                      <select
                        id={`slot-${index}-regime`}
                        className="input select"
                        value={slot.riceWaterRegime}
                        onChange={(event) => setSlot(index, { riceWaterRegime: event.target.value as SlotForm["riceWaterRegime"] })}
                      >
                        <option value="">Belum tahu</option>
                        <option value="flooded_paddy">Digenangi</option>
                        <option value="intermittently_flooded_paddy">Genangan berselang</option>
                        <option value="nonflooded_aerobic">Tidak digenangi (aerob)</option>
                        <option value="mixed_or_variable">Campuran atau berubah-ubah</option>
                        <option value="other_documented">Lainnya, terdokumentasi</option>
                      </select>
                    </Field>
                  </>
                )}
              </div>
            </li>
          ))}
        </ol>
        {form.slots.length < 3 && (
          <button type="button" className="button button--quiet" onClick={() => update((f) => ({ ...f, slots: [...f.slots, newSlot()] }))}>
            <Plus aria-hidden="true" size={17} /> Tambah slot tanaman
          </button>
        )}
        <label className="check">
          <input type="checkbox" checked={form.continuationConfirmed} onChange={(event) => update((f) => ({ ...f, continuationConfirmed: event.target.checked }))} />
          <span>Saya menggunakan urutan ini sebagai kelanjutan rotasi pada periode yang dipilih.</span>
        </label>
      </div>

      <div className="form-block">
        <h4>Tanaman untuk alternatif</h4>
        <p className="field__hint">Generator hanya memakai tanaman yang boleh dicoba. Tidak ada pilihan bawaan.</p>
        <div className="policy-table" role="group" aria-label="Tanaman untuk alternatif">
          {CROP_IDS.map((crop) => (
            <ChoiceGroup
              key={crop}
              name={`policy-${crop}`}
              legend={CROPS[crop].name}
              value={form.cropPolicy[crop]}
              options={[
                { value: "allowed", label: "Boleh dicoba" },
                { value: "excluded", label: "Hindari" },
                { value: "", label: "Belum ditentukan" },
              ]}
              onChange={(value) => update((f) => ({ ...f, cropPolicy: { ...f.cropPolicy, [crop]: value } }))}
            />
          ))}
        </div>
      </div>

      <div className="form-block" id="durations">
        <h4>Durasi tanaman</h4>
        <p className="field__hint">Rentang hari sejak semai atau pindah tanam (hari ke-0). Sebutkan sumbernya; referensi varietas hanya dipakai bila Anda memilihnya.</p>
        <div className="duration-list">
          {CROP_IDS.map((crop) => {
            const d = form.durations[crop];
            const reference = crops.find((item) => item.crop_id === crop)?.local_variety_reference;
            const manual = (patch: Partial<DurationForm>) =>
              setDuration(crop, d.referenceId ? { ...patch, referenceId: null, cultivar: "", originWording: "", source: d.source === d.referenceId ? "" : d.source } : patch);
            return (
              <fieldset key={crop} className="duration">
                <legend>{CROPS[crop].name}</legend>
                <div className="duration__grid">
                  <Field id={`duration-${crop}-min`} label="Minimum (hari)" error={error(`duration-${crop}-min`)}>
                    <input id={`duration-${crop}-min`} className="input" inputMode="numeric" value={d.min} onChange={(event) => manual({ min: event.target.value.trim() })} />
                  </Field>
                  <Field id={`duration-${crop}-max`} label="Maksimum (hari)" error={error(`duration-${crop}-max`)}>
                    <input id={`duration-${crop}-max`} className="input" inputMode="numeric" value={d.max} onChange={(event) => manual({ max: event.target.value.trim() })} />
                  </Field>
                  <Field id={`duration-${crop}-basis`} label="Dihitung sejak">
                    <select
                      id={`duration-${crop}-basis`}
                      className="input select"
                      value={d.basis}
                      onChange={(event) => setDuration(crop, { basis: event.target.value as DurationForm["basis"] })}
                    >
                      <option value="">Belum tahu</option>
                      <option value="sowing">Semai</option>
                      <option value="transplanting">Pindah tanam</option>
                    </select>
                  </Field>
                  <Field id={`duration-${crop}-source`} label="Sumber durasi">
                    <input
                      id={`duration-${crop}-source`}
                      className="input"
                      value={d.source}
                      placeholder="mis. deskripsi benih, catatan penyuluh"
                      onChange={(event) => setDuration(crop, { source: event.target.value })}
                    />
                  </Field>
                </div>
                {reference && (
                  <p className="duration__reference meta">
                    {d.referenceId ? (
                      <>
                        Memakai referensi {reference.name} ({reference.duration_days_min === reference.duration_days_max ? reference.duration_days_min : `${reference.duration_days_min}–${reference.duration_days_max}`} hari). Bukan varietas pilihan petani.
                        {!d.basis && " Sumber tidak menyebut asal hitung semai; pilih asal hitung yang Anda gunakan."}
                      </>
                    ) : (
                      <button
                        type="button"
                        className="text-button"
                        onClick={() =>
                          setDuration(crop, {
                            min: String(reference.duration_days_min),
                            max: String(reference.duration_days_max),
                            basis: reference.duration_start_event.startsWith("sowing") ? "sowing" : "",
                            source: reference.source_id,
                            referenceId: reference.source_id,
                            originWording: reference.duration_start_event,
                            cultivar: reference.name,
                          })
                        }
                      >
                        Pakai referensi varietas {reference.name} ·{" "}
                        {reference.duration_days_min === reference.duration_days_max ? reference.duration_days_min : `${reference.duration_days_min}–${reference.duration_days_max}`} hari
                      </button>
                    )}
                  </p>
                )}
              </fieldset>
            );
          })}
        </div>
        <Field id="prep-gap" label="Jeda persiapan antar musim (hari)" hint="Waktu menyiapkan petak setelah panen. Kosong berarti belum diketahui." error={error("prep-gap")} className="field--narrow">
          <input id="prep-gap" className="input" inputMode="numeric" value={form.prepGap} onChange={(event) => update((f) => ({ ...f, prepGap: event.target.value.trim() }))} />
        </Field>
      </div>

      <div className="form-block">
        <h4>Kalender untuk tanaman alternatif</h4>
        <label className="check">
          <input type="checkbox" checked={form.sharedCalendar} onChange={(event) => update((f) => ({ ...f, sharedCalendar: event.target.checked }))} />
          <span>
            Pakai tanggal dan metode tanam tiap slot juga untuk tanaman alternatif pada posisi yang sama
            <small>Tanpa pilihan ini, kalender jagung atau kedelai pada alternatif menunggu tanggal tersendiri.</small>
          </span>
        </label>
        {form.sharedCalendar && (
          <Field id="shared-note" label="Catatan asumsi kalender bersama" error={error("shared-note")}>
            <textarea
              id="shared-note"
              className="input textarea"
              rows={2}
              value={form.sharedCalendarNote}
              onChange={(event) => update((f) => ({ ...f, sharedCalendarNote: event.target.value }))}
            />
          </Field>
        )}
      </div>
    </div>
  );
}

// ---- Step 3 ---------------------------------------------------------------------

function StepConditions({ form, update }: StepProps) {
  const [more, setMore] = useState(false);
  const togglePriority = (id: Priority, checked: boolean) =>
    update((f) => ({ ...f, priorities: checked ? [...f.priorities, id] : f.priorities.filter((value) => value !== id) }));
  return (
    <div className="form-step" id="conditions">
      <h3 className="form-step__title">Kondisi &amp; prioritas</h3>
      <div className="form-block">
        <h4>Air dan drainase</h4>
        <div className="field-pair">
          <Field id="irrigation" label="Sistem irigasi">
            <select id="irrigation" className="input select" value={form.irrigationSystem} onChange={(event) => update((f) => ({ ...f, irrigationSystem: event.target.value as ScenarioForm["irrigationSystem"] }))}>
              <option value="">Belum tahu</option>
              <option value="none">Tidak ada irigasi</option>
              <option value="surface">Irigasi permukaan</option>
              <option value="sprinkler">Sprinkler</option>
              <option value="drip">Tetes</option>
              <option value="mixed">Campuran</option>
              <option value="other_documented">Lainnya, terdokumentasi</option>
            </select>
          </Field>
          <Field id="rainfed" label="Tadah hujan?">
            <select id="rainfed" className="input select" value={form.rainfed} onChange={(event) => update((f) => ({ ...f, rainfed: event.target.value as ScenarioForm["rainfed"] }))}>
              <option value="">Belum tahu</option>
              <option value="yes">Ya</option>
              <option value="no">Tidak</option>
            </select>
          </Field>
          <Field id="drainage" label="Kondisi drainase">
            <select id="drainage" className="input select" value={form.drainage} onChange={(event) => update((f) => ({ ...f, drainage: event.target.value as ScenarioForm["drainage"] }))}>
              <option value="">Belum tahu</option>
              <option value="good_reported">Baik, menurut laporan</option>
              <option value="poor_reported">Buruk, menurut laporan</option>
              <option value="variable_reported">Bervariasi, menurut laporan</option>
              <option value="other_documented">Lainnya, terdokumentasi</option>
            </select>
          </Field>
          <Field id="water-control" label="Kemampuan mengatur air">
            <select id="water-control" className="input select" value={form.waterControl} onChange={(event) => update((f) => ({ ...f, waterControl: event.target.value as ScenarioForm["waterControl"] }))}>
              <option value="">Belum tahu</option>
              <option value="can_supply_and_drain_reported">Bisa memasukkan dan membuang air</option>
              <option value="supply_only_reported">Hanya bisa memasukkan air</option>
              <option value="drain_only_reported">Hanya bisa membuang air</option>
              <option value="no_control_reported">Tidak bisa mengatur air</option>
              <option value="other_documented">Lainnya, terdokumentasi</option>
            </select>
          </Field>
        </div>
        <p className="field__hint">Laporan drainase baik belum membuktikan kelayakan transisi padi ke tanaman lahan kering.</p>
      </div>

      <fieldset className="form-block priorities">
        <legend>
          <h4>Fokus yang ingin disorot</h4>
        </legend>
        <p className="field__hint">Pilihan menyorot informasi yang relevan; tidak memberi peringkat strategi.</p>
        <div className="check-grid">
          {PRIORITIES.map((priority) => (
            <label key={priority.id} className="check">
              <input type="checkbox" checked={form.priorities.includes(priority.id)} onChange={(event) => togglePriority(priority.id, event.target.checked)} />
              <span>
                {priority.label}
                {priority.note && <small>{priority.note}</small>}
              </span>
            </label>
          ))}
        </div>
      </fieldset>

      <div className="form-block">
        <button type="button" className="button button--quiet" aria-expanded={more} aria-controls="advanced" onClick={() => setMore((v) => !v)}>
          {more ? "Sembunyikan informasi tambahan" : "Lengkapi informasi"}
        </button>
        <div id="advanced" hidden={!more} className="advanced">
          <p className="field__hint">Dipakai oleh pemeriksaan hama, transisi padi, dan legum. “Tidak ada catatan” berbeda dari “belum tahu”.</p>
          {ADVANCED.map(({ key, label, rule }) => {
            const entry = form.advanced[key];
            return (
              <div key={key} className="advanced__item">
                <ChoiceGroup
                  name={`advanced-${key}`}
                  legend={
                    <>
                      {label} <span className="meta">· {rule}</span>
                    </>
                  }
                  value={entry.state === "unknown" ? "" : entry.state}
                  options={[
                    { value: "", label: "Belum tahu" },
                    { value: "none", label: "Tidak ada catatan" },
                    { value: "note", label: "Ada catatan" },
                  ]}
                  onChange={(value) =>
                    update((f) => ({ ...f, advanced: { ...f.advanced, [key]: { ...f.advanced[key], state: value === "" ? "unknown" : value } } }))
                  }
                />
                {entry.state === "note" && (
                  <Field id={`advanced-${key}-note`} label="Catatan singkat" hint="Dicatat sebagai isian yang belum diverifikasi.">
                    <input
                      id={`advanced-${key}-note`}
                      className="input"
                      value={entry.note}
                      onChange={(event) => update((f) => ({ ...f, advanced: { ...f.advanced, [key]: { ...f.advanced[key], note: event.target.value } } }))}
                    />
                  </Field>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

// ---- Summary ------------------------------------------------------------------------

function Summary({ form, place }: { form: ScenarioForm; place: Place }) {
  const sequence = form.slots.map((slot) => slot.cropId).filter(Boolean) as CropId[];
  const allowed = CROP_IDS.filter((crop) => form.cropPolicy[crop] === "allowed");
  const excluded = CROP_IDS.filter((crop) => form.cropPolicy[crop] === "excluded");
  const durations = CROP_IDS.filter((crop) => form.durations[crop].min || form.durations[crop].max);
  const conditions = [form.irrigationSystem, form.rainfed, form.drainage, form.waterControl].filter(Boolean).length;
  const periodValid = /^\d{4}-\d{2}-\d{2}$/.test(form.start) && /^\d{4}-\d{2}-\d{2}$/.test(form.endInclusive) && form.start <= form.endInclusive;
  const rows = [
      { label: "Lokasi", value: placeLabel(place) + (place.kind === "custom" && !place.regionalClimate ? " · tanpa konteks iklim" : "") },
      {
        label: "Jenis isian",
        value: form.inputKind === "scenario_assumption" ? "Skenario asumsi" : form.inputKind === "user_reported" ? "Isian pengguna" : "Belum dipilih",
        missing: !form.inputKind,
      },
      { label: "Periode", value: periodValid ? fmtWindow(form.start, addDays(form.endInclusive, 1)) : "Belum lengkap", missing: !periodValid },
      { label: "Mode waktu", value: form.timeMode ? timeModeLabel(form.timeMode) : "Belum dipilih", missing: !form.timeMode },
      {
        label: "Rotasi berjalan",
        value: sequence.length
          ? `${sequenceLabel(sequence)}${form.continuationConfirmed ? "" : " · belum dikonfirmasi"}`
          : "Belum ada urutan",
        missing: !sequence.length || !form.continuationConfirmed,
      },
      {
        label: "Tanggal mulai",
        value: form.slots
          .map((slot, i) => {
            const start = slot.method === "transplanted" ? slot.transplantingDate : slot.method === "direct_seeded" ? slot.sowingDate : "";
            return `Slot ${i + 1}: ${start ? fmtDateShort(start) : "belum"}`;
          })
          .join(" · "),
      },
      {
        label: "Alternatif",
        value: allowed.length || excluded.length ? `Boleh: ${allowed.map((c) => CROPS[c].name).join(", ") || "—"}${excluded.length ? ` · Hindari: ${excluded.map((c) => CROPS[c].name).join(", ")}` : ""}` : "Belum ditentukan",
        missing: !allowed.length,
      },
      { label: "Slot terkunci", value: form.lockedPrefix ? `${form.lockedPrefix} slot pertama` : "Tidak ada" },
      {
        label: "Durasi",
        value: durations.length
          ? durations.map((crop) => `${CROPS[crop].name} ${form.durations[crop].min || "?"}${form.durations[crop].max !== form.durations[crop].min ? `–${form.durations[crop].max || "?"}` : ""} hari`).join(" · ")
          : "Belum diisi",
        missing: !durations.length,
      },
      { label: "Kondisi air", value: `${conditions} dari 4 diisi` },
      { label: "Fokus", value: form.priorities.length ? PRIORITIES.filter((p) => form.priorities.includes(p.id)).map((p) => p.label).join(", ") : "Belum dipilih" },
    ];
  return (
    <dl className="summary-list">
      {rows.map((row) => (
        <div key={row.label} className={row.missing ? "is-missing" : undefined}>
          <dt>{row.label}</dt>
          <dd>{row.value}</dd>
        </div>
      ))}
    </dl>
  );
}
