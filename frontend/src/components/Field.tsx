import { useId, type ReactNode } from "react";
import { Icon } from "./Icon";

export interface FieldControlProps {
  id: string;
  "aria-describedby"?: string;
  "aria-invalid"?: boolean;
  "aria-required"?: boolean;
}

interface FieldProps {
  label: string;
  hint?: ReactNode;
  error?: string | null;
  required?: boolean;
  /** Дополнительная пометка рядом с подписью: «данные клиента», «не проверено». */
  tag?: ReactNode;
  children: (control: FieldControlProps) => ReactNode;
}

/** Подпись над полем, подсказка и ошибка рядом с полем; связи через aria-describedby. */
export function Field({ label, hint, error, required = false, tag, children }: FieldProps) {
  const id = useId();
  const hintId = hint ? `${id}-hint` : undefined;
  const errorId = error ? `${id}-error` : undefined;
  const describedBy = [errorId, hintId].filter(Boolean).join(" ") || undefined;

  return (
    <div className={`field${error ? " field-invalid" : ""}`}>
      <div className="field-label-row">
        <label className="field-label" htmlFor={id}>
          {label}
          {required ? <span className="field-required"> (обязательно)</span> : null}
        </label>
        {tag}
      </div>
      {children({
        id,
        "aria-describedby": describedBy,
        "aria-invalid": error ? true : undefined,
        "aria-required": required || undefined,
      })}
      {error ? (
        <p className="field-error" id={errorId}>
          <Icon name="alert" />
          <span>
            <span className="visually-hidden">Ошибка: </span>
            {error}
          </span>
        </p>
      ) : null}
      {hint ? (
        <p className="field-hint" id={hintId}>
          {hint}
        </p>
      ) : null}
    </div>
  );
}
