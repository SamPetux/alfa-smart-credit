import type { ReactNode } from "react";
import type { OfferTerms } from "../api/types";
import { formatAmount, formatMoney, formatRate } from "../shared/money";
import { Icon } from "./Icon";
import { KeyValueList } from "./Layout";

interface AgreementPayload {
  notice?: string;
  revision_no?: number;
  terms?: OfferTerms;
}

/** Документ backend — JSON; если разобрать не удалось, показываем только исходный текст. */
function parseAgreement(text: string): AgreementPayload | null {
  try {
    const parsed: unknown = JSON.parse(text);
    return typeof parsed === "object" && parsed !== null ? (parsed as AgreementPayload) : null;
  } catch {
    return null;
  }
}

function ReadableAgreement({ payload }: { payload: AgreementPayload }) {
  const terms = payload.terms ?? {};
  const items: Array<{ label: ReactNode; value: ReactNode; numeric?: boolean }> = [
    { label: "Сумма", value: formatAmount(terms.amount), numeric: true },
    { label: "Срок", value: terms.term_months ? `${terms.term_months} мес.` : "—", numeric: true },
    { label: "Ставка", value: `${formatRate(terms.annual_rate)} годовых`, numeric: true },
    { label: "Комиссии", value: formatMoney(terms.fees ?? null), numeric: true },
    { label: "Валюта", value: terms.currency ?? "—" },
  ];
  if (payload.revision_no !== undefined) {
    items.push({ label: "Ревизия заявки", value: payload.revision_no, numeric: true });
  }
  return (
    <div className="document-readable stack">
      {payload.notice ? <p>{payload.notice}</p> : null}
      <KeyValueList items={items} />
    </div>
  );
}

/**
 * Демонстрационный документ. Читаемое представление собрано из того же текста,
 * исходник доступен целиком: контрольная сумма относится именно к нему.
 */
export function DocumentView({ title, text, contentHash }: { title: string; text: string; contentHash: string }) {
  const payload = parseAgreement(text);
  return (
    <figure className="document">
      <figcaption className="document-head">
        <Icon name="file" />
        <span>{title}</span>
        <span className="document-stamp small">Имитация, не юридический документ</span>
      </figcaption>
      {payload ? <ReadableAgreement payload={payload} /> : null}
      <details className="document-source" open={!payload}>
        <summary>Исходный текст документа</summary>
        <pre className="document-body" tabIndex={0} aria-label={`Текст документа: ${title}`}>
          {text}
        </pre>
      </details>
      <p className="document-hash small muted">
        Контрольная сумма SHA-256: <code className="hash">{contentHash}</code>
      </p>
    </figure>
  );
}
