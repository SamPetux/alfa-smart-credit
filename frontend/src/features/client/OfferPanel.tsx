import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../../api/endpoints";
import { queryKeys } from "../../api/queryClient";
import type { ClientApplication, Offer } from "../../api/types";
import { useCommand } from "../../api/useCommand";
import { Button } from "../../components/Button";
import { ConfirmDialog } from "../../components/ConfirmDialog";
import { KeyValueList, Panel } from "../../components/Layout";
import { ErrorBlock, LoadingBlock, Notice } from "../../components/States";
import { formatAmount, formatMoney, formatRate } from "../../shared/money";
import { useToast } from "../../components/Toasts";
import { isConflict, useApplicationCommandEffects } from "./commandEffects";

/** Условия предложения — только значения сервера. Платёж и итог frontend не вычисляет. */
export function OfferTerms({ offer, requestedAmount }: { offer: Offer; requestedAmount: string | null | undefined }) {
  const terms = offer.terms;
  return (
    <div className="stack">
      <div className="offer-card">
        <span className="offer-label small">Сумма кредита</span>
        <strong className="offer-amount num">{formatAmount(terms.amount)}</strong>
        {terms.is_alternative && requestedAmount ? (
          <span className="offer-note small">Вы запрашивали {formatAmount(requestedAmount)}</span>
        ) : null}
        <div className="offer-facts">
          <div>
            <span className="small">Срок</span>
            <strong className="num">{terms.term_months ? `${terms.term_months} мес.` : "—"}</strong>
          </div>
          <div>
            <span className="small">Ставка</span>
            <strong className="num">{formatRate(terms.annual_rate)} годовых</strong>
          </div>
          <div>
            <span className="small">Комиссии</span>
            <strong className="num">{formatMoney(terms.fees ?? "0.00")}</strong>
          </div>
        </div>
        <p className="offer-note small">В демонстрационной модели комиссий нет</p>
      </div>
      <KeyValueList
        items={[
          {
            label: "Ежемесячный платёж",
            value: terms.monthly_payment ? formatMoney(terms.monthly_payment) : "—",
            numeric: true,
          },
          {
            label: "Сумма всех выплат",
            value: terms.total_payment ? formatMoney(terms.total_payment) : "—",
            numeric: true,
          },
        ]}
      />
    </div>
  );
}

function AlternativeReason({ id }: { id: string }) {
  const explain = useQuery({
    queryKey: queryKeys.explain(id, "amount"),
    queryFn: ({ signal }) => api.explain(id, "amount", { signal }),
  });
  if (!explain.data) return null;
  return (
    <Notice tone="info" title="Почему сумма меньше запрошенной">
      <ul className="bullets">
        {explain.data.bullets
          .filter((line) => !line.startsWith("Рекомендация risk-модуля"))
          .map((line) => (
            <li key={line}>{line}</li>
          ))}
      </ul>
      <p className="small muted">{explain.data.disclaimer}</p>
    </Notice>
  );
}

export function OfferPanel({ app }: { app: ClientApplication }) {
  const effects = useApplicationCommandEffects(app.id);
  const toast = useToast();
  const [confirmDecline, setConfirmDecline] = useState(false);
  const offer = useQuery({
    queryKey: queryKeys.offer(app.id),
    queryFn: ({ signal }) => api.offer(app.id, { signal }),
  });

  const accept = useCommand((offerId: string, ctx) => api.acceptOffer(app.id, app.version, offerId, ctx), {
    ...effects,
    onSuccess: (updated) => {
      effects.onSuccess(updated);
      toast("Условия приняты", "Ознакомьтесь с документом и подтвердите подписание.");
    },
  });
  const decline = useCommand((offerId: string, ctx) => api.declineOffer(app.id, app.version, offerId, ctx), {
    ...effects,
    onSettled: () => setConfirmDecline(false),
  });
  const commandError = accept.error ?? decline.error;

  return (
    <Panel title="Предложенные условия" id="offer">
      {offer.isPending ? (
        <LoadingBlock rows={5} label="Загружаем условия" />
      ) : offer.isError ? (
        <ErrorBlock error={offer.error} onRetry={() => void offer.refetch()} />
      ) : !offer.data ? (
        <Notice tone="warning">Действующего предложения нет. Обновите страницу: статус мог измениться.</Notice>
      ) : (
        <>
          <p className="muted">Условия подтвердил специалист банка. Они рассчитаны по учебной политике и не являются публичной офертой.</p>
          <OfferTerms offer={offer.data} requestedAmount={app.draft_fields?.requested_amount} />
          {offer.data.terms.is_alternative ? <AlternativeReason id={app.id} /> : null}
          {commandError ? (
            isConflict(commandError) ? (
              <Notice tone="warning" title="Данные заявки изменились.">
                Мы обновили страницу. Проверьте условия и повторите действие, если оно ещё нужно.
              </Notice>
            ) : (
              <ErrorBlock error={commandError} title="Действие не выполнено." />
            )
          ) : null}
          <div className="row">
            <Button
              variant="primary"
              busy={accept.isPending}
              busyLabel="Принимаем…"
              disabled={decline.isPending}
              onClick={() => accept.mutate(offer.data!.id)}
            >
              Принять условия
            </Button>
            <Button variant="danger" disabled={accept.isPending} onClick={() => setConfirmDecline(true)}>
              Отклонить предложение
            </Button>
          </div>
          <p className="small muted">После принятия откроется документ для ознакомления. Подписание будет отдельным шагом.</p>
          <ConfirmDialog
            open={confirmDecline}
            title="Отклонить предложение?"
            description="Заявка будет завершена. Чтобы получить новые условия, понадобится новая заявка."
            confirmLabel="Отклонить предложение"
            tone="danger"
            busy={decline.isPending}
            onConfirm={() => decline.mutate(offer.data!.id)}
            onCancel={() => setConfirmDecline(false)}
          />
        </>
      )}
    </Panel>
  );
}
