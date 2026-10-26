import { MutationCache, QueryCache, QueryClient } from "@tanstack/react-query";
import { isApiError } from "./errors";

export const queryKeys = {
  session: ["session"] as const,
  meta: ["meta"] as const,
  demoProfiles: ["demo-profiles"] as const,
  products: ["products"] as const,
  applications: ["applications"] as const,
  application: (id: string) => ["applications", id] as const,
  history: (id: string) => ["applications", id, "history"] as const,
  infoRequest: (id: string) => ["applications", id, "info-request"] as const,
  offer: (id: string) => ["applications", id, "offer"] as const,
  agreement: (id: string) => ["applications", id, "agreement"] as const,
  explain: (id: string, topic: string) => ["applications", id, "explain", topic] as const,
  bankQueue: (filters: object) => ["bank", "queue", filters] as const,
  bankApplication: (id: string) => ["bank", "applications", id] as const,
};

/** Истёкшая сессия: убрать все данные прежнего пользователя и вернуть на /demo. */
function handleUnauthenticated(client: QueryClient, error: unknown): void {
  if (!isApiError(error) || error.kind !== "unauthenticated") return;
  client.removeQueries({ predicate: (query) => query.queryKey[0] !== queryKeys.session[0] });
  client.setQueryData(queryKeys.session, null);
}

export function createQueryClient(): QueryClient {
  const client: QueryClient = new QueryClient({
    queryCache: new QueryCache({ onError: (error) => handleUnauthenticated(client, error) }),
    mutationCache: new MutationCache({ onError: (error) => handleUnauthenticated(client, error) }),
    defaultOptions: {
      queries: {
        staleTime: 5_000,
        refetchOnWindowFocus: true,
        retry: (failureCount, error) =>
          failureCount < 2 && isApiError(error) && (error.kind === "network" || error.kind === "unavailable"),
      },
      // Команды не повторяются автоматически: повтор решает пользователь (тот же Idempotency-Key).
      mutations: { retry: false },
    },
  });
  return client;
}
