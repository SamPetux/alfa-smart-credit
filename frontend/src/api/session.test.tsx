import { QueryClientProvider, useQuery } from "@tanstack/react-query";
import { act, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { resetSessionScope } from "./http";
import { createQueryClient } from "./queryClient";
import { SessionProvider, useSession } from "./session";
import { useCommand } from "./useCommand";
import { ApiError } from "./errors";
import { renderHook } from "@testing-library/react";
import type { ReactNode } from "react";

const fetchMock = vi.fn<typeof fetch>();

function json(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

function sessionFor(name: string) {
  return {
    user: { id: name, username: name, role: "CLIENT", display_name: name, company: null },
    csrf_token: `csrf-${name}`,
    demo_mode: true,
  };
}

beforeEach(() => {
  vi.stubGlobal("fetch", fetchMock);
  resetSessionScope();
});
afterEach(() => {
  fetchMock.mockReset();
  vi.unstubAllGlobals();
});

function Probe() {
  const { session, switchProfile } = useSession();
  const apps = useQuery({
    queryKey: ["applications"],
    queryFn: () => fetch("/api/v1/applications").then((r) => r.json() as Promise<{ owner: string }>),
    enabled: Boolean(session),
  });
  return (
    <div>
      <span data-testid="user">{session?.user.username ?? "none"}</span>
      <span data-testid="apps">{apps.data?.owner ?? "empty"}</span>
      <button onClick={() => void switchProfile("officer")}>switch</button>
    </div>
  );
}

describe("SessionProvider", () => {
  it("treats 401 from /auth/me as no session", async () => {
    fetchMock.mockResolvedValueOnce(json(401, { detail: "Not authenticated" }));
    const client = createQueryClient();
    render(
      <QueryClientProvider client={client}>
        <SessionProvider>
          <Probe />
        </SessionProvider>
      </QueryClientProvider>,
    );
    await waitFor(() => expect(screen.getByTestId("user")).toHaveTextContent("none"));
  });

  it("clears cached data of the previous profile on switch", async () => {
    fetchMock.mockImplementation(async (input) => {
      const url = String(input);
      if (url.endsWith("/auth/me")) return json(200, sessionFor("client_romashka"));
      if (url.endsWith("/demo/session")) return json(200, sessionFor("officer"));
      return json(200, { owner: "romashka" });
    });
    const client = createQueryClient();
    render(
      <QueryClientProvider client={client}>
        <SessionProvider>
          <Probe />
        </SessionProvider>
      </QueryClientProvider>,
    );
    await waitFor(() => expect(screen.getByTestId("apps")).toHaveTextContent("romashka"));

    fetchMock.mockImplementation(async (input) => {
      const url = String(input);
      if (url.endsWith("/demo/session")) return json(200, sessionFor("officer"));
      return new Promise<Response>(() => {});
    });
    await act(async () => screen.getByText("switch").click());
    await waitFor(() => expect(screen.getByTestId("user")).toHaveTextContent("officer"));
    expect(screen.getByTestId("apps")).toHaveTextContent("empty");
  });
});

describe("useCommand", () => {
  function wrapper({ children }: { children: ReactNode }) {
    return <QueryClientProvider client={createQueryClient()}>{children}</QueryClientProvider>;
  }

  it("reuses the key after a network failure and renews it after success or 409", async () => {
    const seen: string[] = [];
    const outcomes: Array<() => Promise<string>> = [
      () => Promise.reject(new ApiError({ status: 0, code: "NETWORK_ERROR", message: "n" })),
      () => Promise.resolve("ok"),
      () => Promise.reject(new ApiError({ status: 409, code: "VERSION_CONFLICT", message: "c" })),
      () => Promise.resolve("ok"),
    ];
    const { result } = renderHook(
      () =>
        useCommand<void, string>((_v, { idempotencyKey }) => {
          seen.push(idempotencyKey);
          return outcomes[seen.length - 1]!();
        }),
      { wrapper },
    );
    for (let i = 0; i < outcomes.length; i += 1) {
      await act(async () => {
        await result.current.mutateAsync().catch(() => undefined);
      });
    }
    expect(seen[0]).toBe(seen[1]);
    expect(seen[2]).not.toBe(seen[1]);
    expect(seen[3]).not.toBe(seen[2]);
  });
});
