import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router";
import { api } from "../../api/endpoints";
import { queryKeys } from "../../api/queryClient";
import { useSession } from "../../api/session";
import type { ClientApplication, Product } from "../../api/types";
import { ButtonLink } from "../../components/Button";
import { EmptyBlock, ErrorBlock, LoadingBlock } from "../../components/States";
import { StatusBadge } from "../../components/StatusBadge";
import { Stepper } from "../../components/Stepper";
import { formatDateTime } from "../../shared/dates";
import { formatAmount } from "../../shared/money";
import { productTitle, useProducts } from "./products";

export function applicationPath(app: Pick<ClientApplication, "id" | "status">): string {
  return app.status === "DRAFT" ? `/applications/${app.id}/edit` : `/applications/${app.id}`;
}

function ApplicationCard({ app, products }: { app: ClientApplication; products: Product[] | undefined }) {
  const amount = app.draft_fields?.requested_amount ?? null;
  return (
    <li className="app-card">
      <div className="app-card-top">
        <Link to={applicationPath(app)} className="app-row-title">
          {productTitle(products, app.product_code)}
        </Link>
        <StatusBadge status={app.status} />
      </div>
      <div className="app-card-amount num">
        {amount ? formatAmount(amount) : <span className="app-card-empty">Сумма не указана</span>}
      </div>
      <Stepper status={app.status} compact />
      <div className="app-card-foot small muted">
        <span>{app.next_action}</span>
        <time className="num" dateTime={app.updated_at}>
          {formatDateTime(app.updated_at)}
        </time>
      </div>
    </li>
  );
}

function ApplicationList({ items, products }: { items: ClientApplication[]; products: Product[] | undefined }) {
  return (
    <ul className="app-grid">
      {items.map((app) => (
        <ApplicationCard key={app.id} app={app} products={products} />
      ))}
    </ul>
  );
}

export function HomePage() {
  const { session } = useSession();
  const products = useProducts();
  const applications = useQuery({
    queryKey: queryKeys.applications,
    queryFn: ({ signal }) => api.listApplications({ signal }),
  });
  const company = session?.user.company;

  const items = applications.data ?? [];
  const needsAction = items.filter((app) => app.allowed_actions.length > 0);
  const others = items.filter((app) => app.allowed_actions.length === 0);

  return (
    <div className="stack-lg">
      <section className="promo">
        <div className="promo-copy">
          <p className="promo-company small">
            {company ? (
              <>
                {company.display_name}, <span className="num">{company.demo_registration_id}</span>
              </>
            ) : null}
          </p>
          <h1 className="promo-title">Финансирование для вашего бизнеса</h1>
          <p className="promo-lead">
            Подайте заявку, следите за каждым этапом и получите рассчитанные условия. Решение подтверждает
            специалист банка.
          </p>
          <ButtonLink to="/applications/new" variant="on-dark" size="large">
            Новая заявка
          </ButtonLink>
        </div>
        <div className="promo-stats" aria-label="Сводка по заявкам">
          <div>
            <span className="promo-stat-value num">{applications.isSuccess ? items.length : "—"}</span>
            <span className="small">всего заявок</span>
          </div>
          <div>
            <span className="promo-stat-value num">{applications.isSuccess ? needsAction.length : "—"}</span>
            <span className="small">ждут вашего действия</span>
          </div>
        </div>
      </section>

      {applications.isPending ? (
        <section className="stack" aria-label="Заявки">
          <LoadingBlock rows={4} label="Загружаем заявки" />
        </section>
      ) : applications.isError ? (
        <ErrorBlock error={applications.error} onRetry={() => void applications.refetch()} />
      ) : items.length === 0 ? (
        <EmptyBlock action={<ButtonLink to="/applications/new" variant="primary">Создать первую заявку</ButtonLink>}>
          У компании пока нет заявок. Выберите продукт, заполните сведения и отправьте заявку на проверку.
        </EmptyBlock>
      ) : (
        <>
          <section className="stack" aria-labelledby="due-title">
            <div className="section-head">
              <h2 id="due-title">Требуют вашего действия</h2>
              <span className="tag num">{needsAction.length}</span>
            </div>
            {needsAction.length ? (
              <ApplicationList items={needsAction} products={products.data} />
            ) : (
              <p className="muted">Сейчас от вас ничего не требуется. Статусы остальных заявок ниже.</p>
            )}
          </section>
          {others.length ? (
            <section className="stack" aria-labelledby="rest-title">
              <div className="section-head">
                <h2 id="rest-title">В работе и завершённые</h2>
                <span className="tag num">{others.length}</span>
              </div>
              <ApplicationList items={others} products={products.data} />
            </section>
          ) : null}
        </>
      )}
    </div>
  );
}
