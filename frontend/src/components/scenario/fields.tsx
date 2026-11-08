import type { ReactNode } from "react";

interface FieldProps {
  id: string;
  label: ReactNode;
  hint?: ReactNode;
  error?: string;
  children: ReactNode;
  className?: string;
}

export function Field({ id, label, hint, error, children, className = "" }: FieldProps) {
  return (
    <div className={`field${error ? " field--error" : ""} ${className}`}>
      <label className="field__label" htmlFor={id}>
        {label}
      </label>
      {children}
      {hint && (
        <p className="field__hint" id={`${id}-hint`}>
          {hint}
        </p>
      )}
      {error && (
        <p className="field__error" id={`${id}-error`}>
          {error}
        </p>
      )}
    </div>
  );
}

interface ChoiceProps<T extends string> {
  name: string;
  legend: ReactNode;
  value: T | "";
  options: { value: T | ""; label: string; note?: string }[];
  onChange: (value: T | "") => void;
  hint?: ReactNode;
  error?: string;
  id?: string;
}

/** Radio group; every group that maps to an unknown-able field includes "Belum tahu" (empty). */
export function ChoiceGroup<T extends string>({ name, legend, value, options, onChange, hint, error, id }: ChoiceProps<T>) {
  return (
    <fieldset className={`choice-row${error ? " field--error" : ""}`} id={id}>
      <legend className="field__label">{legend}</legend>
      <div className="choice-row__options">
        {options.map((option) => (
          <label key={option.value || "unknown"} className="choice">
            <input type="radio" name={name} value={option.value} checked={value === option.value} onChange={() => onChange(option.value)} />
            <span>
              {option.label}
              {option.note && <small>{option.note}</small>}
            </span>
          </label>
        ))}
      </div>
      {hint && <p className="field__hint">{hint}</p>}
      {error && <p className="field__error">{error}</p>}
    </fieldset>
  );
}

export const UNKNOWN = "Belum tahu";
