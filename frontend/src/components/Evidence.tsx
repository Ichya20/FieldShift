import { ExternalLink, X } from "lucide-react";
import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from "react";
import { DATA_KIND, resolveSource, type DataKind } from "../lib/sources";
import type { SourceEntry } from "../lib/types";
import { translateNote } from "../lib/labels";

export interface EvidenceItem {
  title: string;
  value?: string;
  kind: DataKind;
  sourceRefs: string[];
  period?: string;
  support?: string;
  validity?: string;
  method?: string;
  limitations?: string[];
  assumptions?: string[];
}

const EvidenceContext = createContext<(item: EvidenceItem) => void>(() => undefined);

export const useEvidence = () => useContext(EvidenceContext);

export function EvidenceProvider({ catalog, children }: { catalog?: Record<string, SourceEntry>; children: ReactNode }) {
  const [item, setItem] = useState<EvidenceItem | null>(null);
  const dialog = useRef<HTMLDialogElement>(null);
  const open = useCallback((next: EvidenceItem) => setItem(next), []);

  useEffect(() => {
    const element = dialog.current;
    if (!element) return;
    if (item && !element.open) element.showModal();
    if (!item && element.open) element.close();
  }, [item]);

  return (
    <EvidenceContext.Provider value={open}>
      {children}
      <dialog
        ref={dialog}
        className="drawer"
        aria-labelledby="drawer-title"
        onClose={() => setItem(null)}
        onClick={(event) => {
          if (event.target === event.currentTarget) setItem(null);
        }}
      >
        {item && (
          <div className="drawer__panel">
            <header className="drawer__head">
              <div>
                <p className="drawer__kicker">Bukti &amp; sumber</p>
                <h2 id="drawer-title">{item.title}</h2>
              </div>
              <button type="button" className="icon-button" onClick={() => setItem(null)} aria-label="Tutup bukti dan sumber">
                <X aria-hidden="true" size={20} />
              </button>
            </header>
            <div className="drawer__body">
              {item.value && <p className="drawer__value">{item.value}</p>}
              <dl className="facts">
                <div>
                  <dt>Jenis data</dt>
                  <dd>{DATA_KIND[item.kind]}</dd>
                </div>
                {item.period && (
                  <div>
                    <dt>Periode</dt>
                    <dd>{item.period}</dd>
                  </div>
                )}
                {item.support && (
                  <div>
                    <dt>Dukungan ruang</dt>
                    <dd>{item.support}</dd>
                  </div>
                )}
                {item.validity && (
                  <div>
                    <dt>Cakupan valid</dt>
                    <dd>{item.validity}</dd>
                  </div>
                )}
                {item.method && (
                  <div>
                    <dt>Metode turunan</dt>
                    <dd>{item.method}</dd>
                  </div>
                )}
              </dl>
              {item.assumptions && item.assumptions.length > 0 && (
                <section className="drawer__section">
                  <h3>Asumsi yang dipakai</h3>
                  <ul className="plain-list">
                    {item.assumptions.map((text) => (
                      <li key={text}>{text}</li>
                    ))}
                  </ul>
                </section>
              )}
              {item.limitations && item.limitations.length > 0 && (
                <section className="drawer__section">
                  <h3>Keterbatasan</h3>
                  <ul className="plain-list">
                    {item.limitations.map((text) => (
                      <li key={text}>{translateNote(text)}</li>
                    ))}
                  </ul>
                </section>
              )}
              <section className="drawer__section">
                <h3>Sumber</h3>
                <ul className="source-list">
                  {item.sourceRefs.map((id) => {
                    const source = resolveSource(id, catalog);
                    return (
                      <li key={id}>
                        <p className="source-list__name">{source.name}</p>
                        <p className="source-list__meta">
                          {source.org} · {DATA_KIND[source.kind]}
                          {source.accessed ? ` · diakses ${source.accessed.slice(0, 10)}` : ""}
                        </p>
                        {source.url && (
                          <a href={source.url} target="_blank" rel="noreferrer" className="text-link">
                            Buka sumber <ExternalLink aria-hidden="true" size={14} />
                          </a>
                        )}
                        {source.sha256 && <p className="source-list__hash">SHA-256 snapshot lokal {source.sha256.slice(0, 12)}…</p>}
                      </li>
                    );
                  })}
                </ul>
              </section>
              <p className="drawer__note">
                Data NASA disebut sebagai sumber data; FieldShift tidak berafiliasi dengan NASA. Angka dibulatkan untuk tampilan.
              </p>
            </div>
          </div>
        )}
      </dialog>
    </EvidenceContext.Provider>
  );
}

export function SourceButton({ item, label = "Lihat sumber", children }: { item: EvidenceItem; label?: string; children?: ReactNode }) {
  const open = useEvidence();
  return (
    <button type="button" className="text-button" onClick={() => open(item)}>
      {children ?? label}
    </button>
  );
}
