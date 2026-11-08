import { ExternalLink } from "lucide-react";
import { ATTRIBUTION, resolveSource } from "../lib/sources";
import type { SourceEntry } from "../lib/types";
import { Wordmark } from "./Header";

export function SourcesSection({ catalog }: { catalog?: Record<string, SourceEntry> }) {
  return (
    <section id="sumber" className="section section--sources" aria-labelledby="sumber-title">
      <div className="container sources">
        <div className="sources__intro">
          <h2 id="sumber-title">Sumber &amp; metode</h2>
          <p>
            FieldShift membaca snapshot data publik yang disiapkan untuk area contoh Yogyakarta–Klaten. Data NASA memberi konteks iklim dan
            vegetasi; tanah, medan, tutupan lahan, dan agronomi memakai atribusinya masing-masing. Aplikasi tidak mengambil observasi baru
            saat dibuka.
          </p>
          <ul className="method-points">
            <li>Nilai yang tidak diketahui tetap kosong, bukan nol.</li>
            <li>Hari atau komposit yang tidak lolos kualitas tidak diisi dengan interpolasi.</li>
            <li>Titik di luar cakupan tidak menerima angka dari titik terdekat.</li>
            <li>Tidak ada peringkat, skor kesesuaian, prediksi hasil, penghematan air, atau keuntungan.</li>
            <li>Metode 0.1.0 belum divalidasi secara agronomi di lapangan.</li>
          </ul>
        </div>
        <dl className="attribution">
          {ATTRIBUTION.map(({ id, role }) => {
            const source = resolveSource(id, catalog);
            return (
              <div key={id}>
                <dt>
                  {source.url ? (
                    <a href={source.url} target="_blank" rel="noreferrer">
                      {source.name} <ExternalLink aria-hidden="true" size={13} />
                    </a>
                  ) : (
                    source.name
                  )}
                </dt>
                <dd>
                  {role} <span className="meta">{source.org}</span>
                </dd>
              </div>
            );
          })}
        </dl>
      </div>
    </section>
  );
}

export function Footer() {
  return (
    <footer className="site-footer">
      <div className="container site-footer__row">
        <div className="site-footer__id">
          <Wordmark />
          <p className="meta">Eksplorasi rotasi padi, jagung, dan kedelai untuk area contoh Yogyakarta–Klaten. Isian digunakan selama sesi ini.</p>
        </div>
        <nav aria-label="Tautan bagian">
          <ul>
            <li>
              <a href="#kondisi">Kondisi lokasi</a>
            </li>
            <li>
              <a href="#skenario">Susun skenario</a>
            </li>
            <li>
              <a href="#perbandingan">Perbandingan</a>
            </li>
            <li>
              <a href="#sumber">Sumber &amp; metode</a>
            </li>
          </ul>
        </nav>
        <p className="meta site-footer__note">
          Dibuat untuk NASA Space Apps Challenge 2026 · Field Shift. Memakai data NASA, tanpa afiliasi resmi. Tekstur diorama: Poly Haven (CC0). Peta dasar © kontributor OpenStreetMap.
        </p>
      </div>
    </footer>
  );
}
