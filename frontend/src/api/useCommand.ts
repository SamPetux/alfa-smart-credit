import { useMutation, type UseMutationOptions } from "@tanstack/react-query";
import { useCallback, useRef } from "react";
import { isApiError } from "./errors";

function newKey(): string {
  return crypto.randomUUID();
}

/**
 * Команда с Idempotency-Key. Ключ живёт, пока пользователь повторяет то же намерение:
 * после сетевой ошибки или 503 повтор уходит с тем же ключом и не дублирует эффект.
 * После успеха или окончательного отказа (4xx) следующий вызов получает новый ключ.
 * Автоматического повтора нет — особенно после 409.
 */
export function useCommand<TVariables, TData>(
  run: (variables: TVariables, ctx: { idempotencyKey: string }) => Promise<TData>,
  options: Omit<UseMutationOptions<TData, Error, TVariables>, "mutationFn"> = {},
) {
  const keyRef = useRef<string>(newKey());
  const renewKey = useCallback(() => {
    keyRef.current = newKey();
  }, []);

  return useMutation<TData, Error, TVariables>({
    ...options,
    mutationFn: (variables) => run(variables, { idempotencyKey: keyRef.current }),
    onSuccess: (...args) => {
      renewKey();
      return options.onSuccess?.(...args);
    },
    onError: (...args) => {
      const [error] = args;
      if (!(isApiError(error) && error.isRetryable)) renewKey();
      return options.onError?.(...args);
    },
  });
}
