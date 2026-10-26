import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Navigate, useNavigate, useParams } from "react-router";
import { api } from "../../api/endpoints";
import { isApiError } from "../../api/errors";
import { queryKeys } from "../../api/queryClient";
import { useSession } from "../../api/session";
import type { ClientApplication, Product, UploadedDocument } from "../../api/types";
import { useCommand } from "../../api/useCommand";
import { Button } from "../../components/Button";
import { ConfirmDialog } from "../../components/ConfirmDialog";
import { KeyValueList, PageHeader, Panel } from "../../components/Layout";
import { ErrorBlock, LoadingBlock, Notice } from "../../components/States";
import { StatusBadge } from "../../components/StatusBadge";
import { formatTime } from "../../shared/dates";
import { formatAmount } from "../../shared/money";
import { COMPANY_FORMS, FIELD_LABELS, serverFieldErrors, validateForSubmit, type FieldErrors } from "./draftForm";
import { DraftFieldInputs } from "./DraftFieldInputs";
import { DocumentsUpload } from "./DocumentsUpload";
import { documentTitle, requiredDocuments } from "./policy";
import { productTitle, useProducts } from "./products";
import { useClientApplication } from "./queries";
import { UnsavedChangesGuard } from "./UnsavedChangesGuard";
import { useDraftEditing } from "./useDraftEditing";

const SECTION_OF_FIELD: Record<string, string> = {
  requested_amount: "amount",
  term_months: "amount",
  company_form: "company",
  monthly_revenue: "finance",
  monthly_operating_costs: "finance",
  declared_monthly_debt_payments: "finance",
  documents: "documents",
};

const PURPOSE_LABELS: Record<string, string> = {
  working_capital: "Пополнение оборотных средств",
  equipment: "Покупка оборудования",
};

function SaveStatus({ dirty, savedAt, updatedAt }: { dirty: boolean; savedAt: Date | null; updatedAt: string }) {
  if (dirty) return <span className="save-status save-status-dirty">Есть несохранённые изменения</span>;
  const stamp = savedAt ?? new Date(updatedAt);
  return (
    <span className="save-status" role="status">
      Сохранено на сервере в <span className="num">{formatTime(stamp)}</span>
    </span>
  );
}

function DraftEditor({ app, product, products }: { app: ClientApplication; product: Product | undefined; products: Product[] | undefined }) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { session } = useSession();
  const editing = useDraftEditing(app);
  const [uploaded, setUploaded] = useState<Record<string, UploadedDocument>>({});
  const [confirming, setConfirming] = useState(false);
  const [submitErrors, setSubmitErrors] = useState<FieldErrors>({});

  const submit = useCommand((_: void, ctx) => api.submit(app.id, app.version, ctx), {
    onSuccess: (updated) => {
      queryClient.setQueryData(queryKeys.application(app.id), updated);
      void queryClient.invalidateQueries({ queryKey: queryKeys.applications, exact: true });
      navigate(`/applications/${app.id}`, { replace: true });
    },
    onError: (error) => {
      setConfirming(false);
      if (isApiError(error) && error.kind === "validation") setSubmitErrors(serverFieldErrors(error.fieldErrors));
    },
  });

  const docKinds = app.product_code ? requiredDocuments(app.product_code) : [];
  const clientErrors = validateForSubmit(editing.values, product);
  const errors: FieldErrors = { ...submitErrors, ...editing.fieldErrors };
  const missingDocs = docKinds.filter((kind) => !uploaded[kind]);
  const blockers = Object.keys(clientErrors).length;
  const conflict = isApiError(editing.save.error) && editing.save.error.kind === "conflict";

  const setField: typeof editing.setField = (field, value) => {
    editing.setField(field, value);
    setSubmitErrors((current) => ({ ...current, [field]: undefined }));
  };

  function attemptSubmit() {
    if (blockers) {
      setSubmitErrors(clientErrors);
      return;
    }
    setConfirming(true);
  }

  return (
    <div className="stack-lg">
      <UnsavedChangesGuard when={editing.dirty && !submit.isPending} />
      <PageHeader
        title={productTitle(products, app.product_code)}
        backTo="/applications"
        backLabel="Мои заявки"
        meta={
          <>
            <StatusBadge status={app.status} />
            <SaveStatus dirty={editing.dirty} savedAt={editing.savedAt} updatedAt={app.updated_at} />
          </>
        }
        actions={
          <Button
            variant="secondary"
            onClick={() => editing.save.mutate()}
            disabled={!editing.dirty || editing.hasFormatErrors}
            busy={editing.save.isPending}
            busyLabel="Сохраняем…"
          >
            Сохранить черновик
          </Button>
        }
      />

      {conflict ? (
        <Notice tone="warning" title="Черновик изменился в другой вкладке или сессии.">
          <p>Ваши правки не сохранены. Загрузите актуальную версию и внесите изменения заново.</p>
          <div>
            <Button onClick={() => void editing.reloadFromServer()}>Загрузить актуальную версию</Button>
          </div>
        </Notice>
      ) : editing.save.isError ? (
        <ErrorBlock error={editing.save.error} title="Черновик не сохранён." />
      ) : null}

      <div className="editor-grid">
        <div className="stack-lg">
          <Panel title="Цель и продукт" id="purpose">
            <KeyValueList
              items={[
                { label: "Продукт", value: productTitle(products, app.product_code) },
                {
                  label: FIELD_LABELS.purpose,
                  value: PURPOSE_LABELS[app.draft_fields?.purpose ?? ""] ?? "—",
                },
              ]}
            />
            <p className="small muted">Чтобы выбрать другой продукт, создайте новую заявку. Этот черновик сохранится.</p>
          </Panel>

          <Panel title="Сумма и срок" id="amount">
            <DraftFieldInputs
              fields={["requested_amount", "term_months"]}
              values={editing.values}
              errors={errors}
              product={product}
              onChange={setField}
              onFormatError={editing.setFormatError}
            />
          </Panel>

          <Panel title="Сведения о компании" id="company">
            <KeyValueList
              items={[
                { label: "Компания", value: session?.user.company?.display_name ?? "—" },
                {
                  label: "Демонстрационный идентификатор компании",
                  value: session?.user.company?.demo_registration_id ?? "—",
                  numeric: true,
                },
              ]}
            />
            <p className="small muted">Название и идентификатор сервер берёт из профиля; изменить их в заявке нельзя.</p>
            <DraftFieldInputs
              fields={["company_form"]}
              values={editing.values}
              errors={errors}
              product={product}
              onChange={setField}
              onFormatError={editing.setFormatError}
            />
          </Panel>

          <Panel title="Финансовые показатели" id="finance">
            <p className="small muted">Данные клиента. Сведения о долгах сверяются с демонстрационным кредитным бюро.</p>
            <DraftFieldInputs
              fields={["monthly_revenue", "monthly_operating_costs", "declared_monthly_debt_payments"]}
              values={editing.values}
              errors={errors}
              product={product}
              onChange={setField}
              onFormatError={editing.setFormatError}
            />
          </Panel>

          <Panel title="Документы" id="documents">
            <DocumentsUpload
              app={app}
              kinds={docKinds}
              error={errors.documents}
              uploaded={uploaded}
              onUploaded={(doc) => setUploaded((current) => ({ ...current, [doc.kind]: doc }))}
            />
          </Panel>
        </div>

        <aside className="editor-aside">
          <Panel title="Проверка и отправка" id="review">
            <KeyValueList
              items={[
                { label: FIELD_LABELS.requested_amount, value: formatAmount(editing.values.requested_amount), numeric: true },
                {
                  label: FIELD_LABELS.term_months,
                  value: editing.values.term_months ? `${editing.values.term_months} мес.` : "—",
                  numeric: true,
                },
                {
                  label: "Форма",
                  value: COMPANY_FORMS.find((form) => form.value === editing.values.company_form)?.label ?? "—",
                },
                { label: "Выручка", value: formatAmount(editing.values.monthly_revenue), numeric: true },
                { label: "Расходы", value: formatAmount(editing.values.monthly_operating_costs), numeric: true },
                { label: "Платежи по кредитам", value: formatAmount(editing.values.declared_monthly_debt_payments), numeric: true },
              ]}
            />
            {blockers || missingDocs.length ? (
              <div className="review-todo small">
                <p className="muted">Перед отправкой:</p>
                <ul>
                  {Object.entries(clientErrors).map(([field, message]) => (
                    <li key={field}>
                      <a href={`#${SECTION_OF_FIELD[field] ?? "amount"}`}>
                        {FIELD_LABELS[field as keyof typeof FIELD_LABELS]}
                      </a>
                      : {message.toLowerCase()}
                    </li>
                  ))}
                  {missingDocs.map((kind) => (
                    <li key={kind}>
                      <a href="#documents">{documentTitle(kind)}</a>: загрузите файл
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
            {editing.dirty ? <p className="small muted">Сохраните изменения, чтобы отправить заявку.</p> : null}
            {submit.isError && !(isApiError(submit.error) && submit.error.kind === "validation") ? (
              <ErrorBlock error={submit.error} title="Заявка не отправлена." />
            ) : null}
            {submit.isError && isApiError(submit.error) && submit.error.kind === "validation" ? (
              <Notice tone="error" title="Сервер не принял заявку.">
                <p>{submit.error.message}. Исправьте отмеченные поля.</p>
              </Notice>
            ) : null}
            <Button variant="primary" onClick={attemptSubmit} disabled={editing.dirty || submit.isPending}>
              Отправить заявку
            </Button>
          </Panel>
        </aside>
      </div>

      <ConfirmDialog
        open={confirming}
        title="Отправить заявку на проверку?"
        description="После отправки данные зафиксируются в ревизии и изменить их можно будет только по запросу специалиста. Проверка выполняется на демонстрационных источниках."
        confirmLabel="Отправить"
        busy={submit.isPending}
        onConfirm={() => submit.mutate()}
        onCancel={() => setConfirming(false)}
      />
    </div>
  );
}

export function DraftEditorPage() {
  const { id = "" } = useParams();
  const application = useClientApplication(id);
  const products = useProducts();

  if (application.isPending) {
    return <LoadingBlock rows={6} label="Загружаем черновик" />;
  }
  if (application.isError) {
    return (
      <div className="stack-lg">
        <PageHeader title="Черновик" backTo="/applications" backLabel="Мои заявки" />
        <ErrorBlock error={application.error} onRetry={() => void application.refetch()} />
      </div>
    );
  }
  if (application.data.status !== "DRAFT") {
    return <Navigate to={`/applications/${id}`} replace />;
  }
  const product = products.data?.find((item) => item.code === application.data.product_code);
  return <DraftEditor app={application.data} product={product} products={products.data} />;
}
