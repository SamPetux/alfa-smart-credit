import { useQueryClient } from "@tanstack/react-query";
import { useCallback } from "react";
import { isApiError } from "../../api/errors";
import { queryKeys } from "../../api/queryClient";
import type { ClientApplication } from "../../api/types";

/**
 * Общие эффекты клиентских команд. Успех — новое состояние из ответа сервера и перечитывание
 * зависимых данных. 409 — перечитать заявку, но не повторять команду автоматически.
 */
export function useApplicationCommandEffects(id: string) {
  const queryClient = useQueryClient();

  const refreshDependents = useCallback(() => {
    void queryClient.invalidateQueries({
      predicate: (query) => query.queryKey[0] === "applications" && query.queryKey[1] === id && query.queryKey.length > 2,
    });
    void queryClient.invalidateQueries({ queryKey: queryKeys.applications, exact: true });
  }, [id, queryClient]);

  const onSuccess = useCallback(
    (updated: ClientApplication) => {
      queryClient.setQueryData(queryKeys.application(id), updated);
      refreshDependents();
    },
    [id, queryClient, refreshDependents],
  );

  const onError = useCallback(
    (error: Error) => {
      if (isApiError(error) && (error.kind === "conflict" || error.kind === "not_found")) {
        void queryClient.invalidateQueries({ queryKey: queryKeys.application(id), exact: true });
        refreshDependents();
      }
    },
    [id, queryClient, refreshDependents],
  );

  return { onSuccess, onError };
}

export function isConflict(error: unknown): boolean {
  return isApiError(error) && error.kind === "conflict";
}
