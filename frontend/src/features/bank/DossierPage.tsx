import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router";
import { api } from "../../api/endpoints";
import { queryKeys } from "../../api/queryClient";
import type { BankApplication } from "../../api/types";
import { Icon } from "../../components/Icon";
import { KeyValueList, PageHeader, Panel } from "../../components/Layout";
import { ErrorBlock, LoadingBlock, Notice } from "../../components/States";
import { StatusBadge } from "../../components/StatusBadge";
import { Timeline } from "../../components/Timeline";
import { formatDateTime, formatTime } from "../../shared/dates";
import { formatAmount, formatMoney, formatRate } from "../../shared/money";
import { isWorkerDriven } from "../../shared/status";
import { COMPANY_FORMS, FIELD_LABELS } from "../client/draftForm";
import { documentTitle, requiredDocuments } from "../client/policy";
import { productTitle, useProducts } from "../client/products";
import { POLL_INTERVAL_MS } from "../client/queries";
import { factorText, formatRatio, outcomeOf, reasonText, recommendationText, sourceText } from "./labels";
import { OfficerActions } from "./OfficerActions";

function DeclaredData({ app }: { app: BankApplication }) {
  const d = app.draft_fields;
  const docs = app.product_code ? requiredDocuments(app.product_code) : [];
  return (
    <Panel title="Заявлено клиентом" aside={<span className="tag">Данные клиента</span>}>
      <KeyValueList
        items={[
          { label: "Компания", value: app.company_name ?? "—" },
          { label: "Демонстрационный идентификатор", value: app.demo_registration_id ?? "—", numeric: true },
          { label: "Форма", value: COMPANY_FORMS.find((f) => f.value === d?.company_form)?.label ?? d?.company_form ?? "—" },
          { label: FIELD_LABELS.requested_amount, value: formatAmount(d?.requested_amount), numeric: true },
          { label: FIELD_LABELS.term_months, value: d?.term_months ? `${d.term_months} мес.` : "—", numeric: true },
          { label: FIELD_LABELS.monthly_revenue, value: formatAmount(d?.monthly_revenue), numeric: true },
          { label: FIELD_LABELS.monthly_operating_costs, value: formatAmount(d?.monthly_operating_costs), numeric: true },
          { label: FIELD_LABELS.declared_monthly_debt_payments, value: formatAmount(d?.declared_monthly_debt_payments), numeric: true },
        ]}
      />
      {docs.length ? (
        <p className="small muted">
          Документы ({docs.map(documentTitle).join(", ")}): сервер подтвердил наличие при отправке. Содержание не
          проверялось: имя файла не является проверкой.
        </p>
      ) : null}
    </Panel>
  );
}

function Sources({ app }: { app: BankApplication }) {
  return (
    <Panel title="Источники проверок" aside={<span className="tag">Данные симулятора</span>}>
      {app.checks.length === 0 ? (
        <p className="muted">Проверки по текущему запуску ещё не выполнялись.</p>
      ) : (
        <ul className="source-list">
          {app.checks.map((check, index) => {
            const outcome = outcomeOf(check.outcome);
            return (
              <li key={`${check.source}-${index}`} className="source-row">
                <span className="source-name">{sourceText(check.source)}</span>
                <span className={outcome.ok ? "source-ok" : "source-fail"}>
                  <Icon name={outcome.ok ? "check" : "alert"} /> {outcome.label}
                </span>
                <span className="small muted num">
                  Попыток: {check.attempt_count}, {formatDateTime(check.observed_at)}
                </span>
              </li>
            );
          })}
        </ul>
      )}
      <p className="small muted">Локальные симуляторы, не реальные БКИ и реестр. Техническая ошибка источника — не кредитный отказ.</p>
    </Panel>
  );
}

function RiskAssessment({ app }: { app: BankApplication }) {
  const risk = app.risk_summary;
  if (!risk) {
    return (
      <Panel title="Оценка риска">
        <p className="muted">Результата расчёта по текущему запуску нет.</p>
      </Panel>
    );
  }
  const a = risk.affordability;
  const candidate = risk.candidate;
  return (
    <Panel title="Оценка риска и рекомендация" aside={<span className="tag">Расчёт risk-v1</span>}>
      <div className="risk-summary">
        <div>
          <span className="small muted">Рекомендация</span>
          <strong className="risk-value">{recommendationText(risk.recommendation)}</strong>
        </div>
        <div>
          <span className="small muted">Учебный балл</span>
          <strong className="risk-value num">{risk.score ?? "не рассчитан"}</strong>
        </div>
        <div>
          <span className="small muted">Класс</span>
          <strong className="risk-value">{risk.band ?? "—"}</strong>
        </div>
      </div>
      <p className="small muted">
        Балл 0–100 по демонстрационной шкале; это не вероятность одобрения. Окончательное решение — за сотрудником.
      </p>
      {risk.reasons?.length ? (
        <div className="stack-tight">
          <h3>Причины</h3>
          <ul className="bullets">
            {risk.reasons.map((code) => (
              <li key={code}>
                {reasonText(code)} <code className="mono-id muted">{code}</code>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {risk.factors?.length ? (
        <div className="stack-tight">
          <h3>Вклад факторов</h3>
          <KeyValueList
            items={risk.factors.map((f) => ({ label: factorText(f.code), value: `${f.points}`, numeric: true }))}
          />
        </div>
      ) : null}
      {a ? (
        <div className="stack-tight">
          <h3>Доступность</h3>
          <KeyValueList
            items={[
              { label: "Свободный поток (выручка − расходы)", value: formatMoney(a.free_cashflow), numeric: true },
              { label: "Текущие платежи по данным бюро", value: formatMoney(a.existing_payment), numeric: true },
              { label: "Платёж по запрошенной сумме", value: formatMoney(a.requested_payment), numeric: true },
              { label: "DSCR по запрошенной сумме", value: formatRatio(a.requested_dscr), numeric: true },
              { label: "Платёж по предложению", value: formatMoney(a.offered_payment), numeric: true },
              { label: "DSCR по предложению", value: formatRatio(a.offered_dscr), numeric: true },
              { label: "Сумма выплат по предложению", value: formatMoney(a.total_payment), numeric: true },
            ]}
          />
        </div>
      ) : null}
      {candidate ? (
        <div className="stack-tight">
          <h3>Рекомендованные условия</h3>
          <KeyValueList
            items={[
              {
                label: "Сумма",
                value: formatAmount(candidate.amount),
                numeric: true,
                note: candidate.is_alternative ? "Меньше запрошенной" : undefined,
              },
              { label: "Срок", value: `${candidate.term_months ?? "—"} мес.`, numeric: true },
              { label: "Ставка", value: `${formatRate(candidate.annual_rate)} годовых`, numeric: true },
              { label: "Комиссии", value: formatMoney(candidate.fees ?? null), numeric: true },
            ]}
          />
        </div>
      ) : null}
    </Panel>
  );
}

function Revisions({ app }: { app: BankApplication }) {
  return (
    <Panel title="Ревизии">
      {app.revisions.length === 0 ? (
        <p className="muted">Заявка ещё не отправлялась.</p>
      ) : (
        <KeyValueList
          items={app.revisions.map((r) => ({
            label: `Ревизия ${r.revision_no}${r.revision_no === app.current_revision ? " (текущая)" : ""}`,
            value: formatDateTime(r.submitted_at),
            numeric: true,
            note: <code className="hash">{r.snapshot_hash.slice(0, 12)}…</code>,
          }))}
        />
      )}
    </Panel>
  );
}

export function DossierPage() {
  const { id = "" } = useParams();
  const products = useProducts();
  const dossier = useQuery({
    queryKey: queryKeys.bankApplication(id),
    queryFn: ({ signal }) => api.bankApplication(id, { signal }),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status && isWorkerDriven(status) ? POLL_INTERVAL_MS : false;
    },
  });

  if (dossier.isPending) return <LoadingBlock rows={8} label="Загружаем досье" />;
  if (dossier.isError) {
    return (
      <div className="stack-lg">
        <PageHeader title="Досье" backTo="/bank/applications" backLabel="Очередь" />
        <ErrorBlock error={dossier.error} onRetry={() => void dossier.refetch()} />
      </div>
    );
  }
  const app = dossier.data;
  return (
    <div className="stack-lg">
      <PageHeader
        title={app.company_name ?? "Досье заявки"}
        backTo="/bank/applications"
        backLabel="Очередь"
        meta={
          <>
            <StatusBadge status={app.status} />
            <span>{productTitle(products.data, app.product_code)}</span>
            <span className="num">Ревизия {app.current_revision}, версия {app.version}</span>
            <span className="num">Данные на {formatTime(new Date(dossier.dataUpdatedAt))}</span>
          </>
        }
      />
      {app.status === "PROCESSING_ERROR" ? (
        <Notice tone="warning" title="Проверка не завершена из-за технической ошибки источника.">
          Это не кредитный отказ. Перезапустите проверку, когда источник будет доступен.
        </Notice>
      ) : null}
      <div className="dossier-grid">
        <div className="stack-lg">
          <RiskAssessment app={app} />
          <DeclaredData app={app} />
          <Sources app={app} />
        </div>
        <div className="stack-lg dossier-aside">
          <OfficerActions app={app} />
          <Revisions app={app} />
          <Panel title="История">
            <Timeline events={app.audit} showRevision />
          </Panel>
        </div>
      </div>
    </div>
  );
}
