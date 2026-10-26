import type { FieldError } from "./types";

export type ApiErrorKind =
  | "unauthenticated"
  | "forbidden"
  | "not_found"
  | "conflict"
  | "validation"
  | "too_large"
  | "unsupported"
  | "rate_limited"
  | "unavailable"
  | "network"
  | "server";

/** Единая ошибка API: envelope из contracts/ или стандартный ответ FastAPI. */
export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly fieldErrors: FieldError[];
  readonly requestId: string | null;

  constructor(init: {
    status: number;
    code: string;
    message: string;
    fieldErrors?: FieldError[];
    requestId?: string | null;
  }) {
    super(init.message);
    this.name = "ApiError";
    this.status = init.status;
    this.code = init.code;
    this.fieldErrors = init.fieldErrors ?? [];
    this.requestId = init.requestId ?? null;
  }

  get kind(): ApiErrorKind {
    return kindForStatus(this.status);
  }

  /** Повтор той же команды с тем же Idempotency-Key безопасен только для этих ошибок. */
  get isRetryable(): boolean {
    return this.kind === "network" || this.kind === "unavailable" || this.code === "REQUEST_IN_PROGRESS";
  }
}

export function isApiError(error: unknown): error is ApiError {
  return error instanceof ApiError;
}

export function isAbortError(error: unknown): boolean {
  return error instanceof DOMException && error.name === "AbortError";
}

function kindForStatus(status: number): ApiErrorKind {
  switch (status) {
    case 0:
      return "network";
    case 401:
      return "unauthenticated";
    case 403:
      return "forbidden";
    case 404:
      return "not_found";
    case 409:
      return "conflict";
    case 413:
      return "too_large";
    case 415:
      return "unsupported";
    case 422:
      return "validation";
    case 429:
      return "rate_limited";
    case 502:
    case 503:
    case 504:
      return "unavailable";
    default:
      return "server";
  }
}

const DEFAULT_MESSAGES: Record<ApiErrorKind, string> = {
  unauthenticated: "Сессия закончилась. Выберите демопрофиль заново.",
  forbidden: "Это действие недоступно для текущего профиля.",
  not_found: "Объект не найден или недоступен текущему профилю.",
  conflict: "Данные уже изменились. Обновите страницу перед действием.",
  validation: "Проверьте заполнение полей.",
  too_large: "Файл больше допустимого размера.",
  unsupported: "Этот тип файла не поддерживается.",
  rate_limited: "Слишком много запросов. Повторите через несколько секунд.",
  unavailable: "Сервис временно недоступен. Данные сохранены, повторите позже.",
  network: "Нет связи с сервером. Проверьте подключение и повторите.",
  server: "Внутренняя ошибка сервера. Повторите позже.",
};

interface Envelope {
  error: { code: string; message: string; field_errors?: FieldError[]; request_id?: string };
}

interface FastApiDetail {
  detail: string | Array<{ loc?: Array<string | number>; msg?: string }>;
}

function isEnvelope(body: unknown): body is Envelope {
  return typeof body === "object" && body !== null && "error" in body;
}

function isFastApiDetail(body: unknown): body is FastApiDetail {
  return typeof body === "object" && body !== null && "detail" in body;
}

/** Поле из loc FastAPI: ["body","draft_fields","requested_amount"] → "requested_amount". */
function fieldFromLoc(loc: Array<string | number> | undefined): string {
  const named = (loc ?? []).filter((part): part is string => typeof part === "string" && part !== "body");
  return named[named.length - 1] ?? "request";
}

export function toApiError(status: number, body: unknown, requestId: string | null): ApiError {
  const kind = kindForStatus(status);
  if (isEnvelope(body)) {
    return new ApiError({
      status,
      code: body.error.code,
      message: body.error.message || DEFAULT_MESSAGES[kind],
      fieldErrors: body.error.field_errors ?? [],
      requestId: body.error.request_id ?? requestId,
    });
  }
  if (isFastApiDetail(body) && Array.isArray(body.detail)) {
    return new ApiError({
      status,
      code: "VALIDATION_ERROR",
      message: DEFAULT_MESSAGES.validation,
      fieldErrors: body.detail.map((item) => ({
        field: fieldFromLoc(item.loc),
        message: item.msg ?? "Некорректное значение",
      })),
      requestId,
    });
  }
  // Текст detail от FastAPI техничен (часто на английском) — показываем понятное сообщение.
  return new ApiError({ status, code: kind.toUpperCase(), message: DEFAULT_MESSAGES[kind], requestId });
}

export function networkError(): ApiError {
  return new ApiError({ status: 0, code: "NETWORK_ERROR", message: DEFAULT_MESSAGES.network });
}

export function messageFor(error: unknown): string {
  if (isApiError(error)) return error.message;
  return DEFAULT_MESSAGES.server;
}
