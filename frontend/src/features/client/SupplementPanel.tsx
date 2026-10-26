import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../../api/endpoints";
import { isApiError } from "../../api/errors";
import { queryKeys } from "../../api/queryClient";
import type { ClientApplication, Product, UploadedDocument } from "../../api/types";
import { useCommand } from "../../api/useCommand";
import { Button } from "../../components/Button";
import { Panel } from "../../components/Layout";
import { ErrorBlock, LoadingBlock, Notice } from "../../components/States";
import { formatTime } from "../../shared/dates";
import { EDITABLE_FIELDS, FIELD_LABELS, serverFieldErrors, type EditableField } from "./draftForm";
import { DraftFieldInputs } from "./DraftFieldInputs";
import { DocumentsUpload } from "./DocumentsUpload";
import { documentTitle } from "./policy";
import { isConflict, useApplicationCommandEffects } from "./commandEffects";
import { UnsavedChangesGuard } from "./UnsavedChangesGuard";
import { useDraftEditing } from "./useDraftEditing";

function isEditableField(field: string): field is EditableField {
  return (EDITABLE_FIELDS as readonly string[]).includes(field);
}

function SupplementForm({
  app,
  product,
  requestId,
  fields,
  documentKinds,
}: {
  app: ClientApplication;
  product: Product | undefined;
  requestId: string;
  fields: EditableField[];
  documentKinds: string[];
}) {
  const effects = useApplicationCommandEffects(app.id);
  // В NEEDS_INFO меняются только запрошенные поля: остальные не попадают в PATCH.
  const editing = useDraftEditing(app, fields);
  const [uploaded, setUploaded] = useState<Record<string, UploadedDocument>>({});

  const resubmit = useCommand((_: void, ctx) => api.resubmit(app.id, app.version, requestId, ctx), {
    ...effects,
    onError: (error) => {
      effects.onError(error);
      if (isApiError(error) && error.kind === "validation") editing.setServerErrors(serverFieldErrors(error.fieldErrors));
    },
  });
  const missingDocs = documentKinds.filter((kind) => !uploaded[kind]);
  const emptyFields = fields.filter((field) => editing.values[field] === null);

  return (
    <>
      <UnsavedChangesGuard when={editing.dirty && !resubmit.isPending} />
      {fields.length ? (
        <div className="stack">
          <DraftFieldInputs
            fields={fields}
            values={editing.values}
            errors={editing.fieldErrors}
            product={product}
            onChange={editing.setField}
            onFormatError={editing.setFormatError}
          />
          <div className="row">
            <Button
              onClick={() => editing.save.mutate()}
              disabled={!editing.dirty || editing.hasFormatErrors}
              busy={editing.save.isPending}
              busyLabel="Сохраняем…"
            >
              Сохранить уточнения
            </Button>
            <span className="small muted" role="status">
              {editing.dirty
                ? "Есть несохранённые изменения"
                : editing.savedAt
                  ? `Сохранено на сервере в ${formatTime(editing.savedAt)}`
                  : null}
            </span>
          </div>
          {editing.save.isError ? (
            isConflict(editing.save.error) ? (
              <Notice tone="warning" title="Заявка изменилась.">
                <div>
                  <Button onClick={() => void editing.reloadFromServer()}>Загрузить актуальную версию</Button>
                </div>
              </Notice>
            ) : (
              <ErrorBlock error={editing.save.error} title="Уточнения не сохранены." />
            )
          ) : null}
        </div>
      ) : null}

      {documentKinds.length ? (
        <DocumentsUpload
          app={app}
          kinds={documentKinds}
          uploaded={uploaded}
          onUploaded={(doc) => setUploaded((current) => ({ ...current, [doc.kind]: doc }))}
        />
      ) : null}

      {resubmit.isError ? (
        isConflict(resubmit.error) ? (
          <Notice tone="warning" title="Данные изменились.">
            Мы обновили заявку. Проверьте уточнения и отправьте снова.
          </Notice>
        ) : (
          <ErrorBlock error={resubmit.error} title="Уточнения не отправлены." />
        )
      ) : null}
      <div className="stack-tight">
        <div>
          <Button
            variant="primary"
            disabled={editing.dirty || emptyFields.length > 0 || missingDocs.length > 0}
            busy={resubmit.isPending}
            busyLabel="Отправляем…"
            onClick={() => resubmit.mutate()}
          >
            Отправить уточнения
          </Button>
        </div>
        <p className="small muted">
          {editing.dirty
            ? "Сначала сохраните изменения."
            : emptyFields.length || missingDocs.length
              ? "Заполните запрошенные поля и загрузите документы."
              : "Будет создана новая ревизия, и проверка запустится заново."}
        </p>
      </div>
    </>
  );
}

export function SupplementPanel({ app, product }: { app: ClientApplication; product: Product | undefined }) {
  const infoRequest = useQuery({
    queryKey: queryKeys.infoRequest(app.id),
    queryFn: ({ signal }) => api.infoRequest(app.id, { signal }),
  });

  return (
    <Panel title="Нужны дополнительные сведения" id="info-request">
      {infoRequest.isPending ? (
        <LoadingBlock rows={4} label="Загружаем запрос" />
      ) : infoRequest.isError ? (
        <ErrorBlock error={infoRequest.error} onRetry={() => void infoRequest.refetch()} />
      ) : !infoRequest.data ? (
        <Notice tone="warning">Активного запроса нет. Обновите страницу — статус мог измениться.</Notice>
      ) : (
        <>
          <blockquote className="request-message">{infoRequest.data.message}</blockquote>
          <p className="small muted">
            Запрошено:{" "}
            {[
              ...infoRequest.data.fields.map((field) => FIELD_LABELS[field as keyof typeof FIELD_LABELS] ?? field),
              ...infoRequest.data.document_kinds.map(documentTitle),
            ].join(", ")}
          </p>
          <SupplementForm
            app={app}
            product={product}
            requestId={infoRequest.data.id}
            fields={infoRequest.data.fields.filter(isEditableField)}
            documentKinds={infoRequest.data.document_kinds}
          />
        </>
      )}
    </Panel>
  );
}
