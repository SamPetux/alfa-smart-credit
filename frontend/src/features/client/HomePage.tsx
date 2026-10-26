import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router";
import { api } from "../../api/endpoints";
import { queryKeys } from "../../api/queryClient";
import { useSession } from "../../api/session";
import type { ClientApplication, Product } from "../../api/types";
import { ButtonLink } from "../../components/Button";
import { Icon } from "../../components/Icon";
import { PageHeader, Panel } from "../../components/Layout";
import { EmptyBlock, ErrorBlock, LoadingBlock } from "../../components/States";
import { StatusBadge } from "../../components/StatusBadge";
import { formatDateTime } from "../../shared/dates";
import { formatAmount } from "../../shared/money";
import { productTitle, useProducts } from "./products";

export function applicationPath(app: Pick<ClientApplication, "id" | "status">): string {
  return app.status === "DRAFT" ? `/applications/${app.id}/edit` : `/applications/${app.id}`;
}

function ApplicationRow({ app, products }: { app: ClientApplication; products: Product[] | undefined }) {
  const amount = app.draft_fields?.requested_amount ?? null;
  return (
    <li className="app-row">
      <div className="app-row-main">
        <Link to={applicationPath(app)} className="app-row-title">
          {productTitle(products, app.product_code)}
        </Link>
        <span className="small muted">Следующий шаг: {app.next_action}</span>
      </div>
      <span className="app-row-amount num">{amount ? formatAmount(amount) : <span className="muted">сумма не указана</span>}</span>
      <StatusBadge status={app.status} />
      <time className="app-row-date small muted num" dateTime={app.updated_at}>
        {formatDateTime(app.updated_at)}
      </time>
      <Icon name="chevron" />
    </li>
  );
}

function ApplicationList({ items, products }: { items: ClientApplication[]; products: Product[] | undefined }) {
  return (
    <ul className="app-list">
      {items.map((app) => (
        <ApplicationRow key={app.id} app={app} products={products} />
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
      <PageHeader
        title="Мои заявки"
        meta={
          company ? (
            <>
              <span>{company.display_name}</span>
              <span>
                Демонстрационный идентификатор компании:{" "}
                <span className="num nowrap">{company.demo_registration_id}</span>
              </span>
            </>
          ) : null
        }
        actions={
          <ButtonLink to="/applications/new" variant="primary">
            Новая заявка
          </ButtonLink>
        }
      />

      {applications.isPending ? (
        <Panel title="Заявки">
          <LoadingBlock rows={4} label="Загружаем заявки" />
        </Panel>
      ) : applications.isError ? (
        <Panel title="Заявки">
          <ErrorBlock error={applications.error} onRetry={() => void applications.refetch()} />
        </Panel>
      ) : items.length === 0 ? (
        <Panel title="Заявки">
          <EmptyBlock action={<ButtonLink to="/applications/new">Создать первую заявку</ButtonLink>}>
            У компании пока нет заявок. Выберите продукт, заполните сведения и отправьте заявку на проверку.
          </EmptyBlock>
        </Panel>
      ) : (
        <>
          <Panel title="Требуют вашего действия" aside={<span className="small muted num">{needsAction.length}</span>}>
            {needsAction.length ? (
              <ApplicationList items={needsAction} products={products.data} />
            ) : (
              <p className="muted">Сейчас от вас ничего не требуется. Статусы остальных заявок — ниже.</p>
            )}
          </Panel>
          {others.length ? (
            <Panel title="В работе и завершённые" aside={<span className="small muted num">{others.length}</span>}>
              <ApplicationList items={others} products={products.data} />
            </Panel>
          ) : null}
        </>
      )}
    </div>
  );
}
