import { ChevronDown } from "lucide-react";
import { useId, useState, type ReactNode } from "react";
import { useMediaQuery } from "../lib/hooks";

interface Props {
  title: ReactNode;
  status?: ReactNode;
  meta?: ReactNode;
  children: ReactNode;
  defaultOpen?: boolean;
  className?: string;
}

/** Always open on wide screens; a labelled toggle with visible status on phones. */
export function Disclosure({ title, status, meta, children, defaultOpen = false, className = "" }: Props) {
  const compact = useMediaQuery("(max-width: 720px)");
  const [open, setOpen] = useState(defaultOpen);
  const id = useId();
  const expanded = !compact || open;
  return (
    <section className={`panel disclosure ${className}`}>
      <header className="disclosure__head">
        {compact ? (
          <button type="button" className="disclosure__toggle" aria-expanded={open} aria-controls={id} onClick={() => setOpen((v) => !v)}>
            <span className="disclosure__title">{title}</span>
            <ChevronDown aria-hidden="true" size={20} className="disclosure__chevron" />
          </button>
        ) : (
          <h3 className="disclosure__title">{title}</h3>
        )}
        {status && <div className="disclosure__status">{status}</div>}
      </header>
      {meta && <div className="disclosure__meta">{meta}</div>}
      <div id={id} hidden={!expanded} className="disclosure__body">
        {children}
      </div>
    </section>
  );
}
