import { QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";
import { createBrowserRouter, RouterProvider } from "react-router";
import { createQueryClient } from "../api/queryClient";
import { SessionProvider } from "../api/session";
import { ButtonLink } from "../components/Button";
import { DemoPage } from "../features/demo/DemoPage";
import { HomePage } from "../features/client/HomePage";
import { AppShell } from "./AppShell";
import { RequireRole, RootRedirect } from "./guards";

function NotFound() {
  return (
    <main className="page" id="main">
      <div className="panel stack">
        <h1>Страница не найдена</h1>
        <p className="muted">Проверьте адрес или вернитесь в кабинет.</p>
        <div>
          <ButtonLink to="/">В кабинет</ButtonLink>
        </div>
      </div>
    </main>
  );
}

export function createAppRouter() {
  return createBrowserRouter([
    { path: "/", element: <RootRedirect /> },
    { path: "/demo", element: <DemoPage /> },
    {
      element: (
        <RequireRole role="CLIENT">
          <AppShell />
        </RequireRole>
      ),
      children: [{ path: "/applications", element: <HomePage /> }],
    },
    { path: "*", element: <NotFound /> },
  ]);
}

export function App() {
  const [queryClient] = useState(createQueryClient);
  const [router] = useState(createAppRouter);
  return (
    <QueryClientProvider client={queryClient}>
      <SessionProvider>
        <RouterProvider router={router} />
      </SessionProvider>
    </QueryClientProvider>
  );
}
