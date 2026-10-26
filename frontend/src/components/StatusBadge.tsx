import type { ApplicationStatus } from "../api/types";
import { statusLabel, statusTone } from "../shared/status";

/** Статус текстом из contracts/statuses.json; цвет только дублирует смысл. */
export function StatusBadge({ status }: { status: ApplicationStatus }) {
  return (
    <span className={`badge badge-${statusTone(status)}`} data-status={status}>
      {statusLabel(status)}
    </span>
  );
}
