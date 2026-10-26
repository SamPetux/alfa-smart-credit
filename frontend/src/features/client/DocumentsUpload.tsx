import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../../api/endpoints";
import { queryKeys } from "../../api/queryClient";
import type { ClientApplication, UploadedDocument } from "../../api/types";
import { useCommand } from "../../api/useCommand";
import { Button } from "../../components/Button";
import { Field } from "../../components/Field";
import { Icon } from "../../components/Icon";
import { ErrorBlock } from "../../components/States";
import { DOCUMENT_LABELS, documentTitle } from "./policy";

const MAX_BYTES = 10 * 1024 * 1024;
const ACCEPT = ".pdf,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg";

function checkFile(file: File): string | null {
  if (file.size > MAX_BYTES) return "Файл больше 10 МБ.";
  if (!/\.(pdf|png|jpe?g)$/i.test(file.name)) return "Подходят только PDF, PNG или JPEG.";
  return null;
}

function DocumentSlot({
  app,
  kind,
  uploaded,
  error: externalError,
  onUploaded,
}: {
  app: ClientApplication;
  kind: string;
  uploaded: UploadedDocument | undefined;
  error?: string;
  onUploaded: (doc: UploadedDocument, fileName: string) => void;
}) {
  const queryClient = useQueryClient();
  const [file, setFile] = useState<File | null>(null);
  const [localError, setLocalError] = useState<string | null>(null);
  const [inputKey, setInputKey] = useState(0);

  const upload = useCommand(
    (selected: File, ctx) => api.uploadDocument(app.id, { kind, file: selected, expectedVersion: app.version }, ctx),
    {
      onSuccess: (doc, selected) => {
        // Загрузка увеличивает version заявки: следующие команды должны её учитывать.
        queryClient.setQueryData<ClientApplication>(queryKeys.application(app.id), (current) =>
          current ? { ...current, version: doc.version } : current,
        );
        onUploaded(doc, selected.name);
        setFile(null);
        setInputKey((key) => key + 1);
      },
    },
  );

  return (
    <div className="doc-slot">
      <Field
        label={documentTitle(kind)}
        hint={DOCUMENT_LABELS[kind]?.hint ?? "PDF, PNG или JPEG до 10 МБ."}
        error={localError ?? externalError}
        required
        tag={
          uploaded ? (
            <span className="tag tag-done">
              <Icon name="check" /> Загружен
            </span>
          ) : (
            <span className="tag">Не загружен</span>
          )
        }
      >
        {(control) => (
          <div className="file-picker">
            <input
              key={inputKey}
              {...control}
              type="file"
              className="file-picker-input"
              accept={ACCEPT}
              onChange={(event) => {
                const next = event.target.files?.[0] ?? null;
                setLocalError(next ? checkFile(next) : null);
                setFile(next);
              }}
            />
            <span className="btn btn-secondary file-picker-button" aria-hidden="true">
              Выбрать файл
            </span>
            <span className="file-picker-name small muted" aria-hidden="true">
              {file ? file.name : "Файл не выбран"}
            </span>
          </div>
        )}
      </Field>
      {uploaded ? (
        <p className="small muted">
          Загружено в этой сессии. Содержание файла не проверяется — сотрудник видит только факт загрузки.
        </p>
      ) : null}
      <div className="row">
        <Button
          onClick={() => file && upload.mutate(file)}
          disabled={!file || Boolean(localError)}
          busy={upload.isPending}
          busyLabel="Загружаем…"
        >
          {uploaded ? "Загрузить новую версию" : "Загрузить"}
        </Button>
      </div>
      {upload.isError ? <ErrorBlock error={upload.error} title="Файл не загружен." /> : null}
    </div>
  );
}

/**
 * Загрузка демодокументов. API не отдаёт список загруженных файлов, поэтому отметка
 * «Загружен» живёт до перезагрузки страницы; итоговую полноту проверяет submit.
 */
export function DocumentsUpload({
  app,
  kinds,
  error,
  uploaded,
  onUploaded,
}: {
  app: ClientApplication;
  kinds: string[];
  error?: string;
  uploaded: Record<string, UploadedDocument>;
  onUploaded: (doc: UploadedDocument) => void;
}) {
  return (
    <div className="stack">
      {kinds.map((kind) => (
        <DocumentSlot
          key={kind}
          app={app}
          kind={kind}
          uploaded={uploaded[kind]}
          error={!uploaded[kind] && error?.includes(kind) ? "Документ нужен для отправки" : undefined}
          onUploaded={(doc) => onUploaded(doc)}
        />
      ))}
    </div>
  );
}
