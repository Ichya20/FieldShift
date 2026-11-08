import { CircleDashed, CircleMinus, CircleQuestionMark, Eye, Info, MapPinOff, TriangleExclamationPoint, type LucideIcon } from "lucide-react";
import { statusOf } from "../lib/labels";
import type { Status } from "../lib/types";

const ICONS: Partial<Record<Status, LucideIcon>> = {
  evidence_available: Info,
  needs_input: CircleQuestionMark,
  review_required: Eye,
  input_conflict: TriangleExclamationPoint,
  outside_coverage: MapPinOff,
  not_applicable: CircleMinus,
  partial: CircleDashed,
  invalid_input: TriangleExclamationPoint,
  insufficient_alternatives: CircleDashed,
  complete_for_selected_checks: Info,
};

export function StatusBadge({ status, label, compact = false }: { status: Status | string; label?: string; compact?: boolean }) {
  const meta = statusOf(status);
  const Icon = ICONS[status as Status] ?? CircleDashed;
  return (
    <span className={`badge badge--${meta.tone}${compact ? " badge--compact" : ""}`}>
      <Icon aria-hidden="true" size={compact ? 14 : 15} strokeWidth={2} />
      <span>{label ?? meta.label}</span>
    </span>
  );
}
