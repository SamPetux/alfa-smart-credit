import { useQuery } from "@tanstack/react-query";
import { api } from "../../api/endpoints";
import { queryKeys } from "../../api/queryClient";
import type { ApplicationStatus } from "../../api/types";
import { isWorkerDriven } from "../../shared/status";

export const POLL_INTERVAL_MS = 2_000;

/**
 * Заявка клиента. Опрос раз в 2 секунды только пока статус меняет worker; при скрытой
 * вкладке React Query опрос останавливает, при возврате — перечитывает данные.
 */
export function useClientApplication(id: string) {
  return useQuery({
    queryKey: queryKeys.application(id),
    queryFn: ({ signal }) => api.getApplication(id, { signal }),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status && isWorkerDriven(status) ? POLL_INTERVAL_MS : false;
    },
    refetchIntervalInBackground: false,
    refetchOnWindowFocus: "always",
  });
}

export function useHistory(id: string, status: ApplicationStatus | undefined, version: number | undefined) {
  return useQuery({
    // Версия в ключе: история перечитывается при каждом изменении заявки, без отдельного опроса.
    queryKey: [...queryKeys.history(id), version],
    queryFn: ({ signal }) => api.history(id, { signal }),
    enabled: Boolean(status),
    placeholderData: (previous) => previous,
  });
}
