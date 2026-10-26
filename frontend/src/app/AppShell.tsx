import { useQuery } from "@tanstack/react-query";
import { NavLink, Outlet } from "react-router";
import { api } from "../api/endpoints";
import { queryKeys } from "../api/queryClient";
import { useSession } from "../api/session";

export function DemoBanner() {
  const meta = useQuery({ queryKey: queryKeys.meta, queryFn: ({ signal }) => api.meta({ signal }), staleTime: Infinity });
  const { session } = useSession();
  const demo = meta.data?.demo_mode ?? session?.demo_mode ?? true;
  return (
    <div className="demo-banner" role="note">
      <strong>{demo ? "Демонстрационный режим." : "Тестовый стенд."}</strong>{" "}
      Только синтетические данные. Реальная выдача и юридическая подпись не выполняются
      {demo ? "; открытый выбор профиля не является аутентификацией." : "."}
    </div>
  );
}

function BrandMark() {
  return (
    <span className="brand">
      <span className="brand-mark" aria-hidden="true" />
      <span className="brand-name">Кредитный кабинет</span>
    </span>
  );
}

export function AppShell() {
  const { session } = useSession();
  const isOfficer = session?.user.role === "OFFICER";
  const company = session?.user.company;

  return (
    <>
      <a className="skip-link" href="#main">
        К содержимому
      </a>
      <DemoBanner />
      <header className="topbar">
        <div className="topbar-inner">
          <NavLink to={isOfficer ? "/bank/applications" : "/applications"} className="brand-link">
            <BrandMark />
          </NavLink>
          <nav aria-label="Основная навигация" className="topnav">
            {isOfficer ? (
              <NavLink to="/bank/applications" end={false}>
                Очередь заявок
              </NavLink>
            ) : (
              <NavLink to="/applications" end>
                Мои заявки
              </NavLink>
            )}
          </nav>
          <div className="identity">
            <span className="identity-text">
              <span className="identity-name">{company?.display_name ?? session?.user.display_name}</span>
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
