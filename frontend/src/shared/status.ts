import statusContract from "@contracts/statuses.json";
import type { ApplicationStatus } from "../api/types";

/** Подписи и терминальность — только из contracts/statuses.json. */
const CLIENT_LABELS = statusContract.client_labels as Record<ApplicationStatus, string>;
const TERMINAL = new Set<string>(statusContract.terminal);

export const ALL_STATUSES = statusContract.statuses as ApplicationStatus[];

/** Состояния, в которых результат меняет worker без участия пользователя — их опрашиваем. */
const WORKER_DRIVEN = new Set<ApplicationStatus>(["SUBMITTED", "CHECKING", "SIGNED"]);

export function statusLabel(status: ApplicationStatus): string {
  return CLIENT_LABELS[status] ?? status;
}

export function isTerminal(status: ApplicationStatus): boolean {
  return TERMINAL.has(status);
}

export function isWorkerDriven(status: ApplicationStatus): boolean {
  return WORKER_DRIVEN.has(status);
}

export type StatusTone = "neutral" | "progress" | "attention" | "positive" | "negative";

/** Тон бейджа. Ошибка обработки — «attention», а не «negative»: это не кредитный отказ. */
export function statusTone(status: ApplicationStatus): StatusTone {
  switch (status) {
    case "SUBMITTED":
    case "CHECKING":
    case "MANUAL_REVIEW":
    case "SIGNED":
      return "progress";
    case "NEEDS_INFO":
    case "OFFERED":
    case "ACCEPTED":
    case "PROCESSING_ERROR":
      return "attention";
    case "COMPLETED":
      return "positive";
    case "REJECTED":
      return "negative";
    default:
      return "neutral";
  }
}
