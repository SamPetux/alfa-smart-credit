import { QueryClientProvider } from "@tanstack/react-query";
import { MotionConfig } from "motion/react";
import { render } from "@testing-library/react";
import type { ReactElement } from "react";
import { createMemoryRouter, RouterProvider } from "react-router";
import { vi } from "vitest";
import { createQueryClient } from "../api/queryClient";
import { SessionProvider } from "../api/session";
import { ToastProvider } from "../components/Toasts";

export function json(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

export type Route = (url: string, init?: RequestInit) => Response | Promise<Response> | undefined;

/** Подменяет fetch маршрутами вида (url, init) → Response; неизвестный запрос — 404. */
export function mockFetch(route: Route) {
  const mock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const response = await route(String(input), init);
    return response ?? json(404, { detail: "Not Found" });
  });
  vi.stubGlobal("fetch", mock);
  return mock;
}

export function renderRoute(element: ReactElement, { path = "/", url = "/" } = {}) {
  const router = createMemoryRouter(
    [
      { path, element },
      { path: "/demo", element: <p>demo page</p> },
      { path: "*", element: <p>other page</p> },
    ],
    { initialEntries: [url] },
  );
  return render(
    <QueryClientProvider client={createQueryClient()}>
      <MotionConfig reducedMotion="always">
        <SessionProvider>
          <ToastProvider>
            <RouterProvider router={router} />
          </ToastProvider>
        </SessionProvider>
      </MotionConfig>
    </QueryClientProvider>,
  );
}

export const clientSession = {
  user: {
    id: "u-client",
    username: "client_romashka",
    role: "CLIENT",
    display_name: "Клиент",
    company: { id: "c1", display_name: "ООО «Ромашка» (синтетика)", demo_registration_id: "DEMO-001" },
  },
  csrf_token: "csrf",
  demo_mode: true,
};

export const officerSession = {
  user: { id: "u-officer", username: "officer", role: "OFFICER", display_name: "Сотрудник", company: null },
  csrf_token: "csrf",
  demo_mode: true,
};
