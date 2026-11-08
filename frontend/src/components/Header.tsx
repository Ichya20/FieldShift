import { Menu, X } from "lucide-react";
import { useEffect, useState } from "react";
import { useActiveSection } from "../lib/hooks";

const LINKS = [
  { id: "kondisi", label: "Kondisi lokasi" },
  { id: "skenario", label: "Susun skenario" },
  { id: "perbandingan", label: "Perbandingan" },
];

export function Wordmark() {
  return (
    <span className="wordmark">
      <svg className="wordmark__mark" viewBox="0 0 24 24" aria-hidden="true">
        <path d="M5 16.5 11.5 6" />
        <path d="M9 19 15.5 8.5" />
        <path d="M13 21.5 19.5 11" />
      </svg>
      <span>FieldShift</span>
    </span>
  );
}

export function Header() {
  const active = useActiveSection(LINKS.map((link) => link.id));
  const [open, setOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => event.key === "Escape" && setOpen(false);
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  return (
    <header className={`site-header${scrolled ? " site-header--scrolled" : ""}`}>
      <div className="container site-header__row">
        <a href="#top" className="site-header__brand" aria-label="FieldShift, ke awal halaman">
          <Wordmark />
        </a>
        <nav className="site-nav" aria-label="Bagian halaman">
          <ul>
            {LINKS.map((link) => (
              <li key={link.id}>
                <a href={`#${link.id}`} aria-current={active === link.id ? "true" : undefined}>
                  {link.label}
                </a>
              </li>
            ))}
          </ul>
        </nav>
        <div className="site-header__actions">
          <a href="#kondisi" className="button button--primary button--small site-header__cta">
            Mulai eksplorasi
          </a>
          <button
            type="button"
            className="icon-button site-header__menu"
            aria-expanded={open}
            aria-controls="mobile-nav"
            onClick={() => setOpen((value) => !value)}
          >
            {open ? <X aria-hidden="true" size={22} /> : <Menu aria-hidden="true" size={22} />}
            <span className="visually-hidden">{open ? "Tutup menu" : "Buka menu"}</span>
          </button>
        </div>
      </div>
      <nav id="mobile-nav" className="mobile-nav" hidden={!open} aria-label="Bagian halaman">
        <ul className="container">
          {LINKS.map((link) => (
            <li key={link.id}>
              <a href={`#${link.id}`} onClick={() => setOpen(false)} aria-current={active === link.id ? "true" : undefined}>
                {link.label}
              </a>
            </li>
          ))}
          <li>
            <a href="#sumber" onClick={() => setOpen(false)}>
              Sumber &amp; metode
            </a>
          </li>
        </ul>
      </nav>
    </header>
  );
}
