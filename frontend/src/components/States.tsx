import type { ReactNode } from "react";
import { isApiError, messageFor } from "../api/errors";
import { Button } from "./Button";
import { Icon } from "./Icon";

/** Загрузка: серые плашки в размер будущего содержимого, без анимированного блеска. */
export function LoadingBlock({ rows = 3, label = "Загружаем данные" }: { rows?: number; label?: string }) {
  return (
    <div className="loading-block" role="status" aria-live="polite">
      <span className="visually-hidden">{label}</span>
      {Array.from({ length: rows }, (_, index) => (
        <span key={index} className="skeleton" style={{ width: `${88 - index * 17}%` }} aria-hidden="true" />
      ))}
    </div>
  );
}

/** Ошибка внутри блока, который не загрузился: что случилось и как повторить. */
export function ErrorBlock({ error, onRetry, title }: { error: unknown; onRetry?: () => void; title?: string }) {
  const requestId = isApiError(error) ? error.requestId : null;
  return (
    <div className="notice notice-error" role="alert">
      <Icon name="alert" />
      <div className="stack-tight">
        <p>
          <strong>{title ?? "Не удалось загрузить данные."}</strong> {messageFor(error)}
        </p>
        {requestId ? <p className="small muted">Код запроса: {requestId}</p> : null}
        {onRetry ? (
          <div>
            <Button variant="ghost" onClick={onRetry}>
              <Icon name="refresh" /> Повторить
            </Button>
          </div>
        ) : null}
      </div>
    </div>
  );
}

/** Пустое состояние держит рамку блока и объясняет следующий шаг. */
export function EmptyBlock({ children, action }: { children: ReactNode; action?: ReactNode }) {
  return (
    <div className="empty-block">
      <p>{children}</p>
      {action}
    </div>
  );
}

export function Notice({
  tone = "info",
  children,
  title,
}: {
  tone?: "info" | "warning" | "error" | "success";
  title?: ReactNode;
  children?: ReactNode;
}) {
  const icon = tone === "success" ? "check" : tone === "info" ? "info" : "alert";
  return (
    <div className={`notice notice-${tone}`} role={tone === "error" ? "alert" : undefined}>
      <Icon name={icon} />
      <div className="stack-tight">
        {title ? <p className="notice-title">{title}</p> : null}
        {children}
      </div>
    </div>
  );
}
