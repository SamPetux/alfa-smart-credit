import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router";
import type { Role } from "../api/types";
import { useSession } from "../api/session";
import { ButtonLink } from "../components/Button";
import { LoadingBlock } from "../components/States";

export function homePathFor(role: Role | string | undefined): string {
  return role === "OFFICER" ? "/bank/applications" : "/applications";
}

/**
 * Удобство навигации, а не защита: каждое действие и чтение проверяет сервер.
 * Без сессии — на /demo, чужая роль — объяснение и ссылка в свой кабинет.
 */
export function RequireRole({ role, children }: { role: Role; children: ReactNode }) {
  const { session, isLoading } = useSession();
  const location = useLocation();

  if (isLoading) {
    return (
      <main className="page">
        <LoadingBlock label="Проверяем сессию" />
      </main>
    );
  }
  if (!session) {
    return <Navigate to="/demo" replace state={{ from: location.pathname }} />;
  }
  if (session.user.role !== role) {
    return (
      <main className="page" id="main">
        <div className="panel stack">
          <h1>Раздел недоступен для текущего профиля</h1>
          <p className="muted">
            Этот раздел относится к другой роли. Сервер всё равно отклонит такие запросы — откройте свой
            кабинет или смените демопрофиль.
          </p>
          <div className="row">
            <ButtonLink to={homePathFor(session.user.role)} variant="primary">
              Открыть мой кабинет
            </ButtonLink>
            <ButtonLink to="/demo">Сменить профиль</ButtonLink>
          </div>
        </div>
      </main>
    );
  }
  return <>{children}</>;
}

export function RootRedirect() {
  const { session, isLoading } = useSession();
  if (isLoading) {
    return (
      <main className="page">
        <LoadingBlock label="Проверяем сессию" />
      </main>
    );
  }
  return <Navigate to={session ? homePathFor(session.user.role) : "/demo"} replace />;
}
