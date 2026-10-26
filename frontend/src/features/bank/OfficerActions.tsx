import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../../api/endpoints";
import { isApiError } from "../../api/errors";
import { queryKeys } from "../../api/queryClient";
import type { AllowedAction, BankApplication } from "../../api/types";
import { useCommand } from "../../api/useCommand";
import { Button } from "../../components/Button";
import { ConfirmDialog } from "../../components/ConfirmDialog";
import { Field } from "../../components/Field";
import { KeyValueList, Panel } from "../../components/Layout";
import { ErrorBlock, Notice } from "../../components/States";
import { formatAmount, formatRate } from "../../shared/money";
import { EDITABLE_FIELDS, FIELD_LABELS } from "../client/draftForm";
import { documentTitle, requiredDocuments } from "../client/policy";
import { REASON_CODES, reasonText } from "./labels";

type DialogKind = "request" | "approve" | "reject" | "retry-checks" | "retry-disbursement";

/**
 * Снимок того, что видел сотрудник при открытии диалога. Команда уходит с этими
 * version/run/candidate: если заявка изменилась, сервер вернёт 409, а не применит
 * решение к новым данным.
 */
interface Snapshot {
  version: number;
  runId: string | null;
  candidateHash: string | null;
}

function useOfficerCommandEffects(id: string, onDone: () => void) {
  const queryClient = useQueryClient();
  return {
    onSuccess: (updated: BankApplication) => {
      queryClient.setQueryData(queryKeys.bankApplication(id), updated);
      void queryClient.invalidateQueries({ queryKey: ["bank", "queue"] });
      onDone();
    },
    onError: (error: Error) => {
      if (isApiError(error) && error.kind === "conflict") {
        void queryClient.invalidateQueries({ queryKey: queryKeys.bankApplication(id) });
        onDone();
      }
    },
  };
}

export function OfficerActions({ app }: { app: BankApplication }) {
  const [dialog, setDialog] = useState<DialogKind | null>(null);
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [conflict, setConflict] = useState(false);
  const [fields, setFields] = useState<string[]>([]);
  const [docKinds, setDocKinds] = useState<string[]>([]);
  const [message, setMessage] = useState("");
  const [reasonCode, setReasonCode] = useState("");
  const [comment, setComment] = useState("");

  const close = () => setDialog(null);
  const effects = useOfficerCommandEffects(app.id, close);
  const withConflict = {
    ...effects,
    onError: (error: Error) => {
      if (isApiError(error) && error.kind === "conflict") setConflict(true);
      effects.onError(error);
    },
    onSuccess: (updated: BankApplication) => {
      setConflict(false);
      effects.onSuccess(updated);
    },
  };

  const requestInfo = useCommand(
    (s: Snapshot, ctx) =>
      api.requestInfo(app.id, { expectedVersion: s.version, fields, documentKinds: docKinds, message: message.trim() }, ctx),
    withConflict,
  );
  const approve = useCommand(
    (s: Snapshot, ctx) =>
      api.approveOffer(app.id, { expectedVersion: s.version, runId: s.runId ?? "", candidateHash: s.candidateHash ?? "" }, ctx),
    withConflict,
  );
  const reject = useCommand(
    (s: Snapshot, ctx) =>
      api.reject(app.id, { expectedVersion: s.version, runId: s.runId ?? "", reasonCode, comment: comment.trim() }, ctx),
    withConflict,
  );
  const retryChecks = useCommand((s: Snapshot, ctx) => api.retryChecks(app.id, s.version, ctx), withConflict);
  const retryDisbursement = useCommand((s: Snapshot, ctx) => api.retryDisbursement(app.id, s.version, ctx), withConflict);

  function open(kind: DialogKind) {
    setSnapshot({
      version: app.version,
      runId: app.active_run_id ?? null,
      candidateHash: app.risk_summary?.candidate_hash ?? null,
    });
    setConflict(false);
    for (const command of [requestInfo, approve, reject, retryChecks, retryDisbursement]) command.reset();
    if (kind === "request") {
      setFields([]);
      setDocKinds([]);
      setMessage("");
    }
    if (kind === "reject") {
      setReasonCode(app.risk_summary?.recommendation === "REJECT" ? (app.risk_summary.reasons?.[0] ?? "") : "");
      setComment("");
    }
    setDialog(kind);
  }

  const allowed = new Set<AllowedAction>(app.allowed_actions);
  const candidate = app.risk_summary?.candidate;
  const nonConflictError = (error: Error | null) =>
    error && !(isApiError(error) && error.kind === "conflict") ? <ErrorBlock error={error} title="Действие не выполнено." /> : null;
  const productDocs = app.product_code ? requiredDocuments(app.product_code) : [];

  const toggle = (list: string[], value: string) => (list.includes(value) ? list.filter((v) => v !== value) : [...list, value]);

  return (
    <Panel title="Решение" id="actions">
      {conflict ? (
        <Notice tone="warning" title="Заявка изменилась, пока вы её рассматривали.">
          Действие не выполнено. Досье обновлено — проверьте актуальные данные и примите решение заново.
        </Notice>
      ) : null}
      {allowed.size === 0 ? (
        <p className="muted">Сейчас действий сотрудника не требуется.</p>
      ) : (
        <div className="stack">
          {allowed.has("APPROVE_OFFER") ? (
            <Button variant="primary" onClick={() => open("approve")}>
              Подтвердить рассчитанное предложение
            </Button>
          ) : null}
          {allowed.has("REQUEST_INFO") ? <Button onClick={() => open("request")}>Запросить уточнение</Button> : null}
          {allowed.has("REJECT") ? (
            <Button variant="danger" onClick={() => open("reject")}>
              Отказать с причиной
            </Button>
          ) : null}
          {allowed.has("RETRY_CHECKS") ? (
            <Button variant="primary" onClick={() => open("retry-checks")}>
              Перезапустить проверку
            </Button>
          ) : null}
          {allowed.has("RETRY_DISBURSEMENT") ? (
            <Button variant="primary" onClick={() => open("retry-disbursement")}>
              Повторить имитацию выдачи
            </Button>
          ) : null}
          {allowed.has("REJECT") && !allowed.has("APPROVE_OFFER") ? (
            <p className="small muted">
              Подтверждение условий недоступно: действующая рекомендация не содержит предложения. Свободный ввод суммы и
              ставки в P0 не предусмотрен.
            </p>
          ) : null}
        </div>
      )}

      <ConfirmDialog
        open={dialog === "approve"}
        title="Подтвердить предложение клиенту?"
        description="Клиент увидит эти условия и сможет принять или отклонить их. После подтверждения условия не редактируются."
        confirmLabel="Подтвердить условия"
        busy={approve.isPending}
        error={nonConflictError(approve.error)}
        onConfirm={() => snapshot && approve.mutate(snapshot)}
        onCancel={close}
      >
        {candidate ? (
          <KeyValueList
            items={[
              { label: "Сумма", value: formatAmount(candidate.amount), numeric: true },
              { label: "Срок", value: `${candidate.term_months ?? "—"} мес.`, numeric: true },
              { label: "Ставка", value: `${formatRate(candidate.annual_rate)} годовых`, numeric: true },
            ]}
          />
        ) : null}
      </ConfirmDialog>

      <ConfirmDialog
        open={dialog === "request"}
        title="Запросить уточнение"
        description="Клиент сможет изменить только отмеченные сведения и отправить новую ревизию."
        confirmLabel="Отправить запрос"
        busy={requestInfo.isPending}
        confirmDisabled={(fields.length === 0 && docKinds.length === 0) || message.trim() === ""}
        error={nonConflictError(requestInfo.error)}
        onConfirm={() => snapshot && requestInfo.mutate(snapshot)}
        onCancel={close}
      >
        <fieldset className="field">
          <legend className="field-label">Сведения</legend>
          <div className="stack-tight">
            {EDITABLE_FIELDS.filter((f) => f !== "term_months" && f !== "requested_amount").map((field) => (
              <label key={field} className="checkbox">
                <input type="checkbox" checked={fields.includes(field)} onChange={() => setFields((c) => toggle(c, field))} />
                <span>{FIELD_LABELS[field]}</span>
              </label>
            ))}
          </div>
        </fieldset>
        {productDocs.length ? (
          <fieldset className="field">
            <legend className="field-label">Документы</legend>
            <div className="stack-tight">
              {productDocs.map((kind) => (
                <label key={kind} className="checkbox">
                  <input type="checkbox" checked={docKinds.includes(kind)} onChange={() => setDocKinds((c) => toggle(c, kind))} />
                  <span>{documentTitle(kind)}</span>
                </label>
              ))}
            </div>
          </fieldset>
        ) : null}
        <Field label="Сообщение клиенту" required hint="Конкретно: что уточнить и почему.">
          {(control) => (
            <textarea {...control} className="textarea" value={message} onChange={(e) => setMessage(e.target.value)} />
          )}
        </Field>
        <p className="small muted">Сумму и срок клиент меняет только в новой заявке.</p>
      </ConfirmDialog>

      <ConfirmDialog
        open={dialog === "reject"}
        title="Отказать по заявке?"
        description="Решение окончательное. Клиент увидит причину в шаблонном объяснении."
        confirmLabel="Отказать"
        tone="danger"
        busy={reject.isPending}
        confirmDisabled={!reasonCode || comment.trim() === ""}
        error={nonConflictError(reject.error)}
        onConfirm={() => snapshot && reject.mutate(snapshot)}
        onCancel={close}
      >
        <Field label="Причина" required>
          {(control) => (
            <select {...control} className="select" value={reasonCode} onChange={(e) => setReasonCode(e.target.value)}>
              <option value="">Выберите причину</option>
              {REASON_CODES.map((code) => (
                <option key={code} value={code}>
                  {reasonText(code)}
                </option>
              ))}
            </select>
          )}
        </Field>
        <Field label="Комментарий" required hint="Внутренний комментарий сотрудника.">
          {(control) => (
            <textarea {...control} className="textarea" value={comment} onChange={(e) => setComment(e.target.value)} />
          )}
        </Field>
      </ConfirmDialog>

      <ConfirmDialog
        open={dialog === "retry-checks"}
        title="Перезапустить проверку?"
        description="Будет создан новый запуск проверок для той же ревизии. Прежний запуск сохранится как неуспешный."
        confirmLabel="Перезапустить"
        busy={retryChecks.isPending}
        error={nonConflictError(retryChecks.error)}
        onConfirm={() => snapshot && retryChecks.mutate(snapshot)}
        onCancel={close}
      />

      <ConfirmDialog
        open={dialog === "retry-disbursement"}
        title="Повторить имитацию выдачи?"
        description="Сервер гарантирует одну имитацию выдачи на заявку; повтор не создаст вторую."
        confirmLabel="Повторить"
        busy={retryDisbursement.isPending}
        error={nonConflictError(retryDisbursement.error)}
        onConfirm={() => snapshot && retryDisbursement.mutate(snapshot)}
        onCancel={close}
      />
    </Panel>
  );
}
