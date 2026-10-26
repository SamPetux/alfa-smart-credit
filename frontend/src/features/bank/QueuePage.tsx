import { useQuery } from "@tanstack/react-query";
import { Link, useSearchParams } from "react-router";
import { api } from "../../api/endpoints";
import { queryKeys } from "../../api/queryClient";
import type { ApplicationStatus, BankApplication, BankQueueFilters, ProductCode } from "../../api/types";
import { Button } from "../../components/Button";
import { Field } from "../../components/Field";
import { PageHeader, Panel } from "../../components/Layout";
import { EmptyBlock, ErrorBlock, LoadingBlock } from "../../components/States";
import { StatusBadge } from "../../components/StatusBadge";
import { formatDateTime, formatWaiting } from "../../shared/dates";
import { formatAmount } from "../../shared/money";
import { ALL_STATUSES, statusLabel } from "../../shared/status";
import { productTitle, useProducts } from "../client/products";

const PAGE_LIMIT = 50;

function needsOfficer(app: BankApplication): boolean {
  return app.allowed_actions.length > 0;
}

function QueueRow({ app, productName }: { app: BankApplication; productName: string }) {
  return (
    <li className="queue-row">
      <div className="queue-main">
        <Link to={`/bank/applications/${app.id}`} className="app-row-title">
          {app.company_name ?? "Компания не указана"}
        </Link>
        <span className="small muted">{productName}</span>
      </div>
      <span className="num queue-amount">{formatAmount(app.draft_fields?.requested_amount)}</span>
      <StatusBadge status={app.status} />
      <span className={`queue-action small${needsOfficer(app) ? " queue-action-due" : " muted"}`}>
        {needsOfficer(app) ? "Нужно действие" : "Без действия"}
      </span>
      <span className="queue-time small muted num" title={formatDateTime(app.updated_at)}>
        {formatWaiting(app.updated_at)}
      </span>
    </li>
  );
}

export function QueuePage() {
  const [params, setParams] = useSearchParams();
  const products = useProducts();
  const filters: BankQueueFilters = {
    status: (params.get("status") as ApplicationStatus | null) ?? undefined,
    product_code: (params.get("product") as ProductCode | null) ?? undefined,
    limit: PAGE_LIMIT,
  };
  // Фильтрация на сервере: в браузер приходят только строки текущего фильтра.
  const queue = useQuery({
    queryKey: queryKeys.bankQueue(filters),
    queryFn: ({ signal }) => api.bankQueue(filters, { signal }),
    refetchInterval: 10_000,
    placeholderData: (previous) => previous,
  });

  function setFilter(key: "status" | "product", value: string) {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value);
    else next.delete(key);
    setParams(next, { replace: true });
  }

  const items = queue.data ?? [];
  const filtered = Boolean(filters.status || filters.product_code);
  const dueCount = items.filter(needsOfficer).length;

  return (
    <div className="stack-lg">
      <PageHeader title="Очередь заявок" meta={<span>Заявки всех клиентов; права проверяет сервер для каждой записи.</span>} />

      {queue.data ? (
        <section className="kpi-strip" aria-label="Сводка по очереди">
          <div className="kpi kpi-due">
            <span className="small">Ждут действия</span>
            <span className="kpi-value num">{dueCount}</span>
          </div>
          <div className="kpi">
            <span className="small">{filtered ? "В выбранном фильтре" : "Всего в очереди"}</span>
            <span className="kpi-value num">{items.length}</span>
          </div>
          <div className="kpi">
            <span className="small">Завершено выдачей</span>
            <span className="kpi-value num">{items.filter((app) => app.status === "COMPLETED").length}</span>
          </div>
        </section>
      ) : null}

      <div className="filters">
        <Field label="Статус">
          {(control) => (
            <select {...control} className="select" value={filters.status ?? ""} onChange={(e) => setFilter("status", e.target.value)}>
              <option value="">Все статусы</option>
              {ALL_STATUSES.map((status) => (
                <option key={status} value={status}>
                  {statusLabel(status)}
                </option>
              ))}
            </select>
          )}
        </Field>
        <Field label="Продукт">
          {(control) => (
            <select
              {...control}
              className="select"
              value={filters.product_code ?? ""}
              onChange={(e) => setFilter("product", e.target.value)}
            >
              <option value="">Все продукты</option>
              {(products.data ?? []).map((product) => (
                <option key={product.code} value={product.code}>
                  {product.title}
                </option>
              ))}
            </select>
          )}
        </Field>
        {filtered ? (
          <Button variant="ghost" onClick={() => setParams(new URLSearchParams(), { replace: true })}>
            Сбросить фильтры
          </Button>
        ) : null}
      </div>

      <Panel
        title="Заявки"
        aside={
          items.length >= PAGE_LIMIT ? <span className="small muted">Показаны первые {PAGE_LIMIT}</span> : null
        }
      >
        {queue.isPending ? (
          <LoadingBlock rows={5} label="Загружаем очередь" />
        ) : queue.isError ? (
          <ErrorBlock error={queue.error} onRetry={() => void queue.refetch()} />
        ) : items.length === 0 ? (
          <EmptyBlock
            action={
              filtered ? (
                <Button onClick={() => setParams(new URLSearchParams(), { replace: true })}>Показать все заявки</Button>
              ) : undefined
            }
          >
            {filtered
              ? "По выбранным фильтрам заявок нет."
              : "Заявок пока нет. Они появятся здесь, когда клиенты отправят заявки на проверку."}
          </EmptyBlock>
        ) : (
          <>
            <div className="queue-head small muted" aria-hidden="true">
              <span>Компания и продукт</span>
              <span className="queue-amount">Сумма</span>
              <span>Статус</span>
              <span>Действие</span>
              <span className="queue-time">Без изменений</span>
            </div>
            <ul className="queue-list" aria-busy={queue.isFetching || undefined}>
              {items.map((app) => (
                <QueueRow key={app.id} app={app} productName={productTitle(products.data, app.product_code)} />
              ))}
            </ul>
          </>
        )}
      </Panel>
    </div>
  );
}
