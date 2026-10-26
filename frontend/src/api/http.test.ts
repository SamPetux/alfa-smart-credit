import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "./errors";
import { request, resetSessionScope, setCsrfToken } from "./http";

function jsonResponse(status: number, body: unknown, headers: Record<string, string> = {}): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", ...headers },
  });
}

const fetchMock = vi.fn<typeof fetch>();

beforeEach(() => {
  vi.stubGlobal("fetch", fetchMock);
  resetSessionScope();
});

afterEach(() => {
  fetchMock.mockReset();
  vi.unstubAllGlobals();
});

function lastHeaders(): Record<string, string> {
  const init = fetchMock.mock.calls.at(-1)?.[1];
  return (init?.headers ?? {}) as Record<string, string>;
}

describe("request", () => {
  it("sends CSRF and Idempotency-Key only on commands", async () => {
    setCsrfToken("csrf-1");
    fetchMock.mockResolvedValueOnce(jsonResponse(200, { ok: true }));
    await request("GET", "/applications");
    expect(lastHeaders()["X-CSRF-Token"]).toBeUndefined();

    fetchMock.mockResolvedValueOnce(jsonResponse(202, { ok: true }));
    await request("POST", "/applications/1/submit", { body: { expected_version: 3 }, idempotencyKey: "key-1" });
    expect(lastHeaders()["X-CSRF-Token"]).toBe("csrf-1");
    expect(lastHeaders()["Idempotency-Key"]).toBe("key-1");
    expect(fetchMock.mock.calls.at(-1)?.[0]).toBe("/api/v1/applications/1/submit");
    expect(fetchMock.mock.calls.at(-1)?.[1]?.credentials).toBe("same-origin");
  });

  it("falls back to the readable CSRF cookie after reload", async () => {
    document.cookie = "asc_csrf=from-cookie; path=/";
    fetchMock.mockResolvedValueOnce(jsonResponse(200, {}));
    await request("PATCH", "/applications/1", { body: {} });
    expect(lastHeaders()["X-CSRF-Token"]).toBe("from-cookie");
  });

  it("drops empty query params", async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse(200, { items: [] }));
    await request("GET", "/bank/applications", { query: { status: "MANUAL_REVIEW", product_code: undefined } });
    expect(fetchMock.mock.calls.at(-1)?.[0]).toBe("/api/v1/bank/applications?status=MANUAL_REVIEW");
  });

  it("maps the error envelope with field errors", async () => {
    fetchMock.mockResolvedValueOnce(
      jsonResponse(422, {
        error: {
          code: "VALIDATION_ERROR",
          message: "Не хватает обязательных данных для отправки",
          field_errors: [{ field: "documents", message: "Нужен документ FINANCIAL_SUMMARY" }],
          request_id: "req-1",
        },
      }),
    );
    const error = await request("POST", "/applications/1/submit").catch((e: unknown) => e);
    expect(error).toBeInstanceOf(ApiError);
    const apiError = error as ApiError;
    expect(apiError.kind).toBe("validation");
    expect(apiError.fieldErrors).toEqual([{ field: "documents", message: "Нужен документ FINANCIAL_SUMMARY" }]);
    expect(apiError.requestId).toBe("req-1");
  });

  it("maps FastAPI validation detail to field errors", async () => {
    fetchMock.mockResolvedValueOnce(
      jsonResponse(422, {
        detail: [{ loc: ["body", "draft_fields", "requested_amount"], msg: "Input should be a valid decimal" }],
      }),
    );
    const error = (await request("PATCH", "/applications/1").catch((e: unknown) => e)) as ApiError;
    expect(error.fieldErrors[0]?.field).toBe("requested_amount");
  });

  it.each([
    [401, "unauthenticated"],
    [403, "forbidden"],
    [404, "not_found"],
    [409, "conflict"],
    [503, "unavailable"],
  ] as const)("classifies HTTP %i as %s with a readable message", async (status, kind) => {
    fetchMock.mockResolvedValueOnce(jsonResponse(status, { detail: "Not authenticated" }));
    const error = (await request("GET", "/auth/me").catch((e: unknown) => e)) as ApiError;
    expect(error.kind).toBe(kind);
    expect(error.message).not.toBe("Not authenticated");
  });

  it("marks network and 503 failures as retryable, 409 as not", async () => {
    fetchMock.mockRejectedValueOnce(new TypeError("Failed to fetch"));
    const network = (await request("POST", "/x").catch((e: unknown) => e)) as ApiError;
    expect(network.kind).toBe("network");
    expect(network.isRetryable).toBe(true);

    fetchMock.mockResolvedValueOnce(
      jsonResponse(409, { error: { code: "VERSION_CONFLICT", message: "m", field_errors: [], request_id: "r" } }),
    );
    const conflict = (await request("POST", "/x").catch((e: unknown) => e)) as ApiError;
    expect(conflict.isRetryable).toBe(false);
  });

  it("discards responses that arrive after the profile switched", async () => {
    let resolve: (r: Response) => void = () => {};
    fetchMock.mockImplementationOnce(() => new Promise<Response>((r) => (resolve = r)));
    const pending = request("GET", "/applications");
    resetSessionScope();
    resolve(jsonResponse(200, { items: [{ id: "previous-user" }] }));
    await expect(pending).rejects.toMatchObject({ name: "AbortError" });
  });

  it("aborts in-flight requests when the session scope resets", async () => {
    fetchMock.mockImplementationOnce(
      (_url, init) =>
        new Promise<Response>((_resolve, reject) => {
          init?.signal?.addEventListener("abort", () => reject(new DOMException("aborted", "AbortError")));
        }),
    );
    const pending = request("GET", "/applications");
    resetSessionScope();
    await expect(pending).rejects.toMatchObject({ name: "AbortError" });
  });
});
