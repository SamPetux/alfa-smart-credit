import { networkError, toApiError } from "./errors";

export const API_PREFIX = "/api/v1";
const CSRF_COOKIE = "asc_csrf";

type Method = "GET" | "POST" | "PATCH" | "DELETE";

export interface RequestOptions {
  body?: unknown;
  formData?: FormData;
  query?: Record<string, string | number | undefined>;
  signal?: AbortSignal;
  /** Обязателен для команд submit/resubmit/decision/accept/decline/sign/retry/create. */
  idempotencyKey?: string;
}

/**
 * Область текущей сессии. При смене демопрофиля все запросы прежнего профиля
 * отменяются, а ответы, пришедшие после смены, отбрасываются — иначе данные
 * прошлого пользователя могут попасть в UI нового.
 */
let sessionScope = new AbortController();
let sessionEpoch = 0;
let csrfToken: string | null = null;

export function setCsrfToken(token: string | null): void {
  csrfToken = token;
}

export function resetSessionScope(): void {
  sessionScope.abort();
  sessionScope = new AbortController();
  sessionEpoch += 1;
  csrfToken = null;
}

function readCsrfCookie(): string | null {
  const match = document.cookie.split("; ").find((part) => part.startsWith(`${CSRF_COOKIE}=`));
  return match ? decodeURIComponent(match.slice(CSRF_COOKIE.length + 1)) : null;
}

function buildUrl(path: string, query?: RequestOptions["query"]): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query ?? {})) {
    if (value !== undefined && value !== "") params.set(key, String(value));
  }
  const search = params.toString();
  return `${API_PREFIX}${path}${search ? `?${search}` : ""}`;
}

function combineSignals(signals: Array<AbortSignal | undefined>): AbortSignal {
  const controller = new AbortController();
  for (const signal of signals) {
    if (!signal) continue;
    if (signal.aborted) {
      controller.abort(signal.reason);
      break;
    }
    signal.addEventListener("abort", () => controller.abort(signal.reason), { once: true });
  }
  return controller.signal;
}

function abortedError(): DOMException {
  return new DOMException("Request belongs to a previous session", "AbortError");
}

async function readBody(response: Response): Promise<unknown> {
  if (response.status === 204) return null;
  const text = await response.text();
  if (!text) return null;
  try {
    return JSON.parse(text) as unknown;
  } catch {
    return text;
  }
}

export async function request<T>(method: Method, path: string, options: RequestOptions = {}): Promise<T> {
  const epoch = sessionEpoch;
  const headers: Record<string, string> = { Accept: "application/json" };
  let body: BodyInit | undefined;

  if (options.formData) {
    body = options.formData;
  } else if (options.body !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(options.body);
  }
  if (method !== "GET") {
    const token = csrfToken ?? readCsrfCookie();
    if (token) headers["X-CSRF-Token"] = token;
  }
  if (options.idempotencyKey) headers["Idempotency-Key"] = options.idempotencyKey;

  let response: Response;
  try {
    response = await fetch(buildUrl(path, options.query), {
      method,
      headers,
      body,
      credentials: "same-origin",
      signal: combineSignals([options.signal, sessionScope.signal]),
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") throw error;
    throw networkError();
  }

  const payload = await readBody(response);
  if (epoch !== sessionEpoch) throw abortedError();
  if (!response.ok) {
    throw toApiError(response.status, payload, response.headers.get("X-Request-Id"));
  }
  return payload as T;
}

