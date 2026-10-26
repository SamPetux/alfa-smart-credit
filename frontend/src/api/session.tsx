import { useQuery, useQueryClient } from "@tanstack/react-query";
import { createContext, Fragment, useCallback, useContext, useMemo, type ReactNode } from "react";
import { api } from "./endpoints";
import { isApiError } from "./errors";
import { resetSessionScope, setCsrfToken } from "./http";
import { queryKeys } from "./queryClient";
import type { SessionInfo } from "./types";

interface SessionContextValue {
  session: SessionInfo | null;
  isLoading: boolean;
  /** Смена демопрофиля: отмена запросов, очистка кэша, новая серверная сессия. */
  switchProfile: (profileId: string) => Promise<SessionInfo>;
  /** Вход тестовым аккаунтом при DEMO_MODE=false. */
  signIn: (username: string, password: string) => Promise<SessionInfo>;
  signOut: () => Promise<void>;
}

const SessionContext = createContext<SessionContextValue | null>(null);

async function loadSession(signal: AbortSignal): Promise<SessionInfo | null> {
  try {
    const info = await api.me({ signal });
    setCsrfToken(info.csrf_token);
    return info;
  } catch (error) {
    if (isApiError(error) && error.kind === "unauthenticated") return null;
    throw error;
  }
}

export function SessionProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const sessionQuery = useQuery({
    queryKey: queryKeys.session,
    queryFn: ({ signal }) => loadSession(signal),
    staleTime: Infinity,
    refetchOnWindowFocus: false,
  });

  const dropPreviousProfile = useCallback(async () => {
    resetSessionScope();
    await queryClient.cancelQueries();
    queryClient.getMutationCache().clear();
    queryClient.removeQueries({ predicate: (query) => query.queryKey[0] !== queryKeys.session[0] });
  }, [queryClient]);

  const startSession = useCallback(
    async (open: () => Promise<SessionInfo>) => {
      await dropPreviousProfile();
      const info = await open();
      setCsrfToken(info.csrf_token);
      queryClient.setQueryData(queryKeys.session, info);
      return info;
    },
    [dropPreviousProfile, queryClient],
  );

  const switchProfile = useCallback(
    (profileId: string) => startSession(() => api.startDemoSession(profileId)),
    [startSession],
  );

  const signIn = useCallback(
    (username: string, password: string) => startSession(() => api.login(username, password)),
    [startSession],
  );

  const signOut = useCallback(async () => {
    try {
      await api.logout();
    } finally {
      await dropPreviousProfile();
      queryClient.setQueryData(queryKeys.session, null);
    }
  }, [dropPreviousProfile, queryClient]);

  const value = useMemo<SessionContextValue>(
    () => ({
      session: sessionQuery.data ?? null,
      isLoading: sessionQuery.isPending,
      switchProfile,
      signIn,
      signOut,
    }),
    [sessionQuery.data, sessionQuery.isPending, switchProfile, signIn, signOut],
  );

  // Ключ по пользователю пересоздаёт всё дерево: формы, локальное состояние и подписки
  // на запросы прежнего профиля не переживают смену сессии.
  const identity = value.session?.user.id ?? "anonymous";
  return (
    <SessionContext.Provider value={value}>
      <Fragment key={identity}>{children}</Fragment>
    </SessionContext.Provider>
  );
}

export function useSession(): SessionContextValue {
  const value = useContext(SessionContext);
  if (!value) throw new Error("useSession must be used inside SessionProvider");
  return value;
}
