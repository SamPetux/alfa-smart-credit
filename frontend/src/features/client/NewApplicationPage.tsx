import { useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router";
import { api } from "../../api/endpoints";
import { queryKeys } from "../../api/queryClient";
import type { ProductCode } from "../../api/types";
import { useCommand } from "../../api/useCommand";
import { Button } from "../../components/Button";
import { PageHeader, Panel } from "../../components/Layout";
import { ErrorBlock, LoadingBlock } from "../../components/States";
import { formatAmount } from "../../shared/money";
import { documentTitle, requiredDocuments } from "./policy";
import { useProducts } from "./products";

export function NewApplicationPage() {
  const products = useProducts();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [selected, setSelected] = useState<ProductCode | null>(null);

  const create = useCommand((code: ProductCode, ctx) => api.createApplication(code, ctx), {
    onSuccess: (app) => {
      queryClient.setQueryData(queryKeys.application(app.id), app);
      void queryClient.invalidateQueries({ queryKey: queryKeys.applications, exact: true });
      navigate(`/applications/${app.id}/edit`, { replace: true });
    },
  });

  function submit(event: FormEvent) {
    event.preventDefault();
    if (selected) create.mutate(selected);
  }

  return (
    <div className="stack-lg">
      <PageHeader title="Новая заявка" backTo="/applications" backLabel="Мои заявки" />
      <form onSubmit={submit} className="stack-lg">
        <Panel title="Выберите продукт">
          <p className="muted">
            Условия учебные и не являются предложением банка. Решение принимает сотрудник после проверки.
          </p>
          {products.isPending ? (
            <LoadingBlock rows={3} label="Загружаем продукты" />
          ) : products.isError ? (
            <ErrorBlock error={products.error} onRetry={() => void products.refetch()} />
          ) : (
            <fieldset className="product-options">
              <legend className="visually-hidden">Продукт</legend>
              {products.data.map((product) => (
                <label key={product.code} className="product-option">
                  <input
                    type="radio"
                    name="product"
                    value={product.code}
                    checked={selected === product.code}
                    onChange={() => setSelected(product.code)}
                  />
                  <span className="product-option-body">
                    <span className="product-option-title">{product.title}</span>
                    {product.description ? <span className="small muted">{product.description}</span> : null}
                    <span className="product-facts small">
                      <span>
                        Сумма{" "}
                        <span className="num nowrap">
                          {formatAmount(product.amount_min)} – {formatAmount(product.amount_max)}
                        </span>
                      </span>
                      <span>
                        Срок <span className="num">{product.term_months.join(", ")}</span> мес.
                      </span>
                      <span>Документы: {requiredDocuments(product.code).map(documentTitle).join(", ")}</span>
                    </span>
                  </span>
                </label>
              ))}
            </fieldset>
          )}
        </Panel>
        {create.isError ? <ErrorBlock error={create.error} title="Черновик не создан." /> : null}
        <div className="row">
          <Button type="submit" variant="primary" disabled={!selected} busy={create.isPending} busyLabel="Создаём черновик…">
            Создать черновик
          </Button>
          {!selected ? <span className="small muted">Сначала выберите продукт</span> : null}
        </div>
      </form>
    </div>
  );
}
