import type { AuditEvent } from "../api/types";
import { formatDateTime } from "../shared/dates";
import { statusLabel } from "../shared/status";

const ACTION_LABELS: Record<string, string> = {
  CREATE_DRAFT: "Черновик создан",
  SAVE_DRAFT: "Черновик сохранён",
  UPLOAD_DOCUMENT: "Загружен документ",
  SUBMIT: "Заявка отправлена",
  START_CHECKS: "Начаты проверки",
  FINISH_CHECKS: "Проверки завершены, заявка передана специалисту",
  REQUIRE_INFO: "Нужны дополнительные сведения",
  PROCESSING_FAILED: "Проверка временно недоступна",
  RETRY_CHECKS: "Проверка запущена повторно",
  REQUEST_INFO: "Специалист запросил уточнение",
  SAVE_SUPPLEMENT: "Уточнения сохранены",
  RESUBMIT: "Уточнения отправлены",
  APPROVE_OFFER: "Специалист подтвердил условия",
  REJECT: "Принято отрицательное решение",
  ACCEPT_OFFER: "Условия приняты",
  DECLINE_OFFER: "Предложение отклонено",
  SIMULATE_SIGN: "Подписание смоделировано",
  COMPLETE_SIMULATION: "Выдача смоделирована",
  RETRY_DISBURSEMENT: "Имитация выдачи запущена повторно",
};

export function actionLabel(action: string): string {
  return ACTION_LABELS[action] ?? action;
}

/** История заявки: новые события сверху, у каждого — время и ревизия. */
export function Timeline({ events, showRevision = false }: { events: AuditEvent[]; showRevision?: boolean }) {
  const ordered = [...events].reverse();
  return (
    <ol className="timeline">
      {ordered.map((event, index) => (
        <li key={`${event.action}-${event.created_at}-${index}`} className={index === 0 ? "timeline-current" : undefined}>
          <div className="timeline-title">{actionLabel(event.action)}</div>
          <div className="timeline-meta small muted">
            <time dateTime={event.created_at ?? undefined} className="num">
              {formatDateTime(event.created_at)}
            </time>
            {event.to_status && event.from_status !== event.to_status ? (
              <span>{statusLabel(event.to_status)}</span>
            ) : null}
            {showRevision ? <span className="num">Ревизия {event.revision_no}</span> : null}
          </div>
        </li>
      ))}
    </ol>
  );
}
