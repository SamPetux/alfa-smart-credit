import { useQuery } from "@tanstack/react-query";
import { NavLink, Outlet, useLocation } from "react-router";
import { api } from "../api/endpoints";
import { queryKeys } from "../api/queryClient";
import { useSession } from "../api/session";
import { ButtonLink } from "../components/Button";

export function DemoBanner() {
  const meta = useQuery({ queryKey: queryKeys.meta, queryFn: ({ signal }) => api.meta({ signal }), staleTime: Infinity });
  const { session } = useSession();
  const demo = meta.data?.demo_mode ?? session?.demo_mode ?? true;
  return (
    <div className="demo-banner" role="note">
      <span className="demo-dot" aria-hidden="true" />
      <span>
        <strong>{demo ? "Демонстрационный режим." : "Тестовый стенд."}</strong> Только синтетические данные.
        Реальная выдача и юридическая подпись не выполняются
        {demo ? "; открытый выбор профиля не является аутентификацией." : "."}
      </span>
    </div>
  );
}

/** Собственный знак кабинета. Логотип банка намеренно не воспроизводится. */
export function BrandMark({ caption = "для бизнеса" }: { caption?: string }) {
  return (
    <span className="brand">
      <span className="brand-mark" aria-hidden="true">
        <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="#fff" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M6 17 L11 11 L14 14 L18 8" />
          <path d="M14 8 H18 V12" />
        </svg>
      </span>
      <span className="brand-text">
        <span className="brand-name">Кредитный кабинет</span>
        <span className="brand-caption">{caption}</span>
      </span>
    </span>
  );
}

function initials(name: string): string {
  const words = name
    .replace(/[«»"()]/g, " ")
    .split(/\s+/)
    .filter((word) => word && !/^(ООО|ИП|АО|синтетика)$/i.test(word));
  return words
    .slice(0, 2)
    .map((word) => word[0]?.toUpperCase() ?? "")
    .join("");
}

export function AppShell() {
  const { session } = useSession();
  const location = useLocation();
  const isOfficer = session?.user.role === "OFFICER";
  const company = session?.user.company;
  const displayName = company?.display_name ?? session?.user.display_name ?? "";

  return (
    <>
      <a className="skip-link" href="#main">
        К содержимому
      </a>
      <DemoBanner />
      <header className="topbar">
        <div className="topbar-inner">
          <NavLink to={isOfficer ? "/bank/applications" : "/applications"} className="brand-link">
            <BrandMark caption={isOfficer ? "для сотрудника" : "для бизнеса"} />
          </NavLink>
          <nav aria-label="Основная навигация" className="topnav">
            {isOfficer ? (
              <NavLink to="/bank/applications">Очередь заявок</NavLink>
            ) : (
              <NavLink to="/applications" end>
                Мои заявки
              </NavLink>
            )}
          </nav>
          <div className="identity">
            {!isOfficer && location.pathname !== "/applications/new" ? (
              <ButtonLink to="/applications/new" variant="primary" className="topbar-cta">
                Новая заявка
              </ButtonLink>
            ) : null}
            <span className="avatar" aria-hidden="true">
              {initials(displayName) || "?"}
            </span>
            <span className="identity-text">
              <span className="identity-name">{displayName}</span>
              <span className="identity-meta small muted">
                {isOfficer ? "Сотрудник банка" : company ? company.demo_registration_id : "Клиент"}
              </span>
            </span>
            <NavLink to="/demo" className="btn btn-ghost identity-switch">
              Сменить профиль
            </NavLink>
          </div>
        </div>
      </header>
      <main className="page" id="main" tabIndex={-1}>
        <Outlet />
      </main>
    </>
  );
}
