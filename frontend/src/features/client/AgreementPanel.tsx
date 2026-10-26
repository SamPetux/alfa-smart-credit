import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../../api/endpoints";
import { queryKeys } from "../../api/queryClient";
import type { ClientApplication } from "../../api/types";
import { useCommand } from "../../api/useCommand";
import { Button } from "../../components/Button";
import { DocumentView } from "../../components/DocumentView";
import { Panel } from "../../components/Layout";
import { ErrorBlock, LoadingBlock, Notice } from "../../components/States";
import { isConflict, useApplicationCommandEffects } from "./commandEffects";

/** Документ для ознакомления и явное согласие на имитацию подписания текущей версии. */
export function AgreementPanel({ app }: { app: ClientApplication }) {
  const effects = useApplicationCommandEffects(app.id);
  const [consent, setConsent] = useState(false);
  const agreement = useQuery({
    queryKey: queryKeys.agreement(app.id),
    queryFn: ({ signal }) => api.agreement(app.id, { signal }),
  });

  const sign = useCommand(
    (input: { agreementId: string; contentHash: string }, ctx) =>
      api.simulateSign(app.id, { expectedVersion: app.version, ...input }, ctx),
    effects,
  );

  return (
    <Panel title="Документ для ознакомления" id="agreement">
      {agreement.isPending ? (
        <LoadingBlock rows={6} label="Загружаем документ" />
      ) : agreement.isError ? (
        <ErrorBlock error={agreement.error} onRetry={() => void agreement.refetch()} />
      ) : !agreement.data ? (
        <Notice tone="warning">Документ ещё не сформирован. Обновите страницу через несколько секунд.</Notice>
      ) : (
        <>
          <DocumentView
            title="Кредитный договор (учебная имитация)"
            text={agreement.data.document_text}
            contentHash={agreement.data.content_hash}
          />
          <label className="checkbox">
            <input type="checkbox" checked={consent} onChange={(event) => setConsent(event.target.checked)} />
            <span>
              Я ознакомился с документом выше и согласен смоделировать его подписание. Это не юридически значимая
              электронная подпись.
            </span>
          </label>
          {sign.isError ? (
            isConflict(sign.error) ? (
              <Notice tone="warning" title="Документ или заявка изменились.">
                Мы загрузили актуальную версию. Ознакомьтесь с ней и подтвердите снова.
              </Notice>
            ) : (
              <ErrorBlock error={sign.error} title="Подписание не смоделировано." />
            )
          ) : null}
          <div>
            <Button
              variant="primary"
              disabled={!consent}
              busy={sign.isPending}
              busyLabel="Моделируем подписание…"
              onClick={() =>
                sign.mutate({ agreementId: agreement.data!.id, contentHash: agreement.data!.content_hash })
              }
            >
              Смоделировать подписание
            </Button>
          </div>
        </>
      )}
    </Panel>
  );
}
