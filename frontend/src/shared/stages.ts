import type { ApplicationStatus } from "../api/types";

/**
 * Этапы пути заявки для трекера. Это группировка статусов из contracts/statuses.json,
 * а не процент готовности: этап показывает, где заявка сейчас, без оценки сроков.
 */
export const STAGES = ["Отправка", "Проверка", "Решение", "Условия", "Подписание", "Выдача"] as const;

export type StageTone = "normal" | "attention" | "negative" | "done";

export interface StagePosition {
  /** Индекс текущего этапа в STAGES. */
  index: number;
  tone: StageTone;
}

const POSITIONS: Record<ApplicationStatus, StagePosition> = {
  DRAFT: { index: 0, tone: "normal" },
  SUBMITTED: { index: 1, tone: "normal" },
  CHECKING: { index: 1, tone: "normal" },
  NEEDS_INFO: { index: 1, tone: "attention" },
  PROCESSING_ERROR: { index: 1, tone: "attention" },
  MANUAL_REVIEW: { index: 2, tone: "normal" },
  REJECTED: { index: 2, tone: "negative" },
  OFFERED: { index: 3, tone: "normal" },
  DECLINED_BY_CLIENT: { index: 3, tone: "negative" },
  ACCEPTED: { index: 4, tone: "normal" },
  SIGNED: { index: 5, tone: "normal" },
  COMPLETED: { index: 5, tone: "done" },
};

export function stageOf(status: ApplicationStatus): StagePosition {
  return POSITIONS[status];
}
