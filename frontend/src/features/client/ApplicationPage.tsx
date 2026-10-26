import { useQuery } from "@tanstack/react-query";
import { Navigate, useParams } from "react-router";
import { api } from "../../api/endpoints";
import { queryKeys } from "../../api/queryClient";
import type { ClientApplication, Product } from "../../api/types";
import { ButtonLink } from "../../components/Button";
import { Icon } from "../../components/Icon";
import { KeyValueList, PageHeader, Panel } from "../../components/Layout";
import { ErrorBlock, LoadingBlock, Notice } from "../../components/States";
import { StatusBadge } from "../../components/StatusBadge";
import { Timeline } from "../../components/Timeline";
import { formatTime } from "../../shared/dates";
import { formatAmount } from "../../shared/money";
import { isWorkerDriven } from "../../shared/status";
import { AgreementPanel } from "./AgreementPanel";
import { COMPANY_FORMS, FIELD_LABELS } from "./draftForm";
import { OfferPanel, OfferTerms } from "./OfferPanel";
import { productTitle, useProducts } from "./products";
import { useClientApplication, useHistory } from "./queries";
import { SupplementPanel } from "./SupplementPanel";

function Explanation({ id, topic, title }: { id: string; topic: "why" | "next"; title: string }) {
  const explain = useQuery({
    queryKey: queryKeys.explain(id, topic),
    queryFn: ({ signal }) => api.explain(id, topic, { signal }),
  });
  if (explain.isPending) return <LoadingBlock rows={2} label="Загружаем объяснение" />;
  if (explain.isError) return <ErrorBlock error={explain.error} onRetry={() => void explain.refetch()} />;
  return (
    <div className="stack">
      <p>
        <strong>{title}</strong> {explain.data.headline}
      </p>
      {explain.data.bullets.length ? (
        <ul className="bullets">
          {explain.data.bullets.map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>
      ) : null}
      <p className="small muted">{explain.data.disclaimer}</p>
    </div>
  );
}

function CompletedSummary({ app }: { app: ClientApplication }) {
  const offer = useQuery({
    queryKey: queryKeys.offer(app.id),
    queryFn: ({ signal }) => api.offer(app.id, { signal }),
  });
  return (
    <Panel title="Результат" id="result">
      <Notice tone="success" title="Выдача смоделирована. Реальные средства не переводились.">
        Это учебный сценарий: договор, подпись и выдача имитированы на демонстрационном стенде.
      </Notice>
      {offer.data ? <OfferTerms offer={offer.data} requestedAmount={app.draft_fields?.requested_amount} /> : null}
    </Panel>
  );
}

/** Содержимое текущего шага: что происходит и что может сделать клиент. */
function CurrentStep({ app, product }: { app: ClientApplication; product: Product | undefined }) {
  switch (app.status) {
    case "SUBMITTED":
    case "CHECKING":
      return (
        <Panel title="Проверяем сведения" id="step">
          <p>
            Заявка отправлена. Сведения проверяются на демонстрационных источниках, после этого заявку рассмотрит
            специалист. Страница обновляется сама — можно закрыть её и вернуться позже.
          </p>
        </Panel>
      );
    case "NEEDS_INFO":
      return <SupplementPanel app={app} product={product} />;
    case "PROCESSING_ERROR":
      return (
        <Panel title="Проверка временно недоступна" id="step">
          <Notice tone="warning" title="Заявка сохранена.">
            Демонстрационный источник данных не ответил. Это техническая ошибка, а не отказ по кредиту:
            специалист банка может перезапустить проверку.
          </Notice>
        </Panel>
      );
    case "MANUAL_REVIEW":
      return (
        <Panel title="Заявка у специалиста" id="step">
          <p>
            Проверки завершены, специалист изучает заявку и подтвердит условия или примет решение. Точное время
            ответа не гарантируется.
          </p>
        </Panel>
      );
    case "OFFERED":
      return <OfferPanel app={app} />;
    case "ACCEPTED":
      return <AgreementPanel app={app} />;
    case "SIGNED":
      return (
        <Panel title="Подписание смоделировано" id="step">
          <p>Ожидаем имитацию выдачи. Страница обновится сама.</p>
        </Panel>
      );
    case "COMPLETED":
      return <CompletedSummary app={app} />;
    case "REJECTED":
      return (
        <Panel title="По заявке принято отрицательное решение" id="step">
          <Explanation id={app.id} topic="why" title="Причина." />
          <div>
            <ButtonLink to="/applications/new">Создать новую заявку</ButtonLink>
          </div>
        </Panel>
      );
    case "DECLINED_BY_CLIENT":
      return (
        <Panel title="Вы отклонили предложение" id="step">
          <p>Заявка завершена. Если финансирование снова понадобится, создайте новую заявку.</p>
          <div>
            <ButtonLink to="/applications/new">Создать новую заявку</ButtonLink>
          </div>
        </Panel>
      );
    default:
      return null;
  }
}

function SubmittedData({ app }: { app: ClientApplication }) {
  const draft = app.draft_fields;
  return (
    <Panel title="Данные заявки">
      <KeyValueList
        items={[
          { label: FIELD_LABELS.requested_amount, value: formatAmount(draft?.requested_amount), numeric: true },
          { label: FIELD_LABELS.term_months, value: draft?.term_months ? `${draft.term_months} мес.` : "—", numeric: true },
          { label: "Форма", value: COMPANY_FORMS.find((form) => form.value === draft?.company_form)?.label ?? draft?.company_form ?? "—" },
          { label: "Выручка в месяц", value: formatAmount(draft?.monthly_revenue), numeric: true },
          { label: "Расходы в месяц", value: formatAmount(draft?.monthly_operating_costs), numeric: true },
          { label: "Платежи по кредитам", value: formatAmount(draft?.declared_monthly_debt_payments), numeric: true },
        ]}
      />
    </Panel>
  );
}

export function ApplicationPage() {
  const { id = "" } = useParams();
  const application = useClientApplication(id);
  const products = useProducts();
  const history = useHistory(id, application.data?.status, application.data?.version);

  if (application.isPending) return <LoadingBlock rows={6} label="Загружаем заявку" />;
  if (application.isError) {
    return (
      <div className="stack-lg">
        <PageHeader title="Заявка" backTo="/applications" backLabel="Мои заявки" />
        <ErrorBlock error={application.error} onRetry={() => void application.refetch()} />
      </div>
    );
  }

  const app = application.data;
  if (app.status === "DRAFT") return <Navigate to={`/applications/${id}/edit`} replace />;
  const product = products.data?.find((item) => item.code === app.product_code);
  const polling = isWorkerDriven(app.status);

  return (
    <div className="stack-lg">
      <PageHeader
        title={productTitle(products.data, app.product_code)}
        backTo="/applications"
        backLabel="Мои заявки"
        meta={
          <>
            <StatusBadge status={app.status} />
            <span>Следующий шаг: {app.next_action}</span>
            <span className="nowrap">
              <Icon name={polling ? "refresh" : "clock"} /> Данные на{" "}
              <span className="num">{formatTime(new Date(application.dataUpdatedAt))}</span>
              {polling ? ", обновляются автоматически" : null}
            </span>
          </>
        }
      />
      {application.errorUpdatedAt > application.dataUpdatedAt && application.failureReason ? (
        <ErrorBlock
          error={application.failureReason}
          title="Не удалось обновить статус. Показаны последние полученные данные."
          onRetry={() => void application.refetch()}
        />
      ) : null}
      <div className="card-grid">
        <div className="stack-lg">
          <CurrentStep app={app} product={product} />
          <SubmittedData app={app} />
        </div>
        <Panel title="История">
          {history.isPending ? (
            <LoadingBlock rows={4} label="Загружаем историю" />
          ) : history.isError ? (
            <ErrorBlock error={history.error} onRetry={() => void history.refetch()} />
          ) : (
            <Timeline events={history.data} />
          )}
        </Panel>
      </div>
    </div>
  );
}
