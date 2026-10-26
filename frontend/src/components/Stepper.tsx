import type { CSSProperties } from "react";
import type { ApplicationStatus } from "../api/types";
import { STAGES, stageOf } from "../shared/stages";
import { statusLabel } from "../shared/status";

/** Трекер этапов заявки. Текущий этап назван текстом для скринридера, а не только цветом. */
export function Stepper({ status, compact = false }: { status: ApplicationStatus; compact?: boolean }) {
  const { index, tone } = stageOf(status);
  return (
    <ol
      className={`stepper${compact ? " stepper-compact" : ""}`}
      style={{ "--steps": STAGES.length } as CSSProperties}
      aria-label={`Этап заявки: ${STAGES[index]}, статус «${statusLabel(status)}»`}
    >
      {STAGES.map((stage, position) => {
        const done = position < index || (position === index && tone === "done");
        const current = position === index && tone !== "done";
        const className = [
          "step",
          done ? "step-done" : null,
          current ? "step-current" : null,
          current && tone !== "normal" ? `step-${tone}` : null,
        ]
          .filter(Boolean)
          .join(" ");
        return (
          <li key={stage} className={className} aria-current={current ? "step" : undefined}>
            <span className="step-bar" aria-hidden="true" />
            <span className="step-label">{stage}</span>
          </li>
        );
      })}
    </ol>
  );
}
